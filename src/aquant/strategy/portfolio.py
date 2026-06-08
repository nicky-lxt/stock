from __future__ import annotations

from datetime import date

from aquant.core.types import Prediction, TargetPosition


class PortfolioBuilder:
    def __init__(self, config, risk_engine):
        self.config = config
        self.risk_engine = risk_engine

    def build(self, target_date: date, predictions: list[Prediction]) -> list[TargetPosition]:
        portfolio_cfg = self.config.strategy.portfolio
        selected: list[Prediction] = []

        for pred in sorted(predictions, key=lambda item: item.rank):
            if self.risk_engine.check_candidate(pred.ts_code, target_date):
                selected.append(pred)
            if len(selected) >= portfolio_cfg.max_positions:
                break

        if len(selected) < portfolio_cfg.min_positions:
            return []

        total_weight = self._market_position_cap(target_date)
        weight = total_weight / len(selected)

        return [
            TargetPosition(
                target_date=target_date,
                ts_code=pred.ts_code,
                target_weight=weight,
                score=pred.score,
                reason="LightGBM/heuristic top ranked stock",
            )
            for pred in selected
        ]

    def _market_position_cap(self, target_date: date) -> float:
        return self.config.risk.strong_market_max_position
