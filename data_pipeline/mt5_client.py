"""MetaTrader5 client (Windows-only). Decisive source for FTMO price + account state.

Wire later: requires the MT5 terminal installed, running and logged in, plus
`pip install MetaTrader5`. Times are UTC. 'Max bars in chart' limits available history.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .schemas import AccountSnapshot, Candle

_TF_MAP = {
    "MN": "MONTHLY", "W1": "WEEKLY", "D1": "DAILY", "H4": "H4",
    "H1": "H1", "M15": "M15", "M5": "M5", "M1": "M1",
}


def _require_mt5():
    try:
        import MetaTrader5 as mt5  # noqa
    except ImportError as e:
        raise RuntimeError(
            "MetaTrader5 not installed. Run `pip install MetaTrader5` on Windows with the "
            "MT5 terminal open and logged in."
        ) from e
    if not mt5.initialize():
        raise RuntimeError(f"mt5.initialize() failed: {mt5.last_error()}")
    return mt5


def get_candles(symbol: str, tf: str, count: int) -> list[Candle]:
    mt5 = _require_mt5()
    tf_const = getattr(mt5, f"TIMEFRAME_{_TF_MAP[tf]}")
    rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, count)
    out = []
    for r in rates:
        out.append(Candle(
            time=datetime.fromtimestamp(int(r["time"]), tz=timezone.utc),
            open=float(r["open"]), high=float(r["high"]), low=float(r["low"]),
            close=float(r["close"]), volume=float(r["tick_volume"]),
        ))
    return out


def get_account_snapshot(day_start_balance: float | None = None) -> AccountSnapshot:
    mt5 = _require_mt5()
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"account_info() returned None: {mt5.last_error()}")
    balance, equity = float(info.balance), float(info.equity)
    base = day_start_balance or balance
    daily_pnl_pct = (equity - base) / base * 100 if base else 0.0
    return AccountSnapshot(
        balance=balance, equity=equity,
        daily_pnl_pct=round(daily_pnl_pct, 3),
        drawdown_pct=0.0,  # caller computes vs initial/peak
        open_positions=mt5.positions_total() or 0,
    )
