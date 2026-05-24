from datetime import datetime, timedelta, timezone

from data_pipeline import fixtures
from data_pipeline.collector import collect_live
from data_pipeline.schemas import AccountSnapshot, NewsEvent, Status

NOW = datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc)  # 10:30 NY -> entry window

SYMBOL_CFG = {
    "broker_symbol": "EURUSD", "pip_size": 0.0001, "pip_value_per_lot": 10.0,
    "min_lot": 0.01, "lot_step": 0.01, "max_lot": 50.0, "min_stop_pips": 8,
    "news_currencies": ["EUR", "USD"], "sessions": ["ny_am_silver_bullet"],
}
ACCOUNT_CFG = {
    "initial_capital": 10000, "daily_buffer_pct": 3.5, "max_total_buffer_pct": 8.0,
    "risk_per_trade_pct": 0.5, "min_rr_ratio": 2.0, "max_consecutive_losses": 2,
    "max_trades_per_day": 3, "timezone": "America/New_York",
}
SESSIONS_CFG = {
    "ny_am_silver_bullet": {
        "kill_zone": {"start": "08:30", "end": "11:00"},
        "entry_window": {"start": "10:00", "end": "11:00"},
    }
}


def _candles_fn(end_time, start=1.08, step=0.001, trend="up"):
    return lambda tf, count: fixtures.generate_candles(tf, count, start, step, end_time, trend)


def _snapshot():
    return AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0)


def test_live_fresh_runs():
    end = NOW + timedelta(minutes=5)  # M5 last candle lands on NOW
    ctx = collect_live("EURUSD", SYMBOL_CFG, ACCOUNT_CFG, SESSIONS_CFG,
                       _candles_fn(end), _snapshot, source="mt5", now_utc=NOW,
                       news_events=[])  # feed returned no relevant events -> safe
    assert ctx.data_quality.source == "mt5"
    assert ctx.data_quality.fresh is True
    assert ctx.structure.bias_d1_h4_h1 == "UP"
    assert ctx.news_state.blackout is False


def test_live_news_feed_failure_fails_safe():
    end = NOW + timedelta(minutes=5)
    ctx = collect_live("EURUSD", SYMBOL_CFG, ACCOUNT_CFG, SESSIONS_CFG,
                       _candles_fn(end), _snapshot, source="mt5", now_utc=NOW,
                       news_events=None)  # feed unavailable
    assert ctx.news_state.blackout is True
    assert ctx.validator_result.status == Status.BLOCKED


def test_live_stale_blocks():
    end = NOW - timedelta(minutes=25)  # M5 last candle ~30 min old
    ctx = collect_live("EURUSD", SYMBOL_CFG, ACCOUNT_CFG, SESSIONS_CFG,
                       _candles_fn(end), _snapshot, source="mt5", now_utc=NOW)
    assert ctx.data_quality.fresh is False
    assert ctx.validator_result.status == Status.BLOCKED


def test_live_divergence_blocks():
    end = NOW + timedelta(minutes=5)
    ctx = collect_live("EURUSD", SYMBOL_CFG, ACCOUNT_CFG, SESSIONS_CFG,
                       _candles_fn(end), _snapshot, source="mt5", now_utc=NOW,
                       get_secondary_candles=_candles_fn(end, start=1.10))  # ~1.8% apart
    assert ctx.data_quality.source_agreement is False
    assert ctx.validator_result.status == Status.BLOCKED


def test_live_news_blackout_blocks():
    end = NOW + timedelta(minutes=5)
    events = [NewsEvent(time_utc=NOW + timedelta(minutes=30), currency="USD",
                        impact="High", title="Non-Farm Payrolls")]
    ctx = collect_live("EURUSD", SYMBOL_CFG, ACCOUNT_CFG, SESSIONS_CFG,
                       _candles_fn(end), _snapshot, source="mt5", now_utc=NOW,
                       news_events=events)
    assert ctx.news_state.blackout is True
    assert ctx.validator_result.status == Status.BLOCKED
