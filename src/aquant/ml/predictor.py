from __future__ import annotations

from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from aquant.core.types import Prediction


class Predictor:
    def __init__(self, model_path: str | Path):
        artifact = joblib.load(model_path)
        self.model = artifact["model"]
        self.feature_cols = artifact["feature_cols"]
        self.model_version = artifact["model_version"]

    def predict(self, predict_date: date, factors: pd.DataFrame) -> list[Prediction]:
        scores = self.model.predict(factors[self.feature_cols])
        return _rank_predictions(predict_date, factors["ts_code"].tolist(), scores, self.model_version)


class HeuristicPredictor:
    """Deterministic fallback for local demos before a LightGBM model is trained."""

    model_version = "heuristic-v0"

    def predict(self, predict_date: date, factors: pd.DataFrame) -> list[Prediction]:
        score = pd.Series(0.0, index=factors.index)
        weights = {
            "return_20d": 0.35,
            "return_60d": 0.25,
            "reverse_return_5d": 0.10,
            "volatility_20d": -0.15,
            "distance_to_ma20": 0.10,
            "amount_growth_5d": 0.05,
        }
        for col, weight in weights.items():
            if col in factors:
                score = score + factors[col].fillna(0.0) * weight
        return _rank_predictions(predict_date, factors["ts_code"].tolist(), score, self.model_version)


def _rank_predictions(
    predict_date: date,
    ts_codes: list[str],
    scores,
    model_version: str,
) -> list[Prediction]:
    result = pd.DataFrame({"ts_code": ts_codes, "score": scores})
    result["rank"] = result["score"].rank(ascending=False, method="first").astype(int)
    result = result.sort_values("rank")
    return [
        Prediction(
            predict_date=predict_date,
            ts_code=row.ts_code,
            score=float(row.score),
            rank=int(row.rank),
            model_version=model_version,
        )
        for row in result.itertuples(index=False)
    ]
