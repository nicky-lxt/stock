from __future__ import annotations

from datetime import date

import pandas as pd


class UniverseBuilder:
    def __init__(self, data_repo, config):
        self.data_repo = data_repo
        self.config = config

    def build(self, trade_date: date) -> pd.DataFrame:
        index_codes = self.config.strategy.universe["indexes"]
        members = self.data_repo.get_index_members(index_codes, trade_date)
        rows = []

        for stock in members.itertuples(index=False):
            ts_code = stock.ts_code
            if self._should_exclude(ts_code, trade_date):
                continue
            rows.append(stock._asdict())

        return pd.DataFrame(rows)

    def _should_exclude(self, ts_code: str, trade_date: date) -> bool:
        filters = self.config.strategy.filters
        if filters.get("exclude_st") and self.data_repo.is_st(ts_code, trade_date):
            return True
        if filters.get("exclude_suspended") and self.data_repo.is_suspended(ts_code, trade_date):
            return True
        min_days = filters.get("exclude_new_stock_days", 120)
        if self.data_repo.listed_days(ts_code, trade_date) < min_days:
            return True
        min_amount = filters.get("min_avg_amount_20d", 200_000_000)
        return self.data_repo.avg_amount(ts_code, trade_date, window=20) < min_amount
