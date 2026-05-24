from datetime import datetime, timezone

from _util import c

from data_pipeline.schemas import SwingPoint
from ict_engine.structure import _last_event, analyze_timeframe, combine_bias

_T = datetime(2026, 5, 26, tzinfo=timezone.utc)


def _sp(price: float, kind: str, idx: int = 0) -> SwingPoint:
    return SwingPoint(index=idx, time=_T, price=price, kind=kind)


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


# --- BOS vs CHOCH: prev_bias determines continuation (BOS) vs reversal (CHOCH) ---

def _down_swings():
    # prev structure (all but last) reads DOWN: lower highs + lower lows
    return [_sp(110, "high"), _sp(100, "low"),
            _sp(108, "high"), _sp(98, "low"),
            _sp(106, "high"), _sp(96, "low")]


def _up_swings():
    # prev structure (all but last) reads UP: higher highs + higher lows
    return [_sp(100, "low"), _sp(106, "high"),
            _sp(102, "low"), _sp(108, "high"),
            _sp(104, "low"), _sp(110, "high")]


def test_choch_up_on_reversal_from_down():
    swings = _down_swings()  # last high = 106, prev_bias DOWN
    assert _last_event([c(0, 105, 107, 104, 107)], swings) == "CHOCH_UP"


def test_bos_up_on_continuation_in_uptrend():
    swings = _up_swings()  # last high = 110, prev_bias UP
    assert _last_event([c(0, 109, 112, 108, 111)], swings) == "BOS_UP"


def test_choch_down_on_reversal_from_up():
    swings = _up_swings()  # last low = 104, prev_bias UP
    assert _last_event([c(0, 105, 106, 103, 103)], swings) == "CHOCH_DOWN"


def test_bos_down_on_continuation_in_downtrend():
    swings = _down_swings()  # last low = 96, prev_bias DOWN
    assert _last_event([c(0, 97, 98, 95, 95)], swings) == "BOS_DOWN"


def test_no_event_when_price_inside_range():
    swings = _down_swings()  # last high 106, last low 96
    assert _last_event([c(0, 100, 101, 99, 100)], swings) is None
