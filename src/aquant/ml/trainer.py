from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


class LightGBMTrainer:
    def __init__(self, model_dir: str | Path = "data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame,
        feature_cols: list[str],
        label_col: str,
        model_version: str,
    ):
        import lightgbm as lgb

        model = lgb.LGBMRegressor(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=5,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="regression",
            random_state=42,
            verbosity=-1,
        )

        model.fit(
            train_df[feature_cols],
            train_df[label_col],
            eval_set=[(valid_df[feature_cols], valid_df[label_col])],
            eval_metric="l2",
        )

        path = self.model_dir / f"{model_version}.joblib"
        joblib.dump(
            {
                "model": model,
                "feature_cols": feature_cols,
                "label_col": label_col,
                "model_version": model_version,
            },
            path,
        )
        return model
