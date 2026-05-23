from _util import c

from ict_engine.structure import analyze_timeframe, combine_bias


def _uptrend():
    highs = [5, 6, 8, 6, 5, 7, 10, 7, 6, 9, 12, 9, 8]
    lows = [4, 5, 7, 5, 4, 6, 9, 6, 5, 8, 11, 8, 7]
    return [c(i, lows[i], highs[i], lows[i], highs[i]) for i in range(len(highs))]


def test_uptrend_bias_up():
    st = analyze_timeframe("H1", _uptrend())
    assert st.bias == "UP"
    assert st.last_swing_high == 12
    assert st.last_swing_low == 5


def test_combine_bias():
    assert combine_bias("UP", "UP", "SIDEWAYS") == "UP"
    assert combine_bias("DOWN", "DOWN", "DOWN") == "DOWN"
    assert combine_bias("UP", "DOWN", "UP") == "CONFLICT"
    assert combine_bias("SIDEWAYS", "SIDEWAYS", "UP") == "SIDEWAYS"
