from data_pipeline.schemas import AccountSnapshot, SetupCandidate
from ict_engine.risk import build_ftmo_limits, evaluate_risk

ACCOUNT = {
    "initial_capital": 10000, "daily_buffer_pct": 3.5, "max_total_buffer_pct": 8.0,
    "risk_per_trade_pct": 0.5, "min_rr_ratio": 2.0,
}
EURUSD = {
    "pip_size": 0.0001, "pip_value_per_lot": 10.0, "min_lot": 0.01, "lot_step": 0.01,
    "max_lot": 50.0, "min_stop_pips": 8,
}


def _snap():
    return AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0)


def test_ftmo_limits_room():
    snap = AccountSnapshot(balance=9850, equity=9850, daily_pnl_pct=-1.5, drawdown_pct=2.0)
    lim = build_ftmo_limits(snap, ACCOUNT)
    assert lim.daily_margin_pct == 2.0
    assert lim.total_margin_pct == 6.0


def test_risk_approved_two_r():
    setup = SetupCandidate(model="silver_bullet", direction="LONG",
                           entry_level=1.1000, stop=1.0950, targets=[1.1100])
    r = evaluate_risk(setup, EURUSD, ACCOUNT, _snap())
    assert r.approved is True
    assert r.stop_pips == 50.0 and r.reward_risk == 2.0
    assert abs(r.lot_size - 0.10) < 1e-9


def test_risk_rejected_tight_stop():
    setup = SetupCandidate(model="silver_bullet", direction="LONG",
                           entry_level=1.1000, stop=1.09995, targets=[1.1100])
    r = evaluate_risk(setup, EURUSD, ACCOUNT, _snap())
    assert r.approved is False and "tight" in (r.reason or "")


def test_risk_rejected_low_rr():
    setup = SetupCandidate(model="silver_bullet", direction="LONG",
                           entry_level=1.1000, stop=1.0950, targets=[1.1075])
    r = evaluate_risk(setup, EURUSD, ACCOUNT, _snap())
    assert r.approved is False and "reward:risk" in (r.reason or "")
