from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class Factor(ABC):
    name: str

    @abstractmethod
    def calculate(self, bars: pd.DataFrame, trade_date: date) -> pd.Series:
        """Return a Series indexed by ts_code for one trade date."""
