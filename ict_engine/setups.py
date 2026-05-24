"""Silver Bullet setup candidate generation. Deterministic; the validator gates it."""
from __future__ import annotations

from data_pipeline.schemas import (
    Candle,
    FVG,
    Liquidity,
    OrderBlock,
    SessionState,
    SetupCandidate,
    Structure,
)

# ICT Optimal Trade Entry: the 61.8%-79% retracement band of the displacement leg.
_OTE_SHALLOW = 0.618
_OTE_DEEP = 0.79


def _ote_zone(low: float, high: float, direction: str) -> tuple[float, float] | None:
    """OTE band (61.8-79% retracement) of the leg [low, high] for the given direction.

    LONG retraces down from the high into discount; SHORT retraces up from the low into premium.
    Returns (zone_low, zone_high) or None if the leg is degenerate.
    """
    rng = high - low
    if rng <= 0:
        return None
    if direction == "LONG":
        return (high - _OTE_DEEP * rng, high - _OTE_SHALLOW * rng)
    return (low + _OTE_SHALLOW * rng, low + _OTE_DEEP * rng)


def _sweep_confirmed(candle: Candle, pools: list, direction: str) -> bool:
    """True if `candle` swept a liquidity pool against the trade then rejected back inside.

    LONG: wick takes an SSL (equal lows below) — low < pool < close — a bullish grab.
    SHORT: wick takes a BSL (equal highs above) — high > pool > close — a bearish grab.
    """
    if direction == "LONG":
        return any(p.kind == "SSL" and candle.low < p.price < candle.close for p in pools)
    return any(p.kind == "BSL" and candle.high > p.price > candle.close for p in pools)


def build_silver_bullet(
    structure: Structure,
    liquidity: Liquidity,
    session_state: SessionState,
    entry_fvgs: list[FVG],
    entry_candles: list[Candle],
    symbol_cfg: dict,
    order_blocks: list[OrderBlock] | None = None,
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

    # Target must lie in the trade's direction; otherwise the candidate is incoherent
    # (e.g. a LONG whose only liquidity sits below entry). Reject rather than emit a bad R:R.
    if direction == "LONG" and target <= entry:
        return None
    if direction == "SHORT" and target >= entry:
        return None

    factors: list[str] = [f"HTF bias {bias}", f"Active {fvg.kind} FVG ({fvg.size_pips} pips)"]
    if session_state.in_entry_window:
        factors.append(f"Silver Bullet window ({session_state.active_session})")
    if liquidity.draw_direction:
        factors.append(f"Draw on liquidity {liquidity.draw_direction}")

    # Order Block confluence: an unmitigated OB of the matching kind containing the entry.
    ob_kind = "bullish" if direction == "LONG" else "bearish"
    for ob in (order_blocks or []):
        if ob.kind == ob_kind and not ob.mitigated and ob.bottom <= entry <= ob.top:
            factors.append(f"Entry at {ob_kind} Order Block")
            break

    # OTE: does entry fall in the 61.8-79% retracement of the H1 displacement leg?
    h1 = structure.by_tf.get("H1")
    ote_zone = None
    entry_in_ote = False
    if h1 and h1.last_swing_low is not None and h1.last_swing_high is not None:
        ote_zone = _ote_zone(h1.last_swing_low, h1.last_swing_high, direction)
        if ote_zone and ote_zone[0] <= entry <= ote_zone[1]:
            entry_in_ote = True
            factors.append("Entry in OTE (61.8-79%)")

    # Liquidity sweep: did the latest candle grab a pool against us then reject?
    sweep = _sweep_confirmed(entry_candles[-1], liquidity.pools, direction)
    if sweep:
        factors.append("Liquidity sweep confirmed")

    return SetupCandidate(
        model="silver_bullet",
        direction=direction,
        entry_level=round(entry, 5),
        stop=round(stop, 5),
        targets=[round(target, 5)],
        confluence_factors=factors,
        confluence_score=len(factors),
        ote_zone=(round(ote_zone[0], 5), round(ote_zone[1], 5)) if ote_zone else None,
        entry_in_ote=entry_in_ote,
        sweep_confirmed=sweep,
    )
