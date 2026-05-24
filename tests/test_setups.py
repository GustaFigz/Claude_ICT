from datetime import datetime, timezone

from _util import c

from data_pipeline.schemas import (
    FVG, Liquidity, LiquidityPool, OrderBlock, SessionState, Structure, StructureTF,
)
from ict_engine.setups import _ote_zone, build_silver_bullet

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


def test_ote_zone_long_and_short():
    # leg 1.0900 -> 1.1000, range 0.0100
    lo, hi = _ote_zone(1.0900, 1.1000, "LONG")
    assert round(lo, 5) == 1.0921 and round(hi, 5) == 1.09382
    lo, hi = _ote_zone(1.0900, 1.1000, "SHORT")
    assert round(lo, 5) == 1.09618 and round(hi, 5) == 1.0979
    assert _ote_zone(1.10, 1.10, "LONG") is None  # degenerate leg


def test_entry_in_ote_adds_confluence():
    structure = Structure(bias_d1_h4_h1="UP")
    structure.by_tf["H1"] = StructureTF(timeframe="H1", bias="UP",
                                        last_swing_low=1.0900, last_swing_high=1.1000)
    liquidity = Liquidity(pools=[LiquidityPool(kind="BSL", price=1.1050, touches=2)],
                          draw_direction="UP")
    session = SessionState(active_session="ny_am_silver_bullet", in_entry_window=True)
    # FVG top 1.0930 sits inside the LONG OTE band (1.0921-1.09382)
    fvgs = [FVG(kind="bullish", bottom=1.0920, top=1.0930, time=_T, size_pips=10, filled=False)]
    entry_candles = [c(0, 1.0945, 1.0955, 1.0940, 1.0950)]
    setup = build_silver_bullet(structure, liquidity, session, fvgs, entry_candles, EURUSD)
    assert setup is not None
    assert setup.entry_in_ote is True
    assert setup.ote_zone is not None
    assert any("OTE" in f for f in setup.confluence_factors)


def test_order_block_adds_confluence():
    structure = _structure_up()
    liquidity = Liquidity(pools=[LiquidityPool(kind="BSL", price=1.1050, touches=2)],
                          draw_direction="UP")
    session = SessionState(active_session="ny_am_silver_bullet", in_entry_window=True)
    fvgs = [FVG(kind="bullish", bottom=1.0980, top=1.0990, time=_T, size_pips=10, filled=False)]
    entry_candles = [c(0, 1.0995, 1.1005, 1.0990, 1.1000)]
    # bullish OB whose range contains the entry (1.0990)
    obs = [OrderBlock(kind="bullish", bottom=1.0985, top=1.0995, time=_T, mitigated=False)]
    setup = build_silver_bullet(structure, liquidity, session, fvgs, entry_candles, EURUSD,
                                order_blocks=obs)
    assert setup is not None
    assert any("Order Block" in f for f in setup.confluence_factors)


def test_mitigated_order_block_not_counted():
    structure = _structure_up()
    liquidity = Liquidity(pools=[LiquidityPool(kind="BSL", price=1.1050, touches=2)],
                          draw_direction="UP")
    session = SessionState(active_session="ny_am_silver_bullet", in_entry_window=True)
    fvgs = [FVG(kind="bullish", bottom=1.0980, top=1.0990, time=_T, size_pips=10, filled=False)]
    entry_candles = [c(0, 1.0995, 1.1005, 1.0990, 1.1000)]
    obs = [OrderBlock(kind="bullish", bottom=1.0985, top=1.0995, time=_T, mitigated=True)]
    setup = build_silver_bullet(structure, liquidity, session, fvgs, entry_candles, EURUSD,
                                order_blocks=obs)
    assert setup is not None
    assert not any("Order Block" in f for f in setup.confluence_factors)


def test_rejects_long_with_target_below_entry():
    # LONG bias but no pool above entry and the premium-zone top falls below entry:
    # target would land below entry -> candidate must be rejected (reproduces the
    # bad-R:R fixture bug), not emitted.
    structure = _structure_up()
    liquidity = Liquidity(
        pools=[LiquidityPool(kind="SSL", price=1.0950, touches=2)],
        draw_direction="UP",
        premium_zone=(1.0900, 1.0950),  # top 1.0950 < entry 1.0990
    )
    session = SessionState(active_session="ny_am_silver_bullet", in_entry_window=True)
    fvgs = [FVG(kind="bullish", bottom=1.0980, top=1.0990, time=_T, size_pips=10, filled=False)]
    entry_candles = [c(0, 1.0995, 1.1005, 1.0990, 1.1000)]
    setup = build_silver_bullet(structure, liquidity, session, fvgs, entry_candles, EURUSD)
    assert setup is None
