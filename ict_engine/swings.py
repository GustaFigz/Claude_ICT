"""Swing high/low detection. Deterministic, fractal-style (N candles each side)."""
from __future__ import annotations

from data_pipeline.schemas import Candle, SwingPoint

# N candles required on each side, by timeframe class.
_N_INTRADAY = 2   # M5, M15, H1
_N_HTF = 3        # H4, D1, W1, MN


def n_for_timeframe(tf: str) -> int:
    return _N_HTF if tf in {"H4", "D1", "W1", "MN"} else _N_INTRADAY


def detect_swings(candles: list[Candle], n: int) -> list[SwingPoint]:
    swings: list[SwingPoint] = []
    for i in range(n, len(candles) - n):
        c = candles[i]
        left = candles[i - n:i]
        right = candles[i + 1:i + 1 + n]
        if c.high > max(x.high for x in left) and c.high > max(x.high for x in right):
            swings.append(SwingPoint(index=i, time=c.time, price=c.high, kind="high"))
        if c.low < min(x.low for x in left) and c.low < min(x.low for x in right):
            swings.append(SwingPoint(index=i, time=c.time, price=c.low, kind="low"))
    return swings


def last_swing(swings: list[SwingPoint], kind: str) -> SwingPoint | None:
    for sp in reversed(swings):
        if sp.kind == kind:
            return sp
    return None
