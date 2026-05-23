"""CLI entrypoint.

    python -m cli.main analyze EURUSD [--now 2026-05-26T14:30] [--trend up|down]

Current build runs in data_mode=fixtures (offline, deterministic). Live MT5/OANDA wiring
plugs into the same build_context() once credentials/terminal are available.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from data_pipeline import fixtures
from data_pipeline.audit import append_analysis
from data_pipeline.collector import build_context, collect_live
from data_pipeline.schemas import AccountSnapshot, DataQuality

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
NEEDED_TF = ["D1", "H4", "H1", "M5"]
_START = {"EURUSD": (1.0800, 0.0010), "GBPUSD": (1.2700, 0.0012), "NAS100": (18000.0, 25.0)}


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_configs() -> tuple[dict, dict, dict]:
    acc_path = CONFIG / "account.yaml"
    if not acc_path.exists():
        acc_path = CONFIG / "account.example.yaml"
    account = _load_yaml(acc_path)["account"]
    symbols = _load_yaml(CONFIG / "symbols.yaml")["symbols"]
    sessions = _load_yaml(CONFIG / "sessions.yaml")["sessions"]
    return account, symbols, sessions


def _fixture_candles(symbol: str, now_utc: datetime, trend: str) -> dict:
    start, step = _START.get(symbol, (1.0, 0.001))
    counts = {"D1": 60, "H4": 60, "H1": 80, "M5": 80}
    return {tf: fixtures.generate_candles(tf, counts[tf], start, step, now_utc, trend) for tf in NEEDED_TF}


def _run_live(symbol, symbol_cfg, account, sessions, data_mode, now_utc):
    """Live data path. Requires MT5 terminal + OANDA key. Account state always from MT5 (FTMO)."""
    from data_pipeline import mt5_client, news_client, oanda_client

    if data_mode == "mt5":
        get_candles = lambda tf, count: mt5_client.get_candles(symbol_cfg["broker_symbol"], tf, count)
        get_secondary = lambda tf, count: oanda_client.get_candles(symbol_cfg["oanda_symbol"], tf, count)
    elif data_mode == "oanda":
        get_candles = lambda tf, count: oanda_client.get_candles(symbol_cfg["oanda_symbol"], tf, count)
        get_secondary = None
    else:
        raise ValueError(f"unknown data_mode {data_mode}")

    try:
        events = news_client.events_from_raw(news_client.parse_calendar(news_client.fetch_calendar()))
    except Exception as e:  # network/feed failure: proceed without news (validator stays conservative)
        print(f"  [warn] calendar fetch failed: {e}")
        events = None

    return collect_live(symbol, symbol_cfg, account, sessions, get_candles,
                        mt5_client.get_account_snapshot, source=data_mode, now_utc=now_utc,
                        get_secondary_candles=get_secondary, news_events=events)


def cmd_analyze(args) -> int:
    account, symbols, sessions = _load_configs()
    symbol = args.symbol.upper()
    if symbol not in symbols or not symbols[symbol].get("enabled", False):
        print(f"Symbol {symbol} not enabled in config/symbols.yaml")
        return 2
    symbol_cfg = symbols[symbol]

    now_utc = (datetime.fromisoformat(args.now).replace(tzinfo=timezone.utc)
               if args.now else datetime.now(timezone.utc))

    data_mode = account.get("data_mode", "fixtures")
    if data_mode == "fixtures":
        tf_candles = _fixture_candles(symbol, now_utc, args.trend)
        snapshot = AccountSnapshot(
            balance=float(account["initial_capital"]),
            equity=float(account["initial_capital"]),
            daily_pnl_pct=0.0, drawdown_pct=0.0,
        )
        dq = DataQuality(source="fixtures", fresh=True, age_seconds=0.0)
        ctx = build_context(symbol, symbol_cfg, account, sessions, tf_candles, snapshot, dq, now_utc=now_utc)
    else:
        ctx = _run_live(symbol, symbol_cfg, account, sessions, data_mode, now_utc)

    out_dir = ROOT / "context"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{ctx.run_id}.json"
    out_path.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")
    append_analysis(ctx, ROOT / "logs")

    v = ctx.validator_result
    print(f"[{ctx.symbol}] {now_utc.isoformat()}  source={dq.source}")
    print(f"  bias D1/H4/H1 : {ctx.structure.bias_d1_h4_h1}")
    print(f"  session       : {ctx.session_state.active_session} "
          f"(entry_window={ctx.session_state.in_entry_window})")
    print(f"  setups        : {len(ctx.setup_candidates)}"
          + (f" score={ctx.setup_candidates[0].confluence_score}" if ctx.setup_candidates else ""))
    print(f"  status        : {v.status.value}  decision={v.decision.value}")
    if v.failures:
        print(f"  failures      : {v.failures}")
    print(f"  context JSON  : {out_path.relative_to(ROOT)}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ict")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="run an analysis for a symbol")
    a.add_argument("symbol")
    a.add_argument("--now", help="ISO time (UTC) to evaluate sessions at, e.g. 2026-05-26T14:30")
    a.add_argument("--trend", default="up", choices=["up", "down"], help="fixtures trend")
    a.set_defaults(func=cmd_analyze)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
