"""OANDA v20 REST client (free practice account). Secondary source / sanity check only.

Wire later: set OANDA_API_KEY and OANDA_ENVIRONMENT (practice|live) in .env.
"""
from __future__ import annotations

import os
from datetime import datetime

import requests

from .schemas import Candle

_GRAN = {"MN": "M", "W1": "W", "D1": "D", "H4": "H4", "H1": "H1", "M15": "M15", "M5": "M5", "M1": "M1"}
_HOSTS = {"practice": "https://api-fxpractice.oanda.com", "live": "https://api-fxtrade.oanda.com"}


def get_candles(oanda_symbol: str, tf: str, count: int, price: str = "M") -> list[Candle]:
    api_key = os.environ.get("OANDA_API_KEY")
    if not api_key:
        raise RuntimeError("OANDA_API_KEY not set in environment (.env).")
    env = os.environ.get("OANDA_ENVIRONMENT", "practice")
    url = f"{_HOSTS[env]}/v3/instruments/{oanda_symbol}/candles"
    params = {"granularity": _GRAN[tf], "count": count, "price": price}
    resp = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, params=params, timeout=15)
    resp.raise_for_status()
    out = []
    for c in resp.json().get("candles", []):
        if not c.get("complete", False):
            continue  # never use the forming candle
        m = c["mid"]
        out.append(Candle(
            time=datetime.fromisoformat(c["time"].replace("Z", "+00:00")),
            open=float(m["o"]), high=float(m["h"]), low=float(m["l"]), close=float(m["c"]),
            volume=float(c.get("volume", 0)),
        ))
    return out
