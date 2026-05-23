"""Pydantic data contracts. The JSON the Claude layer reads is an AnalysisContext dump.

Everything here is calculated by Python. The Claude layer must cite these fields and
never invent values. If a required piece is missing, the validator yields BLOCKED.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    COMPRAR = "COMPRAR"
    VENDER = "VENDER"
    AGUARDAR = "AGUARDAR"
    SEM_TRADE = "SEM_TRADE"


class Status(str, Enum):
    GO = "GO"
    BLOCKED = "BLOCKED"


Direction = Literal["LONG", "SHORT"]


class Candle(BaseModel):
    time: datetime  # UTC, candle open time
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class Timeframe(BaseModel):
    name: str  # MN, W1, D1, H4, H1, M15, M5, M1
    candles: list[Candle] = Field(default_factory=list)


class SwingPoint(BaseModel):
    index: int
    time: datetime
    price: float
    kind: Literal["high", "low"]


class FVG(BaseModel):
    kind: Literal["bullish", "bearish"]
    top: float
    bottom: float
    time: datetime
    size_pips: float
    filled: bool = False


class OrderBlock(BaseModel):
    kind: Literal["bullish", "bearish"]
    top: float
    bottom: float
    time: datetime
    mitigated: bool = False


class LiquidityPool(BaseModel):
    kind: Literal["BSL", "SSL"]  # buy-side (above) / sell-side (below)
    price: float
    touches: int


class StructureTF(BaseModel):
    timeframe: str
    bias: Literal["UP", "DOWN", "SIDEWAYS"]
    last_event: Optional[Literal["BOS_UP", "BOS_DOWN", "CHOCH_UP", "CHOCH_DOWN"]] = None
    last_swing_high: Optional[float] = None
    last_swing_low: Optional[float] = None


class Structure(BaseModel):
    by_tf: dict[str, StructureTF] = Field(default_factory=dict)
    bias_d1_h4_h1: Literal["UP", "DOWN", "SIDEWAYS", "CONFLICT"] = "SIDEWAYS"
    fvg_active: list[FVG] = Field(default_factory=list)


class Liquidity(BaseModel):
    pools: list[LiquidityPool] = Field(default_factory=list)
    target: Optional[str] = None        # e.g. "BSL @ 1.0950"
    draw_direction: Optional[Literal["UP", "DOWN"]] = None
    equilibrium: Optional[float] = None
    premium_zone: Optional[tuple[float, float]] = None
    discount_zone: Optional[tuple[float, float]] = None


class SetupCandidate(BaseModel):
    model: str
    direction: Direction
    entry_level: float
    stop: float
    targets: list[float] = Field(default_factory=list)
    confluence_factors: list[str] = Field(default_factory=list)
    confluence_score: int = 0


class RiskCalculation(BaseModel):
    risk_pct: float
    risk_amount: float
    stop_pips: float
    reward_pips: float
    reward_risk: float
    lot_size: float
    approved: bool
    reason: Optional[str] = None


class AccountSnapshot(BaseModel):
    balance: float
    equity: float
    daily_pnl_pct: float            # closed + floating, since FTMO daily anchor
    drawdown_pct: float             # total drawdown from start/peak
    open_positions: int = 0
    consecutive_losses_today: int = 0
    trades_today: int = 0


class FTMOLimits(BaseModel):
    daily_margin_pct: float         # remaining room to daily buffer
    total_margin_pct: float         # remaining room to total buffer
    daily_buffer_pct: float
    total_buffer_pct: float


class SessionState(BaseModel):
    active_session: Optional[str] = None
    in_kill_zone: bool = False
    in_entry_window: bool = False
    next_window: Optional[str] = None
    ny_time: Optional[str] = None


class NewsEvent(BaseModel):
    time_utc: datetime
    currency: str
    impact: str
    title: str
    minutes_until: Optional[int] = None


class NewsState(BaseModel):
    events_next_48h: list[NewsEvent] = Field(default_factory=list)
    blackout: bool = False
    blackout_reason: Optional[str] = None


class DataQuality(BaseModel):
    source: str                     # fixtures | oanda | mt5
    fresh: bool
    age_seconds: Optional[float] = None
    source_agreement: Optional[bool] = None
    max_divergence_pct: Optional[float] = None
    issues: list[str] = Field(default_factory=list)


class ValidatorResult(BaseModel):
    status: Status
    decision: Decision
    failures: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class AnalysisContext(BaseModel):
    run_id: str
    created_at_utc: datetime
    symbol: str
    broker_symbol: str
    data_quality: DataQuality
    account_snapshot: AccountSnapshot
    ftmo_limits: FTMOLimits
    session_state: SessionState
    news_state: NewsState
    structure: Structure
    liquidity: Liquidity
    setup_candidates: list[SetupCandidate] = Field(default_factory=list)
    risk_calculation: Optional[RiskCalculation] = None
    validator_result: ValidatorResult
