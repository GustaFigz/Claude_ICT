"""Audit logger: one structured line per analysis, so any decision is reconstructible."""
from __future__ import annotations

import json
from pathlib import Path

from .schemas import AnalysisContext


def append_analysis(ctx: AnalysisContext, logs_dir: Path) -> Path:
    logs_dir.mkdir(exist_ok=True)
    path = logs_dir / "analyses.jsonl"
    best = max(ctx.setup_candidates, key=lambda s: s.confluence_score, default=None)
    record = {
        "run_id": ctx.run_id,
        "time_utc": ctx.created_at_utc.isoformat(),
        "symbol": ctx.symbol,
        "source": ctx.data_quality.source,
        "bias": ctx.structure.bias_d1_h4_h1,
        "session": ctx.session_state.active_session,
        "status": ctx.validator_result.status.value,
        "decision": ctx.validator_result.decision.value,
        "confluence": best.confluence_score if best else 0,
        "reward_risk": ctx.risk_calculation.reward_risk if ctx.risk_calculation else None,
        "failures": ctx.validator_result.failures,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return path
