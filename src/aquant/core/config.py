from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class PortfolioConfig(BaseModel):
    max_positions: int = 5
    min_positions: int = 3
    weight_method: str = "equal"
    default_single_weight: float = 0.20
    single_stock_soft_cap: float = 0.30
    single_stock_hard_cap: float = 0.50
    allow_manual_confirm_above_soft_cap: bool = True


class RiskConfig(BaseModel):
    max_single_position_auto: float = 0.30
    max_single_position_manual: float = 0.50
    max_industry_exposure: float = 0.60
    max_daily_loss: float = 0.025
    max_weekly_loss: float = 0.05
    max_drawdown: float = 0.10
    weak_market_max_position: float = 0.50
    normal_market_max_position: float = 0.70
    strong_market_max_position: float = 1.00
    kill_switch_enabled: bool = False
    reduce_only: bool = False


class StrategyConfig(BaseModel):
    name: str
    universe: dict[str, Any]
    rebalance: dict[str, Any]
    portfolio: PortfolioConfig
    filters: dict[str, Any]


class AppConfig(BaseModel):
    app: dict[str, Any] = {}
    strategy: StrategyConfig
    risk: RiskConfig
    data: dict[str, Any]
    model: dict[str, Any]
    backtest: dict[str, Any]


def load_config(path: str | Path) -> AppConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return AppConfig(**raw)
