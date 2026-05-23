import json
from datetime import datetime, timezone

from data_pipeline.schemas import (
    AccountSnapshot, AnalysisContext, DataQuality, Decision, FTMOLimits,
    NewsState, SessionState, Status, ValidatorResult,
)


def _minimal_context() -> AnalysisContext:
    return AnalysisContext(
        run_id="abc123",
        created_at_utc=datetime(2026, 5, 26, 14, 30, tzinfo=timezone.utc),
        symbol="EURUSD",
        broker_symbol="EURUSD",
        data_quality=DataQuality(source="fixtures", fresh=True),
        account_snapshot=AccountSnapshot(balance=10000, equity=10000, daily_pnl_pct=0.0, drawdown_pct=0.0),
        ftmo_limits=FTMOLimits(daily_margin_pct=3.5, total_margin_pct=8.0, daily_buffer_pct=3.5, total_buffer_pct=8.0),
        session_state=SessionState(),
        news_state=NewsState(),
        structure=__import__("data_pipeline.schemas", fromlist=["Structure"]).Structure(),
        liquidity=__import__("data_pipeline.schemas", fromlist=["Liquidity"]).Liquidity(),
        validator_result=ValidatorResult(status=Status.GO, decision=Decision.AGUARDAR),
    )


def test_context_json_roundtrip():
    ctx = _minimal_context()
    payload = json.loads(ctx.model_dump_json())
    assert payload["symbol"] == "EURUSD"
    assert payload["validator_result"]["decision"] == "AGUARDAR"
    # rebuild from dumped JSON
    ctx2 = AnalysisContext.model_validate(payload)
    assert ctx2.run_id == "abc123"
