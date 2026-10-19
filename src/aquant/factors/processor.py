from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class FactorProcessor:
    def fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.fillna(df.median(numeric_only=True)).fillna(0.0)

    def winsorize_mad(self, df: pd.DataFrame, n: float = 5.0) -> pd.DataFrame:
        result = df.copy()
        for col in result.columns:
            median = result[col].median()
            mad = np.median(np.abs(result[col] - median))
            if mad == 0 or np.isnan(mad):
                continue
            lower = median - n * 1.4826 * mad
            upper = median + n * 1.4826 * mad
            result[col] = result[col].clip(lower, upper)
        return result

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        scaler = StandardScaler()
        values = scaler.fit_transform(df)
        return pd.DataFrame(values, index=df.index, columns=df.columns)

    def process(self, factors: pd.DataFrame) -> pd.DataFrame:
        processed = self.fill_missing(factors)
        processed = self.winsorize_mad(processed)
        return self.standardize(processed)
