from __future__ import annotations

from datetime import date

import pandas as pd

from aquant.factors.base import Factor


def _close_matrix(bars: pd.DataFrame) -> pd.DataFrame:
    return bars.pivot(index="trade_date", columns="ts_code", values="close").sort_index()


class ReturnFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"return_{window}d"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        values = _close_matrix(bars).pct_change(self.window).loc[trade_date]
        values.name = self.name
        return values


class ReverseReturnFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"reverse_return_{window}d"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        values = -_close_matrix(bars).pct_change(self.window).loc[trade_date]
        values.name = self.name
        return values


class VolatilityFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"volatility_{window}d"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        returns = _close_matrix(bars).pct_change()
        values = returns.rolling(self.window).std().loc[trade_date]
        values.name = self.name
        return values


class DistanceToMAFactor(Factor):
    def __init__(self, window: int):
        self.window = window
        self.name = f"distance_to_ma{window}"

    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        close = _close_matrix(bars)
        ma = close.rolling(self.window).mean()
        values = close.loc[trade_date] / ma.loc[trade_date] - 1
        values.name = self.name
        return values
