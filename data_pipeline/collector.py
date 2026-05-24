"""Orchestrator: turns timeframe candles + account snapshot into a validated AnalysisContext.

This module contains NO trading opinion — it wires the deterministic engine together and
delegates GO/BLOCKED to the validator.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable

from ict_engine import liquidity as liq
from ict_engine import risk as risk_mod
from ict_engine import setups as setup_mod
from ict_engine import structure as struct
from ict_engine.swings import detect_swings

from . import market_clock
from .news_client import build_news_state
from .quality import build_data_quality
from .schemas import (
    AccountSnapshot,
    AnalysisContext,
    Candle,
    DataQuality,
    Liquidity,
    NewsEvent,
    NewsState,
    Structure,
)

# Timeframes the engine consumes. Counts are per timeframe.
ENGINE_TF = {"D1": 60, "H4": 60, "H1": 80, "M5": 80}


def collect_live(
    symbol: str,
    symbol_cfg: dict,
    account_cfg: dict,
    sessions_cfg: dict,
    get_candles: Callable[[str, int], list[Candle]],
    get_snapshot: Callable[[], AccountSnapshot],
    source: str,
    now_utc: datetime | None = None,
    get_secondary_candles: Callable[[str, int], list[Candle]] | None = None,
    news_events: list[NewsEvent] | None = None,
) -> AnalysisContext:
    """Live orchestration via dependency injection.

    Fetchers are injected so this is testable without MT5/OANDA. They MUST return only CLOSED
    candles (no forming candle). Account state should come from the FTMO broker (MT5).
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    tf_candles = {tf: get_candles(tf, count) for tf, count in ENGINE_TF.items()}

    secondary_m5 = get_secondary_candles("M5", ENGINE_TF["M5"]) if get_secondary_candles else None
    data_quality = build_data_quality(
        source, tf_candles.get("M5", []), secondary_m5, now_utc,
        max_age_seconds=300.0, divergence_tol_pct=0.5,
    )

    # Always evaluate news in live mode: None (feed failed) fails safe to blackout.
    news_state = build_news_state(
        news_events, now_utc, symbol_cfg.get("news_currencies", []),
        blackout_minutes=symbol_cfg.get("news_blackout_minutes", 90),
    )

    snapshot = get_snapshot()
    return build_context(symbol, symbol_cfg, account_cfg, sessions_cfg, tf_candles,
                         snapshot, data_quality, now_utc=now_utc, news_state=news_state)


def build_context(
    symbol: str,
    symbol_cfg: dict,
    account_cfg: dict,
    sessions_cfg: dict,
    tf_candles: dict[str, list],
    snapshot: AccountSnapshot,
    data_quality: DataQuality,
    now_utc: datetime | None = None,
    news_state: NewsState | None = None,
) -> AnalysisContext:
    now_utc = now_utc or datetime.now(timezone.utc)
    news_state = news_state or NewsState()
    pip_size = float(symbol_cfg["pip_size"])

    # --- structure (HTF bias) ---
    structure = Structure()
    for tf in ("D1", "H4", "H1"):
        if tf_candles.get(tf):
            structure.by_tf[tf] = struct.analyze_timeframe(tf, tf_candles[tf])
    structure.bias_d1_h4_h1 = struct.combine_bias(
        structure.by_tf["D1"].bias if "D1" in structure.by_tf else "SIDEWAYS",
        structure.by_tf["H4"].bias if "H4" in structure.by_tf else "SIDEWAYS",
        structure.by_tf["H1"].bias if "H1" in structure.by_tf else "SIDEWAYS",
    )

    # --- liquidity ---
    liquidity = Liquidity()
    h1 = tf_candles.get("H1", [])
    if h1:
        swings = detect_swings(h1, 2)
        liquidity.pools = liq.detect_pools(swings, pip_size)
    d1 = tf_candles.get("D1", [])
    if d1:
        eq, prem, disc = liq.premium_discount(d1)
        liquidity.equilibrium, liquidity.premium_zone, liquidity.discount_zone = eq, prem, disc
    if h1:
        liquidity.draw_direction = liq.compute_draw_direction(
            liquidity.pools, h1[-1].close, bias=structure.bias_d1_h4_h1
        )
        liquidity.breakers = liq.detect_breakers(h1, pip_size)

    # --- FVGs on entry timeframe (M5) and H1 ---
    # Filter out noise: keep only gaps >= 20% of ATR (ICT displacement threshold).
    entry_candles = tf_candles.get("M5", []) or h1
    if entry_candles:
        min_fvg_pips = 0.20 * liq.atr_pips(entry_candles, pip_size)
        entry_fvgs = liq.detect_fvg(entry_candles, pip_size, min_pips=min_fvg_pips)
    else:
        entry_fvgs = []
    structure.fvg_active = [f for f in entry_fvgs if not f.filled][:10]

    # --- session ---
    session = market_clock.evaluate_sessions(
        now_utc, sessions_cfg, symbol_cfg.get("sessions", []),
        tz_name=account_cfg.get("timezone", "America/New_York"),
    )

    # --- setup + risk ---
    order_blocks = liq.detect_order_blocks(entry_candles, pip_size) if entry_candles else []
    setup = setup_mod.build_silver_bullet(structure, liquidity, session, entry_fvgs, entry_candles,
                                          symbol_cfg, order_blocks=order_blocks)
    setups = [setup] if setup else []
    risk_calc = risk_mod.evaluate_risk(setup, symbol_cfg, account_cfg, snapshot) if setup else None
    if setup and liquidity.draw_direction:
        # DOWN bias targets sell-side liquidity below (SSL); UP targets buy-side above (BSL).
        kind = "SSL" if structure.bias_d1_h4_h1 == "DOWN" else "BSL"
        if setup.targets:
            liquidity.target = f"{kind} @ {setup.targets[0]}"

    ftmo = risk_mod.build_ftmo_limits(snapshot, account_cfg)

    from ict_engine.validator import validate
    result = validate(
        data_quality, snapshot, ftmo, session, news_state, setups, risk_calc, account_cfg,
        min_confluence=3,
    )

    return AnalysisContext(
        run_id=uuid.uuid4().hex[:12],
        created_at_utc=now_utc,
        symbol=symbol,
        broker_symbol=symbol_cfg.get("broker_symbol", symbol),
        data_quality=data_quality,
        account_snapshot=snapshot,
        ftmo_limits=ftmo,
        session_state=session,
        news_state=news_state,
        structure=structure,
        liquidity=liquidity,
        setup_candidates=setups,
        risk_calculation=risk_calc,
        validator_result=result,
    )
