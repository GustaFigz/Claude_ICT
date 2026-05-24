"""ForexFactory economic calendar (public XML mirror). Used for high-impact blackout.

Feed: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
Note: the feed's <date>/<time> are in the site timezone; normalize before computing
minutes_until. Single-source fragility is a known risk (see ANALISE_CRITICA §3.5) — add a
second source / manual pre-session check before trading live.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from .schemas import NewsEvent, NewsState

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
# The FF XML mirror publishes times in US Eastern by default. Override if your feed differs.
FF_SOURCE_TZ = "America/New_York"


def fetch_calendar(url: str = FF_URL, timeout: int = 10) -> str:
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (ICT-System)"}, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_calendar(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    events = []
    for ev in root.findall("event"):
        events.append({
            "title": (ev.findtext("title") or "").strip(),
            "country": (ev.findtext("country") or "").strip().upper(),
            "date": (ev.findtext("date") or "").strip(),
            "time": (ev.findtext("time") or "").strip(),
            "impact": (ev.findtext("impact") or "").strip(),
        })
    return events


def parse_ff_datetime(date_str: str, time_str: str, src_tz: str = FF_SOURCE_TZ) -> datetime | None:
    """FF date 'MM-DD-YYYY' + time '8:30am' -> UTC datetime. None for All Day/Tentative/empty."""
    t = time_str.strip().lower()
    if not t or t in {"all day", "tentative", "day 1", "day 2"}:
        return None
    try:
        local = datetime.strptime(f"{date_str} {t}", "%m-%d-%Y %I:%M%p")
    except ValueError:
        return None
    return local.replace(tzinfo=ZoneInfo(src_tz)).astimezone(timezone.utc)


def events_from_raw(raw: list[dict], src_tz: str = FF_SOURCE_TZ) -> list[NewsEvent]:
    out: list[NewsEvent] = []
    for r in raw:
        dt = parse_ff_datetime(r.get("date", ""), r.get("time", ""), src_tz)
        if dt is None:
            continue
        out.append(NewsEvent(time_utc=dt, currency=r.get("country", ""),
                             impact=r.get("impact", ""), title=r.get("title", "")))
    return out


def build_news_state(
    events_utc: list[NewsEvent] | None,
    now_utc: datetime,
    currencies: list[str],
    blackout_minutes: int = 90,
    post_event_minutes: int = 30,
) -> NewsState:
    """Build the news gate. events_utc must already be UTC-normalized by the caller.

    Fail-safe: events_utc is None means the calendar feed was unavailable. We block
    (blackout=True) rather than trade blind into a possible high-impact release.

    Blackout windows for relevant currencies:
      - pre-event:  high-impact event within `blackout_minutes` ahead
      - post-event: high-impact event that fired within the last `post_event_minutes`
    """
    if events_utc is None:
        return NewsState(
            events_next_48h=[],
            blackout=True,
            blackout_reason="Calendar feed unavailable — blocking as a safety measure.",
        )

    relevant = []
    blackout = False
    reason = None
    wanted = {c.upper() for c in currencies}
    for ev in events_utc:
        if ev.currency.upper() not in wanted:
            continue
        mins = int((ev.time_utc - now_utc).total_seconds() // 60)
        ev.minutes_until = mins
        relevant.append(ev)
        if ev.impact.lower() not in {"high", "red"}:
            continue
        if 0 <= mins <= blackout_minutes:
            blackout = True
            reason = f"{ev.currency} {ev.title} in {mins} min (high impact)"
        elif -post_event_minutes <= mins < 0:
            blackout = True
            reason = f"{ev.currency} {ev.title} {abs(mins)} min ago (post-event volatility)"
    return NewsState(events_next_48h=relevant, blackout=blackout, blackout_reason=reason)
