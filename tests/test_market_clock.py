from datetime import datetime, timezone

from data_pipeline.market_clock import evaluate_sessions, ftmo_day_start, to_tz

SESSIONS = {
    "ny_am_silver_bullet": {
        "kill_zone": {"start": "08:30", "end": "11:00"},
        "entry_window": {"start": "10:00", "end": "11:00"},
    }
}
SYM = ["ny_am_silver_bullet"]


def test_utc_to_ny_dst():
    # May -> EDT (UTC-4): 14:30Z == 10:30 NY
    assert to_tz(datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc), "America/New_York").hour == 10


def test_inside_entry_window():
    now = datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc)  # 10:30 NY
    st = evaluate_sessions(now, SESSIONS, SYM)
    assert st.active_session == "ny_am_silver_bullet"
    assert st.in_kill_zone and st.in_entry_window


def test_outside_window_sets_next():
    now = datetime(2026, 5, 26, 20, 0, tzinfo=timezone.utc)  # 16:00 NY
    st = evaluate_sessions(now, SESSIONS, SYM)
    assert not st.in_entry_window
    assert st.next_window and "ny_am_silver_bullet" in st.next_window


def test_ftmo_day_start_is_midnight_prague():
    now = datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc)
    start = ftmo_day_start(now, "Europe/Prague")
    local = to_tz(start, "Europe/Prague")
    assert local.hour == 0 and local.minute == 0
