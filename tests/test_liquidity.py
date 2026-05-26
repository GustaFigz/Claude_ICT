from datetime import datetime, timezone

from _util import c

from data_pipeline.schemas import FVG, LiquidityPool, SwingPoint
from ict_engine.liquidity import (
    _mark_filled,
    atr_pips,
    compute_draw_direction,
    detect_breakers,
    detect_fvg,
    detect_order_blocks,
    detect_pools,
    premium_discount,
)

_FVG_TIME = datetime(2026, 5, 26, 0, 0, tzinfo=timezone.utc)

PIP = 1.0


def test_bullish_fvg():
    candles = [c(0, 9, 10, 8, 9), c(1, 10, 11, 9, 10.5), c(2, 12.5, 13, 12, 12.5)]
    fvgs = detect_fvg(candles, PIP)
    assert len(fvgs) == 1
    f = fvgs[0]
    assert f.kind == "bullish" and f.bottom == 10 and f.top == 12 and f.size_pips == 2 and not f.filled


def test_bullish_order_block():
    candles = [c(0, 12, 12, 9, 10), c(1, 10, 10.5, 9.5, 10), c(2, 12, 15, 11, 14)]
    obs = detect_order_blocks(candles, PIP)
    assert any(o.kind == "bullish" and o.top == 12 and o.bottom == 9 for o in obs)


def test_pools_equal_highs_and_lows():
    def t(i):
        from datetime import datetime, timezone
        return datetime(2026, 5, 26, i, tzinfo=timezone.utc)
    swings = [
        SwingPoint(index=0, time=t(0), price=100.0, kind="high"),
        SwingPoint(index=1, time=t(1), price=101.0, kind="high"),
        SwingPoint(index=2, time=t(2), price=90.0, kind="low"),
        SwingPoint(index=3, time=t(3), price=90.0, kind="low"),
    ]
    pools = detect_pools(swings, PIP, tol_pips=2.0)
    by_kind = {p.kind: p for p in pools}
    assert "BSL" in by_kind and "SSL" in by_kind
    # Equal highs -> BSL (above market); equal lows -> SSL (below market)
    assert by_kind["BSL"].price > by_kind["SSL"].price
    assert by_kind["BSL"].price == 100.5  # mean of 100, 101
    assert by_kind["SSL"].price == 90.0   # mean of 90, 90


def test_detect_breakers_inverts_mitigated_ob():
    # candle 0 = bullish OB (bottom 9, top 12); candle 3 closes at 8 (< 9) -> OB mitigated
    candles = [c(0, 12, 12, 9, 10), c(1, 10, 10.5, 9.5, 10), c(2, 12, 15, 11, 14), c(3, 9, 9, 7, 8)]
    breakers = detect_breakers(candles, PIP)
    assert len(breakers) == 1
    b = breakers[0]
    assert b.kind == "bearish" and b.mitigated is True and b.top == 12 and b.bottom == 9


def test_no_breakers_when_ob_not_mitigated():
    # same bullish OB but price never closes below its bottom -> no breaker
    candles = [c(0, 12, 12, 9, 10), c(1, 10, 10.5, 9.5, 10), c(2, 12, 15, 11, 14), c(3, 14, 16, 13, 15)]
    assert detect_breakers(candles, PIP) == []


def test_premium_discount():
    candles = [c(0, 11, 20, 10, 12), c(1, 12, 18, 11, 15)]
    eq, prem, disc = premium_discount(candles)
    assert eq == 15
    assert prem == (15, 20) and disc == (10, 15)


def test_draw_direction_nearest_bsl_is_up():
    pools = [LiquidityPool(kind="BSL", price=101.0, touches=2),
             LiquidityPool(kind="SSL", price=90.0, touches=2)]
    assert compute_draw_direction(pools, price=100.0) == "UP"


def test_draw_direction_nearest_ssl_is_down():
    pools = [LiquidityPool(kind="BSL", price=120.0, touches=2),
             LiquidityPool(kind="SSL", price=99.0, touches=2)]
    assert compute_draw_direction(pools, price=100.0) == "DOWN"


def test_draw_direction_falls_back_to_bias_when_no_pools():
    assert compute_draw_direction([], price=100.0, bias="DOWN") == "DOWN"
    assert compute_draw_direction([], price=100.0, bias="SIDEWAYS") is None


def test_atr_pips_constant_range():
    candles = [c(i, 100, 105, 95, 100) for i in range(16)]  # TR = 10 each
    assert atr_pips(candles, PIP, period=14) == 10.0


def test_atr_pips_insufficient_candles():
    candles = [c(i, 100, 105, 95, 100) for i in range(5)]
    assert atr_pips(candles, PIP, period=14) == 0.0


def test_fvg_min_pips_filters_small_gaps():
    candles = [c(0, 9, 10, 8, 9), c(1, 10, 11, 9, 10.5), c(2, 12.5, 13, 12, 12.5)]
    assert len(detect_fvg(candles, PIP, min_pips=0.0)) == 1  # 2-pip gap kept
    assert detect_fvg(candles, PIP, min_pips=5.0) == []      # 2-pip gap filtered


def test_fvg_not_filled_by_wick():
    # wick below bullish FVG bottom but close is inside → not filled (ICT: filled = close through)
    fvg = FVG(kind="bullish", bottom=10.0, top=12.0, time=_FVG_TIME, size_pips=20)
    candles = [c(1, 11.0, 12.5, 9.0, 11.0)]  # low=9 < 10 (wick), close=11 (inside gap)
    _mark_filled([fvg], candles)
    assert fvg.filled is False


def test_fvg_filled_by_close_below():
    # close below bullish FVG bottom → filled
    fvg = FVG(kind="bullish", bottom=10.0, top=12.0, time=_FVG_TIME, size_pips=20)
    candles = [c(1, 11.0, 12.5, 8.0, 9.0)]  # close=9 < bottom=10
    _mark_filled([fvg], candles)
    assert fvg.filled is True


def test_bearish_fvg_not_filled_by_wick():
    # wick above bearish FVG top but close is inside → not filled
    fvg = FVG(kind="bearish", bottom=10.0, top=12.0, time=_FVG_TIME, size_pips=20)
    candles = [c(1, 11.0, 13.0, 9.5, 11.0)]  # high=13 > top=12 (wick), close=11 (inside)
    _mark_filled([fvg], candles)
    assert fvg.filled is False
