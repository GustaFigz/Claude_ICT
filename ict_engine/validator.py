"""Validator: applies the execution-policy decision tree to produce GO/BLOCKED + decision.

Precedence (rules/execution_policy.md §7):
  data invalid > account risk > news blackout > outside window > no/weak setup > risk fail > GO.
Hard stops -> BLOCKED + SEM_TRADE. Timing/weak-setup -> GO + AGUARDAR. Pass -> GO + COMPRAR/VENDER.
"""
from __future__ import annotations

from data_pipeline.schemas import (
    AccountSnapshot,
    DataQuality,
    Decision,
    FTMOLimits,
    NewsState,
    RiskCalculation,
    SessionState,
    SetupCandidate,
    Status,
    ValidatorResult,
)


def validate(
    data_quality: DataQuality,
    snapshot: AccountSnapshot,
    ftmo: FTMOLimits,
    session: SessionState,
    news: NewsState,
    setups: list[SetupCandidate],
    risk: RiskCalculation | None,
    account_cfg: dict,
    min_confluence: int = 3,
) -> ValidatorResult:
    failures: list[str] = []

    # 1. Data quality
    if not data_quality.fresh:
        failures.append("data not fresh")
    failures.extend(data_quality.issues)
    if data_quality.source_agreement is False:
        failures.append(f"source divergence {data_quality.max_divergence_pct}%")
    if failures:
        return ValidatorResult(status=Status.BLOCKED, decision=Decision.SEM_TRADE,
                               failures=failures, description="Data quality gate failed.")

    # 2. Account risk (FTMO)
    if ftmo.daily_margin_pct <= 0:
        failures.append("daily loss buffer reached")
    if ftmo.total_margin_pct <= 0:
        failures.append("total loss buffer reached")
    if snapshot.consecutive_losses_today >= int(account_cfg.get("max_consecutive_losses", 99)):
        failures.append("max consecutive losses reached")
    if snapshot.trades_today >= int(account_cfg.get("max_trades_per_day", 99)):
        failures.append("max trades per day reached")
    if failures:
        return ValidatorResult(status=Status.BLOCKED, decision=Decision.SEM_TRADE,
                               failures=failures, description="FTMO account-risk gate failed.")

    # 3. News blackout
    if news.blackout:
        return ValidatorResult(status=Status.BLOCKED, decision=Decision.SEM_TRADE,
                               failures=[news.blackout_reason or "high-impact news blackout"],
                               description="News blackout active.")

    # 4. Session timing
    if not session.in_entry_window:
        return ValidatorResult(status=Status.GO, decision=Decision.AGUARDAR,
                               description=f"Outside entry window. Next: {session.next_window}.")

    # 5. Setup presence + confluence
    best = max(setups, key=lambda s: s.confluence_score, default=None)
    if best is None:
        return ValidatorResult(status=Status.GO, decision=Decision.AGUARDAR,
                               description="No setup candidate.")
    if best.confluence_score < min_confluence:
        return ValidatorResult(status=Status.GO, decision=Decision.AGUARDAR,
                               failures=[f"confluence {best.confluence_score} < {min_confluence}"],
                               description="Insufficient confluence.")

    # 6. Risk approval
    if risk is None or not risk.approved:
        return ValidatorResult(status=Status.BLOCKED, decision=Decision.SEM_TRADE,
                               failures=[risk.reason if risk else "no risk calculation"],
                               description="Risk/RR gate failed.")

    # 7. Pass
    decision = Decision.COMPRAR if best.direction == "LONG" else Decision.VENDER
    return ValidatorResult(status=Status.GO, decision=decision,
                           description=f"All gates passed for {best.model} {best.direction}.")
