"""ForexFactory economic calendar (public XML mirror). Used for high-impact blackout.

Feed: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
Note: the feed's <date>/<time> are in the site timezone; normalize before computing
minutes_until. Single-source fragility is a known risk (see ANALISE_CRITICA §3.5) — add a
second source / manual pre-session check before trading live.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

from .schemas import NewsEvent, NewsState

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"


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


def build_news_state(
    events_utc: list[NewsEvent],
    now_utc: datetime,
    currencies: list[str],
    blackout_minutes: int = 90,
) -> NewsState:
    """events_utc must already have time_utc normalized to UTC by the caller."""
    relevant = []
    blackout = False
    reason = None
    for ev in events_utc:
        if ev.currency.upper() not in {c.upper() for c in currencies}:
            continue
        mins = int((ev.time_utc - now_utc).total_seconds() // 60)
        ev.minutes_until = mins
        relevant.append(ev)
        if ev.impact.lower() in {"high", "red"} and 0 <= mins <= blackout_minutes:
            blackout = True
            reason = f"{ev.currency} {ev.title} in {mins} min (high impact)"
    return NewsState(events_next_48h=relevant, blackout=blackout, blackout_reason=reason)
