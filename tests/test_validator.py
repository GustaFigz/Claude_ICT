from data_pipeline.schemas import (
    AccountSnapshot, DataQuality, Decision, FTMOLimits, NewsState,
    RiskCalculation, SessionState, SetupCandidate, Status,
)
from ict_engine.validator import validate

ACCOUNT = {"max_consecutive_losses": 2, "max_trades_per_day": 3}


def _ok_inputs():
    dq = DataQuality(source="fixtures", fresh=True)
    snap = AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0)
    ftmo = FTMOLimits(daily_margin_pct=3.5, total_margin_pct=8.0, daily_buffer_pct=3.5, total_buffer_pct=8.0)
    session = SessionState(active_session="ny_am_silver_bullet", in_kill_zone=True, in_entry_window=True)
    news = NewsState()
    setup = SetupCandidate(model="silver_bullet", direction="LONG", entry_level=1.1, stop=1.095,
                           targets=[1.11], confluence_factors=["a", "b", "c"], confluence_score=3)
    risk = RiskCalculation(risk_pct=0.5, risk_amount=50, stop_pips=50, reward_pips=100,
                           reward_risk=2.0, lot_size=0.1, approved=True)
    return dq, snap, ftmo, session, news, [setup], risk


def test_full_pass_comprar():
    r = validate(*_ok_inputs(), ACCOUNT)
    assert r.status == Status.GO and r.decision == Decision.COMPRAR


def test_news_blackout_blocks():
    dq, snap, ftmo, session, _news, setups, risk = _ok_inputs()
    news = NewsState(blackout=True, blackout_reason="USD NFP in 30 min")
    r = validate(dq, snap, ftmo, session, news, setups, risk, ACCOUNT)
    assert r.status == Status.BLOCKED and r.decision == Decision.SEM_TRADE


def test_account_breach_blocks():
    dq, snap, _ftmo, session, news, setups, risk = _ok_inputs()
    ftmo = FTMOLimits(daily_margin_pct=0.0, total_margin_pct=8.0, daily_buffer_pct=3.5, total_buffer_pct=8.0)
    r = validate(dq, snap, ftmo, session, news, setups, risk, ACCOUNT)
    assert r.status == Status.BLOCKED and "daily" in " ".join(r.failures)


def test_outside_window_aguardar():
    dq, snap, ftmo, _session, news, setups, risk = _ok_inputs()
    session = SessionState(in_entry_window=False, next_window="ny_am @ tomorrow")
    r = validate(dq, snap, ftmo, session, news, setups, risk, ACCOUNT)
    assert r.status == Status.GO and r.decision == Decision.AGUARDAR


def test_stale_data_blocks():
    dq, snap, ftmo, session, news, setups, risk = _ok_inputs()
    dq = DataQuality(source="mt5", fresh=False)
    r = validate(dq, snap, ftmo, session, news, setups, risk, ACCOUNT)
    assert r.status == Status.BLOCKED


def test_warn_only_risk_yields_aguardar():
    dq, snap, ftmo, session, news, setups, _ = _ok_inputs()
    risk = RiskCalculation(risk_pct=0.5, risk_amount=50, stop_pips=50, reward_pips=85,
                           reward_risk=1.7, lot_size=0.1, approved=False, warn_only=True,
                           reason="reward:risk 1.70 marginal (warn zone 1.5-2.0)")
    r = validate(dq, snap, ftmo, session, news, setups, risk, ACCOUNT)
    assert r.status == Status.GO
    assert r.decision == Decision.AGUARDAR
    assert r.setup_preview is not None


def test_consecutive_losses_at_limit_blocks():
    dq, _, ftmo, session, news, setups, risk = _ok_inputs()
    snap = AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0,
                           consecutive_losses_today=3)
    account = {"max_consecutive_losses": 3, "max_trades_per_day": 3}
    r = validate(dq, snap, ftmo, session, news, setups, risk, account)
    assert r.status == Status.BLOCKED
    assert any("consecutive" in f for f in r.failures)


def test_consecutive_losses_below_limit_passes():
    dq, _, ftmo, session, news, setups, risk = _ok_inputs()
    snap = AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0,
                           consecutive_losses_today=2)
    account = {"max_consecutive_losses": 3, "max_trades_per_day": 3}
    r = validate(dq, snap, ftmo, session, news, setups, risk, account)
    assert r.status == Status.GO
    assert r.decision == Decision.COMPRAR
