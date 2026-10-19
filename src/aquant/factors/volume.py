from __future__ import annotations

from datetime import date

import pandas as pd

from aquant.factors.base import Factor


class AmountMeanFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"amount_mean_{window}d"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        amount = bars.pivot(index="trade_date", columns="ts_code", values="amount").sort_index()
        values = amount.rolling(self.window).mean().loc[trade_date]
        values.name = self.name
        return values


class AmountGrowthFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"amount_growth_{window}d"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        amount = bars.pivot(index="trade_date", columns="ts_code", values="amount").sort_index()
        values = amount.pct_change(self.window).loc[trade_date]
        values.name = self.name
        return values
