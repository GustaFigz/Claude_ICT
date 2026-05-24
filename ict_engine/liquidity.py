"""Liquidity structures: FVG, Order Blocks, BSL/SSL pools, premium/discount."""
from __future__ import annotations

from data_pipeline.schemas import Candle, FVG, LiquidityPool, OrderBlock, SwingPoint


def detect_fvg(candles: list[Candle], pip_size: float, min_pips: float = 0.0) -> list[FVG]:
    """3-candle imbalance between candle i and i+2."""
    out: list[FVG] = []
    for i in range(len(candles) - 2):
        a, c = candles[i], candles[i + 2]
        if a.high < c.low:  # bullish gap
            gap = (c.low - a.high) / pip_size
            if gap >= min_pips:
                out.append(FVG(kind="bullish", bottom=a.high, top=c.low, time=c.time, size_pips=round(gap, 2)))
        elif a.low > c.high:  # bearish gap
            gap = (a.low - c.high) / pip_size
            if gap >= min_pips:
                out.append(FVG(kind="bearish", bottom=c.high, top=a.low, time=c.time, size_pips=round(gap, 2)))
    _mark_filled(out, candles)
    return out


def _mark_filled(fvgs: list[FVG], candles: list[Candle]) -> None:
    for f in fvgs:
        for c in candles:
            if c.time <= f.time:
                continue
            if c.low <= f.bottom and c.high >= f.top:
                f.filled = True
                break
            if f.kind == "bullish" and c.low <= f.bottom:
                f.filled = True
                break
            if f.kind == "bearish" and c.high >= f.top:
                f.filled = True
                break


def detect_order_blocks(candles: list[Candle], pip_size: float, displacement_pips: float = 0.0) -> list[OrderBlock]:
    """Last opposite candle before a displacement move that breaks the candle's extreme."""
    out: list[OrderBlock] = []
    for i in range(1, len(candles) - 1):
        prev, nxt = candles[i - 1], candles[i + 1]
        move = (nxt.close - prev.close) / pip_size
        if prev.close < prev.open and move >= displacement_pips and nxt.close > prev.high:
            out.append(OrderBlock(kind="bullish", bottom=prev.low, top=prev.high, time=prev.time))
        elif prev.close > prev.open and -move >= displacement_pips and nxt.close < prev.low:
            out.append(OrderBlock(kind="bearish", bottom=prev.low, top=prev.high, time=prev.time))
    return out


def detect_pools(swings: list[SwingPoint], pip_size: float, tol_pips: float = 2.0) -> list[LiquidityPool]:
    """Equal highs (BSL above) / equal lows (SSL below) clustered within tolerance.

    BSL = Buy Side Liquidity: cluster of equal highs above the market (buy stops rest here).
    SSL = Sell Side Liquidity: cluster of equal lows below the market (sell stops rest here).
    """
    tol = tol_pips * pip_size
    pools: list[LiquidityPool] = []
    for kind, sp_kind, pool_kind in (("high", "high", "BSL"), ("low", "low", "SSL")):
        pts = sorted((s.price for s in swings if s.kind == sp_kind))
        i = 0
        while i < len(pts):
            cluster = [pts[i]]
            j = i + 1
            while j < len(pts) and pts[j] - cluster[-1] <= tol:
                cluster.append(pts[j])
                j += 1
            if len(cluster) >= 2:
                pools.append(LiquidityPool(kind=pool_kind, price=round(sum(cluster) / len(cluster), 5), touches=len(cluster)))
            i = j
    return pools


def premium_discount(candles: list[Candle]) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """Equilibrium (50%) of the dealing range; premium above, discount below."""
    hi = max(c.high for c in candles)
    lo = min(c.low for c in candles)
    eq = (hi + lo) / 2
    return eq, (eq, hi), (lo, eq)


def compute_draw_direction(
    pools: list[LiquidityPool], price: float, bias: str | None = None
) -> str | None:
    """Draw on Liquidity: where price is being pulled, from the nearest unswept pool.

    The market gravitates toward resting liquidity. The closest pool to current price
    defines the immediate draw:
      - nearest pool is BSL (equal highs above) -> draw UP (reaching for buy stops)
      - nearest pool is SSL (equal lows below) -> draw DOWN (reaching for sell stops)
    Ties or no pools fall back to the structural bias (UP/DOWN), else None.
    """
    above = [p for p in pools if p.kind == "BSL" and p.price > price]
    below = [p for p in pools if p.kind == "SSL" and p.price < price]
    nearest_up = min((p.price - price for p in above), default=None)
    nearest_down = min((price - p.price for p in below), default=None)

    if nearest_up is not None and (nearest_down is None or nearest_up < nearest_down):
        return "UP"
    if nearest_down is not None and (nearest_up is None or nearest_down < nearest_up):
        return "DOWN"
    if bias in {"UP", "DOWN"}:
        return bias
    return None
