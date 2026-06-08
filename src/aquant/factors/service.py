from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from aquant.factors.price import (
    DistanceToMAFactor,
    ReturnFactor,
    ReverseReturnFactor,
    VolatilityFactor,
)
from aquant.factors.processor import FactorProcessor
from aquant.factors.volume import AmountGrowthFactor, AmountMeanFactor


class FactorService:
    def __init__(self, data_repo, processor: FactorProcessor | None = None):
        self.data_repo = data_repo
        self.processor = processor or FactorProcessor()
        self.factors = [
            ReturnFactor(5),
            ReturnFactor(20),
            ReturnFactor(60),
            ReverseReturnFactor(5),
            VolatilityFactor(20),
            VolatilityFactor(60),
            DistanceToMAFactor(20),
            AmountMeanFactor(20),
            AmountGrowthFactor(5),
        ]

    def load_or_calculate(self, trade_date: date, universe: pd.DataFrame) -> pd.DataFrame:
        ts_codes = universe["ts_code"].tolist()
        lookback_start = trade_date - timedelta(days=140)
        bars = self.data_repo.get_daily_bars(ts_codes=ts_codes, start=lookback_start, end=trade_date)
        if bars.empty:
            return pd.DataFrame(columns=["ts_code"])

        raw = pd.DataFrame(index=ts_codes)
        for factor in self.factors:
            raw[factor.name] = factor.calculate(bars, trade_date).reindex(ts_codes)

        processed = self.processor.process(raw)
        processed.insert(0, "ts_code", processed.index)
        processed["trade_date"] = trade_date
        return processed.reset_index(drop=True)
