"""Risk + FTMO engine. Protection before profit. Sizing is generic over forex/index via
per-symbol pip_size and pip_value_per_lot (money per pip per 1.0 lot)."""
from __future__ import annotations

from data_pipeline.schemas import (
    AccountSnapshot,
    FTMOLimits,
    RiskCalculation,
    SetupCandidate,
)


def build_ftmo_limits(snapshot: AccountSnapshot, account_cfg: dict) -> FTMOLimits:
    daily_buffer = float(account_cfg["daily_buffer_pct"])
    total_buffer = float(account_cfg["max_total_buffer_pct"])
    current_daily_loss = max(0.0, -snapshot.daily_pnl_pct)
    current_total_dd = max(0.0, snapshot.drawdown_pct)
    return FTMOLimits(
        daily_margin_pct=round(daily_buffer - current_daily_loss, 3),
        total_margin_pct=round(total_buffer - current_total_dd, 3),
        daily_buffer_pct=daily_buffer,
        total_buffer_pct=total_buffer,
    )


def _round_step(value: float, step: float) -> float:
    return round(round(value / step) * step, 10)


def evaluate_risk(
    setup: SetupCandidate,
    symbol_cfg: dict,
    account_cfg: dict,
    snapshot: AccountSnapshot,
) -> RiskCalculation:
    pip_size = float(symbol_cfg["pip_size"])
    pip_value = float(symbol_cfg["pip_value_per_lot"])
    min_lot = float(symbol_cfg["min_lot"])
    lot_step = float(symbol_cfg["lot_step"])
    max_lot = float(symbol_cfg["max_lot"])
    min_stop_pips = float(symbol_cfg["min_stop_pips"])

    risk_pct = float(account_cfg["risk_per_trade_pct"])
    min_rr = float(account_cfg["min_rr_ratio"])
    base = snapshot.balance or float(account_cfg["initial_capital"])
    risk_amount = base * risk_pct / 100.0

    stop_pips = abs(setup.entry_level - setup.stop) / pip_size
    target = setup.targets[0] if setup.targets else setup.entry_level
    reward_pips = abs(target - setup.entry_level) / pip_size
    rr = (reward_pips / stop_pips) if stop_pips > 0 else 0.0

    reason = None
    approved = True
    lot = 0.0
    if stop_pips < min_stop_pips:
        approved, reason = False, f"stop too tight ({stop_pips:.1f} < {min_stop_pips} pips)"
    elif stop_pips <= 0 or pip_value <= 0:
        approved, reason = False, "invalid stop/pip value"
    else:
        lot = _round_step(risk_amount / (stop_pips * pip_value), lot_step)
        if lot < min_lot:
            approved, reason = False, f"required lot {lot} below min {min_lot} (stop too wide)"
        elif lot > max_lot:
            approved, reason = False, f"required lot {lot} above max {max_lot}"
        elif rr < min_rr - 1e-9:
            approved, reason = False, f"reward:risk {rr:.2f} < min {min_rr}"

    return RiskCalculation(
        risk_pct=risk_pct,
        risk_amount=round(risk_amount, 2),
        stop_pips=round(stop_pips, 2),
        reward_pips=round(reward_pips, 2),
        reward_risk=round(rr, 2),
        lot_size=lot,
        approved=approved,
        reason=reason,
    )
