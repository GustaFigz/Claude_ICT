from _util import c

from data_pipeline.schemas import SwingPoint
from ict_engine.liquidity import detect_fvg, detect_order_blocks, detect_pools, premium_discount

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
    kinds = {p.kind for p in pools}
    assert "SSL" in kinds and "BSL" in kinds


def test_premium_discount():
    candles = [c(0, 11, 20, 10, 12), c(1, 12, 18, 11, 15)]
    eq, prem, disc = premium_discount(candles)
    assert eq == 15
    assert prem == (15, 20) and disc == (10, 15)
