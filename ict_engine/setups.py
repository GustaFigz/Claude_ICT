"""Silver Bullet setup candidate generation. Deterministic; the validator gates it."""
from __future__ import annotations

from data_pipeline.schemas import (
    Candle,
    FVG,
    Liquidity,
    SessionState,
    SetupCandidate,
    Structure,
)


def build_silver_bullet(
    structure: Structure,
    liquidity: Liquidity,
    session_state: SessionState,
    entry_fvgs: list[FVG],
    entry_candles: list[Candle],
    symbol_cfg: dict,
) -> SetupCandidate | None:
    bias = structure.bias_d1_h4_h1
    if bias not in {"UP", "DOWN"} or not entry_candles:
        return None

    pip_size = float(symbol_cfg["pip_size"])
    price = entry_candles[-1].close
    direction = "LONG" if bias == "UP" else "SHORT"
    buffer = 2 * pip_size

    if direction == "LONG":
        gaps = [f for f in entry_fvgs if f.kind == "bullish" and not f.filled and f.top <= price]
        if not gaps:
            return None
        fvg = max(gaps, key=lambda f: f.top)  # nearest below price
        entry = fvg.top
        stop = min(fvg.bottom, structure.by_tf.get("H1").last_swing_low or fvg.bottom) - buffer \
            if structure.by_tf.get("H1") else fvg.bottom - buffer
        pools_above = [p.price for p in liquidity.pools if p.price > entry]
        target = min(pools_above) if pools_above else (liquidity.premium_zone[1] if liquidity.premium_zone else price + (entry - stop) * 2)
    else:
        gaps = [f for f in entry_fvgs if f.kind == "bearish" and not f.filled and f.bottom >= price]
        if not gaps:
            return None
        fvg = min(gaps, key=lambda f: f.bottom)  # nearest above price
        entry = fvg.bottom
        stop = max(fvg.top, structure.by_tf.get("H1").last_swing_high or fvg.top) + buffer \
            if structure.by_tf.get("H1") else fvg.top + buffer
        pools_below = [p.price for p in liquidity.pools if p.price < entry]
        target = max(pools_below) if pools_below else (liquidity.discount_zone[0] if liquidity.discount_zone else price - (stop - entry) * 2)

    factors: list[str] = [f"HTF bias {bias}", f"Active {fvg.kind} FVG ({fvg.size_pips} pips)"]
    if session_state.in_entry_window:
        factors.append(f"Silver Bullet window ({session_state.active_session})")
    if liquidity.draw_direction:
        factors.append(f"Draw on liquidity {liquidity.draw_direction}")

    return SetupCandidate(
        model="silver_bullet",
        direction=direction,
        entry_level=round(entry, 5),
        stop=round(stop, 5),
        targets=[round(target, 5)],
        confluence_factors=factors,
        confluence_score=len(factors),
    )
