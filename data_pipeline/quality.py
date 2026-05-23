"""Data-quality gates for live mode: freshness + cross-source agreement (MT5 vs OANDA).

Compares only the last CLOSED candle. Divergence in % of price; tolerance per call.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .schemas import Candle, DataQuality


def build_data_quality(
    source: str,
    primary: list[Candle],
    secondary: list[Candle] | None,
    now_utc: datetime,
    max_age_seconds: float = 300.0,
    divergence_tol_pct: float = 0.5,
) -> DataQuality:
    issues: list[str] = []

    if not primary:
        return DataQuality(source=source, fresh=False, issues=["no primary candles"])

    last = primary[-1]
    last_t = last.time if last.time.tzinfo else last.time.replace(tzinfo=timezone.utc)
    age = (now_utc - last_t).total_seconds()
    fresh = age <= max_age_seconds
    if not fresh:
        issues.append(f"stale data ({age:.0f}s > {max_age_seconds:.0f}s)")

    agreement = None
    max_div = None
    if secondary:
        ref = secondary[-1].close
        if ref:
            max_div = abs(last.close - ref) / ref * 100.0
            agreement = max_div <= divergence_tol_pct
            if not agreement:
                issues.append(f"source divergence {max_div:.3f}% > {divergence_tol_pct}%")

    return DataQuality(
        source=source,
        fresh=fresh,
        age_seconds=round(age, 1),
        source_agreement=agreement,
        max_divergence_pct=round(max_div, 4) if max_div is not None else None,
        issues=issues,
    )
