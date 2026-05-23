from datetime import datetime, timezone

from data_pipeline.news_client import (
    build_news_state, events_from_raw, parse_calendar, parse_ff_datetime,
)

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
