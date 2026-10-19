from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal


Side = Literal["BUY", "SELL"]
OrderStatus = Literal[
    "CREATED",
    "SUBMITTED",
    "ACCEPTED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
]


@dataclass(frozen=True)
class DailyBar:
    trade_date: date
    ts_code: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    volume: float
    amount: float
    adj_factor: float | None = None
    is_suspended: bool = False
    is_limit_up: bool = False
    is_limit_down: bool = False


@dataclass(frozen=True)
class Prediction:
    predict_date: date
    ts_code: str
    score: float
    rank: int
    model_version: str


@dataclass(frozen=True)
class TargetPosition:
    target_date: date
    ts_code: str
    target_weight: float
    score: float
    reason: str


@dataclass(frozen=True)
class OrderIntent:
    strategy_name: str
    ts_code: str
    side: Side
    quantity: int
    price_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    limit_price: float | None = None
    manual_confirmed: bool = False
    reason: str = ""


@dataclass(frozen=True)
class RiskResult:
    approved: bool
    action: Literal["APPROVE", "REJECT", "REDUCE", "WARN"]
    reason: str
    adjusted_order: OrderIntent | None = None


@dataclass
class Position:
    ts_code: str
    quantity: int
    available_quantity: int
    market_value: float
    cost_price: float
    last_price: float

    @property
    def weight_basis_price(self) -> float:
        return self.last_price or self.cost_price


@dataclass
class AccountSnapshot:
    account_id: str
    cash: float
    total_asset: float
    market_value: float
    positions: list[Position] = field(default_factory=list)


@dataclass(frozen=True)
class Trade:
    ts_code: str
    side: Side
    price: float
    quantity: int
    amount: float
    trade_time: datetime
