from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


@dataclass
class DataRepository:
    """Small local repository backed by DataFrames and optional Parquet files."""

    daily_bars: pd.DataFrame
    index_members: pd.DataFrame
    parquet_root: Path | None = None

    @classmethod
    def from_parquet(cls, parquet_root: str | Path) -> "DataRepository":
        root = Path(parquet_root)
        return cls(
            daily_bars=pd.read_parquet(root / "daily_bars.parquet"),
            index_members=pd.read_parquet(root / "index_members.parquet"),
            parquet_root=root,
        )

    def write_parquet(self, parquet_root: str | Path | None = None) -> None:
        root = Path(parquet_root) if parquet_root is not None else self.parquet_root
        if root is None:
            raise ValueError("parquet_root is required")
        root.mkdir(parents=True, exist_ok=True)
        self.daily_bars.to_parquet(root / "daily_bars.parquet", index=False)
        self.index_members.to_parquet(root / "index_members.parquet", index=False)

    def get_trading_days(self, start: date, end: date) -> list[date]:
        days = self.daily_bars["trade_date"].drop_duplicates().sort_values()
        return [d for d in days if start <= d <= end]

    def get_daily_bars(
        self,
        ts_codes: list[str] | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        bars = self.daily_bars
        if ts_codes is not None:
            bars = bars[bars["ts_code"].isin(ts_codes)]
        if start is not None:
            bars = bars[bars["trade_date"] >= start]
        if end is not None:
            bars = bars[bars["trade_date"] <= end]
        return bars.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)

    def get_index_members(self, index_codes: list[str], trade_date: date) -> pd.DataFrame:
        members = self.index_members[self.index_members["index_code"].isin(index_codes)].copy()
        members = members[members["in_date"] <= trade_date]
        members = members[members["out_date"].isna() | (members["out_date"] > trade_date)]
        return members.drop_duplicates("ts_code").reset_index(drop=True)

    def latest_bar(self, ts_code: str, trade_date: date) -> pd.Series | None:
        rows = self.daily_bars[
            (self.daily_bars["ts_code"] == ts_code) & (self.daily_bars["trade_date"] == trade_date)
        ]
        if rows.empty:
            return None
        return rows.iloc[0]

    def is_st(self, ts_code: str, trade_date: date) -> bool:
        bar = self.latest_bar(ts_code, trade_date)
        return bool(False if bar is None else bar.get("is_st", False))

    def is_suspended(self, ts_code: str, trade_date: date) -> bool:
        bar = self.latest_bar(ts_code, trade_date)
        return bool(True if bar is None else bar.get("is_suspended", False))

    def is_limit_up(self, ts_code: str, trade_date: date) -> bool:
        bar = self.latest_bar(ts_code, trade_date)
        return bool(False if bar is None else bar.get("is_limit_up", False))

    def is_limit_down(self, ts_code: str, trade_date: date) -> bool:
        bar = self.latest_bar(ts_code, trade_date)
        return bool(False if bar is None else bar.get("is_limit_down", False))

    def listed_days(self, ts_code: str, trade_date: date) -> int:
        stock_rows = self.daily_bars[self.daily_bars["ts_code"] == ts_code]
        if not stock_rows.empty and "list_date" in stock_rows:
            list_date = stock_rows["list_date"].dropna()
            if not list_date.empty:
                first_list_date = list_date.iloc[0]
                if isinstance(first_list_date, pd.Timestamp):
                    first_list_date = first_list_date.date()
                return max((trade_date - first_list_date).days, 0)

        bars = self.daily_bars[
            (self.daily_bars["ts_code"] == ts_code) & (self.daily_bars["trade_date"] <= trade_date)
        ]
        return int(len(bars))

    def avg_amount(self, ts_code: str, trade_date: date, window: int) -> float:
        bars = self.daily_bars[
            (self.daily_bars["ts_code"] == ts_code) & (self.daily_bars["trade_date"] <= trade_date)
        ].sort_values("trade_date")
        if bars.empty:
            return 0.0
        return float(bars.tail(window)["amount"].mean())

    def get_price(self, ts_code: str, trade_date: date, field: str = "close") -> float:
        bar = self.latest_bar(ts_code, trade_date)
        if bar is None:
            raise KeyError(f"Missing {field} for {ts_code} on {trade_date}")
        return float(bar[field])
