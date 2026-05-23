"""Deterministic synthetic candles so the system runs end-to-end offline (data_mode=fixtures).

Explicit zig-zag with monotonic legs (length >= 4) so the fractal swing detector finds clean
swing highs/lows; up-legs are larger than down-legs (uptrend), giving higher highs / higher lows.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .schemas import Candle

_TF_MINUTES = {"MN": 43200, "W1": 10080, "D1": 1440, "H4": 240, "H1": 60, "M15": 15, "M5": 5, "M1": 1}
_LEG = 5  # candles per leg


def generate_candles(tf: str, n: int, start_price: float, step: float,
                     end_time: datetime, trend: str = "up") -> list[Candle]:
    minutes = _TF_MINUTES.get(tf, 60)
    up, down = (step, 0.5 * step) if trend == "up" else (0.5 * step, step)
    t0 = end_time - timedelta(minutes=minutes * n)
    candles: list[Candle] = []
    price = start_price
    direction = 1  # start with an up-leg
    for i in range(n):
        delta = (up if direction > 0 else -down)
        o = price
        c = price + delta
        hi = max(o, c) + step * 0.2
        lo = min(o, c) - step * 0.2
        is_turn = (i + 1) % _LEG == 0
        if is_turn and direction > 0:      # peak: make it a strict high
            hi += step * 0.6
        elif is_turn and direction < 0:    # trough: make it a strict low
            lo -= step * 0.6
        candles.append(Candle(
            time=(t0 + timedelta(minutes=minutes * i)).replace(tzinfo=timezone.utc),
            open=round(o, 5), high=round(hi, 5), low=round(lo, 5), close=round(c, 5), volume=100 + i,
        ))
        price = c
        if (i + 1) % _LEG == 0:
            direction *= -1
    return candles
