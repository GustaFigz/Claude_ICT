"""Market structure: bias + BOS/CHOCH from swing sequence. Close-based breaks (not wicks)."""
from __future__ import annotations

from data_pipeline.schemas import Candle, StructureTF, SwingPoint
from .swings import detect_swings, n_for_timeframe


def _bias_from_swings(swings: list[SwingPoint]) -> str:
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "SIDEWAYS"
    hh = highs[-1].price > highs[-2].price
    hl = lows[-1].price > lows[-2].price
    lh = highs[-1].price < highs[-2].price
    ll = lows[-1].price < lows[-2].price
    if hh and hl:
        return "UP"
    if lh and ll:
        return "DOWN"
    return "SIDEWAYS"


def _last_event(candles: list[Candle], swings: list[SwingPoint]) -> str | None:
    if not candles or not swings:
        return None
    last_close = candles[-1].close
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    prev_bias = _bias_from_swings(swings[:-1]) if len(swings) > 2 else "SIDEWAYS"
    if highs and last_close > highs[-1].price:
        return "CHOCH_UP" if prev_bias == "DOWN" else "BOS_UP"
    if lows and last_close < lows[-1].price:
        return "CHOCH_DOWN" if prev_bias == "UP" else "BOS_DOWN"
    return None


def analyze_timeframe(tf: str, candles: list[Candle]) -> StructureTF:
    n = n_for_timeframe(tf)
    swings = detect_swings(candles, n)
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    return StructureTF(
        timeframe=tf,
        bias=_bias_from_swings(swings),
        last_event=_last_event(candles, swings),
        last_swing_high=highs[-1].price if highs else None,
        last_swing_low=lows[-1].price if lows else None,
    )


def combine_bias(d1: str, h4: str, h1: str) -> str:
    votes = [d1, h4, h1]
    if votes.count("UP") >= 2 and "DOWN" not in votes:
        return "UP"
    if votes.count("DOWN") >= 2 and "UP" not in votes:
        return "DOWN"
    if "UP" in votes and "DOWN" in votes:
        return "CONFLICT"
    return "SIDEWAYS"
