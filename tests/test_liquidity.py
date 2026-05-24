from _util import c

from data_pipeline.schemas import LiquidityPool, SwingPoint
from ict_engine.liquidity import (
    atr_pips,
    compute_draw_direction,
    detect_fvg,
    detect_order_blocks,
    detect_pools,
    premium_discount,
)

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
