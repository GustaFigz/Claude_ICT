"""Timezone + session/Kill-Zone logic. DST handled by zoneinfo (stdlib, Python 3.11)."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .schemas import SessionState


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def to_tz(dt_utc: datetime, tz_name: str) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(ZoneInfo(tz_name))


def _within(local: datetime, start: time, end: time) -> bool:
    return start <= local.time() < end


def ftmo_day_start(now_utc: datetime, rollover_tz: str) -> datetime:
    """UTC instant of the most recent 00:00 in the FTMO rollover timezone (CE(S)T)."""
    local = to_tz(now_utc, rollover_tz)
    midnight_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight_local.astimezone(timezone.utc)


def evaluate_sessions(
    now_utc: datetime,
    sessions_cfg: dict,
    symbol_sessions: list[str],
    tz_name: str = "America/New_York",
) -> SessionState:
    """Determine active session, kill-zone / entry-window membership and the next window."""
    local = to_tz(now_utc, tz_name)
    state = SessionState(ny_time=local.strftime("%Y-%m-%d %H:%M %Z"))

    next_dt: datetime | None = None
    next_name: str | None = None

    for name in symbol_sessions:
        cfg = sessions_cfg.get(name)
        if not cfg:
            continue
        kz_s, kz_e = _parse_hhmm(cfg["kill_zone"]["start"]), _parse_hhmm(cfg["kill_zone"]["end"])
        ew_s, ew_e = _parse_hhmm(cfg["entry_window"]["start"]), _parse_hhmm(cfg["entry_window"]["end"])

        if _within(local, kz_s, kz_e):
            state.active_session = name
            state.in_kill_zone = True
            if _within(local, ew_s, ew_e):
                state.in_entry_window = True

        # next upcoming entry-window start today or tomorrow
        cand = local.replace(hour=ew_s.hour, minute=ew_s.minute, second=0, microsecond=0)
        if cand <= local:
            cand = cand + timedelta(days=1)
        if next_dt is None or cand < next_dt:
            next_dt, next_name = cand, name

    if next_name and not state.in_entry_window:
        state.next_window = f"{next_name} @ {next_dt.strftime('%Y-%m-%d %H:%M %Z')}"
    return state
