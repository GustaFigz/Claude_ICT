from _util import c

from ict_engine.swings import detect_swings, last_swing, n_for_timeframe


def test_n_for_timeframe():
    assert n_for_timeframe("D1") == 3
    assert n_for_timeframe("M5") == 2


def test_detects_single_swing_high():
    highs = [10, 11, 12, 15, 12, 11, 10]
    lows = [9, 10, 11, 14, 11, 10, 9]
    candles = [c(i, lows[i], highs[i], lows[i], (highs[i] + lows[i]) / 2) for i in range(7)]
    sw = detect_swings(candles, 2)
    assert len(sw) == 1
    assert sw[0].kind == "high"
    assert sw[0].index == 3
    assert sw[0].price == 15


def test_detects_single_swing_low():
    lows = [10, 9, 8, 5, 8, 9, 10]
    highs = [11, 10, 9, 6, 9, 10, 11]
    candles = [c(i, highs[i], highs[i], lows[i], (highs[i] + lows[i]) / 2) for i in range(7)]
    sw = detect_swings(candles, 2)
    assert len(sw) == 1
    assert sw[0].kind == "low"
    assert last_swing(sw, "low").price == 5
