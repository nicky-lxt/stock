from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class SupervisedDataset:
    frame: pd.DataFrame
    feature_cols: list[str]
    label_col: str


class DatasetBuilder:
    """Build point-in-time factor rows with forward excess-return labels."""

    def __init__(self, data_repo, universe_builder, factor_service):
        self.data_repo = data_repo
        self.universe_builder = universe_builder
        self.factor_service = factor_service

    def build(
        self,
        start: date,
        end: date,
        horizon: int = 5,
        label_col: str = "future_5d_excess_return",
    ) -> SupervisedDataset:
        trading_days = self.data_repo.get_trading_days(start, end)
        rows: list[pd.DataFrame] = []

        for idx, trade_date in enumerate(trading_days):
            future_idx = idx + horizon
            if future_idx >= len(trading_days):
                break

            future_date = trading_days[future_idx]
            universe = self.universe_builder.build(trade_date)
            if universe.empty:
                continue

            factors = self.factor_service.load_or_calculate(trade_date, universe)
            if factors.empty:
                continue

            labels = self._build_labels(factors["ts_code"].tolist(), trade_date, future_date, label_col)
            if labels.empty:
                continue

            rows.append(factors.merge(labels, on="ts_code", how="inner"))

        if rows:
            frame = pd.concat(rows, ignore_index=True)
        else:
            frame = pd.DataFrame(columns=["ts_code", "trade_date", label_col])

        feature_cols = [
            col
            for col in frame.columns
            if col not in {"ts_code", "trade_date", label_col}
            and pd.api.types.is_numeric_dtype(frame[col])
        ]
        return SupervisedDataset(frame=frame, feature_cols=feature_cols, label_col=label_col)

    def _build_labels(
        self,
        ts_codes: list[str],
        trade_date: date,
        future_date: date,
        label_col: str,
    ) -> pd.DataFrame:
        label_rows = []
        for ts_code in ts_codes:
            try:
                current_price = self.data_repo.get_price(ts_code, trade_date)
                future_price = self.data_repo.get_price(ts_code, future_date)
            except KeyError:
                continue
            if current_price <= 0:
                continue
            label_rows.append(
                {
                    "ts_code": ts_code,
                    "future_return": future_price / current_price - 1,
                }
            )

        labels = pd.DataFrame(label_rows)
        if labels.empty:
            return pd.DataFrame(columns=["ts_code", label_col])

        labels[label_col] = labels["future_return"] - labels["future_return"].mean()
        return labels[["ts_code", label_col]]
