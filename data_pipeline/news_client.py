"""ForexFactory economic calendar (public XML mirror). Used for high-impact blackout.

Feed: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
Note: the feed's <date>/<time> are in the site timezone; normalize before computing
minutes_until. Single-source fragility is a known risk (see ANALISE_CRITICA §3.5) — add a
second source / manual pre-session check before trading live.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from .schemas import NewsEvent, NewsState

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
# The FF XML mirror publishes times in US Eastern by default. Override if your feed differs.
FF_SOURCE_TZ = "America/New_York"


def fetch_calendar(url: str = FF_URL, timeout: int = 10, retries: int = 3, backoff: float = 1.0) -> str:
    """Fetch the FF calendar XML with retry + exponential backoff.

    Transient network blips shouldn't blind the news gate. Tries `retries` times with
    delays backoff, 2*backoff, ... and re-raises the last error if all attempts fail
    (the caller turns that into a fail-safe blackout).
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (ICT-System)"}, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
    raise last_exc  # type: ignore[misc]


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


# --- Trading Economics fallback source -------------------------------------------------

TE_URL = "https://api.tradingeconomics.com/calendar"
# Country (as TE reports it) -> ISO currency. Covers the majors the system trades.
_TE_COUNTRY_CCY = {
    "united states": "USD", "euro area": "EUR", "germany": "EUR", "france": "EUR",
    "italy": "EUR", "spain": "EUR", "united kingdom": "GBP", "japan": "JPY",
    "canada": "CAD", "australia": "AUD", "new zealand": "NZD", "switzerland": "CHF",
}
_TE_IMPACT = {1: "Low", 2: "Medium", 3: "High"}


def fetch_calendar_te(api_key: str, timeout: int = 10) -> list[NewsEvent]:
    """Trading Economics calendar -> NewsEvent list (fallback for ForexFactory).

    Free tier accepts `c=guest:guest` for limited testing. Times are returned in UTC.
    Raises on network/HTTP error so the caller can fall through to the next source.
    """
    resp = requests.get(TE_URL, params={"c": api_key, "f": "json"}, timeout=timeout)
    resp.raise_for_status()
    out: list[NewsEvent] = []
    for item in resp.json():
        raw_date = (item.get("Date") or "").replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(raw_date)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        currency = (item.get("Currency") or "").strip().upper()
        if not currency:
            currency = _TE_COUNTRY_CCY.get((item.get("Country") or "").strip().lower(), "")
        impact = _TE_IMPACT.get(item.get("Importance"), "Low")
        title = (item.get("Event") or item.get("Category") or "").strip()
        out.append(NewsEvent(time_utc=dt.astimezone(timezone.utc), currency=currency,
                             impact=impact, title=title))
    return out


def fetch_with_fallback(te_api_key: str | None = None) -> list[NewsEvent] | None:
    """Try ForexFactory, then Trading Economics. Return None if BOTH fail.

    None signals the caller (build_news_state) to fail safe into a blackout.
    """
    try:
        return events_from_raw(parse_calendar(fetch_calendar()))
    except Exception as e:  # noqa: BLE001 — any FF failure should fall through
        print(f"  [warn] ForexFactory failed: {e}")
    if te_api_key:
        try:
            events = fetch_calendar_te(te_api_key)
            print("  [info] using Trading Economics fallback calendar")
            return events
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] Trading Economics fallback failed: {e}")
    return None


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
