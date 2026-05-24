from datetime import datetime, timezone

import data_pipeline.news_client as nc
from data_pipeline.news_client import (
    build_news_state, events_from_raw, fetch_with_fallback, parse_calendar, parse_ff_datetime,
)
from data_pipeline.schemas import NewsEvent

SAMPLE_XML = """<weeklyevents>
  <event><title>Non-Farm Payrolls</title><country>USD</country>
    <date>05-26-2026</date><time>8:30am</time><impact>High</impact></event>
  <event><title>Some EUR talk</title><country>EUR</country>
    <date>05-26-2026</date><time>All Day</time><impact>Low</impact></event>
</weeklyevents>"""


def test_parse_calendar_and_datetime():
    raw = parse_calendar(SAMPLE_XML)
    assert len(raw) == 2
    # 8:30am New York (EDT, UTC-4) -> 12:30 UTC
    dt = parse_ff_datetime("05-26-2026", "8:30am")
    assert dt == datetime(2026, 5, 26, 12, 30, tzinfo=timezone.utc)
    assert parse_ff_datetime("05-26-2026", "All Day") is None


def test_blackout_triggers_for_usd_high_impact():
    events = events_from_raw(parse_calendar(SAMPLE_XML))
    assert len(events) == 1  # All Day dropped
    now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)  # 30 min before NFP
    state = build_news_state(events, now, currencies=["EUR", "USD"], blackout_minutes=90)
    assert state.blackout is True
    assert "USD" in (state.blackout_reason or "")


def test_no_blackout_when_currency_irrelevant():
    events = events_from_raw(parse_calendar(SAMPLE_XML))
    now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    state = build_news_state(events, now, currencies=["GBP", "JPY"])
    assert state.blackout is False


def test_blackout_fail_safe_when_feed_none():
    now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    state = build_news_state(None, now, currencies=["EUR", "USD"])
    assert state.blackout is True
    assert "unavailable" in (state.blackout_reason or "").lower()


def test_no_blackout_when_feed_empty():
    now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    state = build_news_state([], now, currencies=["EUR", "USD"])
    assert state.blackout is False
    assert state.blackout_reason is None


def test_blackout_post_event_window():
    events = events_from_raw(parse_calendar(SAMPLE_XML))  # NFP at 12:30 UTC
    now = datetime(2026, 5, 26, 12, 45, tzinfo=timezone.utc)  # 15 min after NFP
    state = build_news_state(events, now, currencies=["USD"], post_event_minutes=30)
    assert state.blackout is True
    assert "post-event" in (state.blackout_reason or "").lower()


def test_no_blackout_after_post_event_window_clears():
    events = events_from_raw(parse_calendar(SAMPLE_XML))  # NFP at 12:30 UTC
    now = datetime(2026, 5, 26, 13, 15, tzinfo=timezone.utc)  # 45 min after NFP
    state = build_news_state(events, now, currencies=["USD"], post_event_minutes=30)
    assert state.blackout is False


# --- fallback orchestration (FF -> TE -> None) ---

_TE_EVENT = NewsEvent(time_utc=datetime(2026, 5, 28, 16, 30, tzinfo=timezone.utc),
                      currency="USD", impact="High", title="Core PCE")


def test_fallback_prefers_forexfactory(monkeypatch):
    monkeypatch.setattr(nc, "fetch_calendar", lambda *a, **k: SAMPLE_XML)
    result = fetch_with_fallback(te_api_key="guest:guest")
    assert any(e.title == "Non-Farm Payrolls" for e in result)


def test_fallback_uses_te_when_ff_fails(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("FF down")
    monkeypatch.setattr(nc, "fetch_calendar", boom)
    monkeypatch.setattr(nc, "fetch_calendar_te", lambda *a, **k: [_TE_EVENT])
    result = fetch_with_fallback(te_api_key="guest:guest")
    assert result == [_TE_EVENT]


def test_fallback_returns_none_when_both_fail(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(nc, "fetch_calendar", boom)
    monkeypatch.setattr(nc, "fetch_calendar_te", boom)
    assert fetch_with_fallback(te_api_key="guest:guest") is None
