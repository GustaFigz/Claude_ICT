from datetime import datetime, timedelta, timezone

from data_pipeline.quality import build_data_quality
from data_pipeline.schemas import Candle

PIP = 0.0001
NOW = datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc)


def _c(close, minutes_ago):
    return Candle(time=NOW - timedelta(minutes=minutes_ago), open=close, high=close,
                  low=close, close=close)


def test_fresh_and_agreeing():
    primary = [_c(1.1000, 1)]
    secondary = [_c(1.1002, 1)]
    dq = build_data_quality("mt5", primary, secondary, NOW)
    assert dq.fresh is True
    assert dq.source_agreement is True
    assert not dq.issues


def test_stale_data_flagged():
    dq = build_data_quality("mt5", [_c(1.1000, 30)], None, NOW, max_age_seconds=300)
    assert dq.fresh is False
    assert any("stale" in i for i in dq.issues)


def test_divergence_flagged():
    primary = [_c(1.1000, 1)]
    secondary = [_c(1.1200, 1)]  # ~1.8% apart
    dq = build_data_quality("mt5", primary, secondary, NOW, divergence_tol_pct=0.5)
    assert dq.source_agreement is False
    assert dq.max_divergence_pct > 0.5
