from datetime import datetime, timezone

from _util import c

from data_pipeline.schemas import FVG, Liquidity, LiquidityPool, SessionState, Structure, StructureTF
from ict_engine.setups import build_silver_bullet

EURUSD = {"pip_size": 0.0001}
_T = datetime(2026, 5, 26, 14, tzinfo=timezone.utc)


def _structure_up():
    s = Structure(bias_d1_h4_h1="UP")
    s.by_tf["H1"] = StructureTF(timeframe="H1", bias="UP", last_swing_low=1.0950)
    return s


def test_builds_long_candidate():
    structure = _structure_up()
    liquidity = Liquidity(pools=[LiquidityPool(kind="SSL", price=1.1050, touches=2)], draw_direction="UP")
    session = SessionState(active_session="ny_am_silver_bullet", in_entry_window=True)
    fvgs = [FVG(kind="bullish", bottom=1.0980, top=1.0990, time=_T, size_pips=10, filled=False)]
    entry_candles = [c(0, 1.0995, 1.1005, 1.0990, 1.1000)]
    setup = build_silver_bullet(structure, liquidity, session, fvgs, entry_candles, EURUSD)
    assert setup is not None
    assert setup.direction == "LONG"
    assert setup.entry_level == 1.0990
    assert setup.targets == [1.1050]
    assert setup.confluence_score >= 3


def test_no_candidate_when_sideways():
    structure = Structure(bias_d1_h4_h1="SIDEWAYS")
    setup = build_silver_bullet(structure, Liquidity(), SessionState(),
                                [], [c(0, 1.1, 1.1, 1.1, 1.1)], EURUSD)
    assert setup is None
