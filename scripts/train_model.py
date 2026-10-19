from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aquant.core.config import load_config
from aquant.data.repository import DataRepository
from aquant.factors.service import FactorService
from aquant.ml.dataset import DatasetBuilder
from aquant.ml.trainer import LightGBMTrainer
from aquant.strategy.universe import UniverseBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a LightGBM model from local factor data.")
    parser.add_argument("--config", default="configs/strategy_lgbm_top5.yaml")
    parser.add_argument("--data", default="data/sample")
    parser.add_argument("--train-start", required=True)
    parser.add_argument("--train-end", required=True)
    parser.add_argument("--valid-start", required=True)
    parser.add_argument("--valid-end", required=True)
    parser.add_argument("--model-dir", default="data/models")
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--horizon", type=int, default=5)
    args = parser.parse_args()

    config = load_config(args.config)
    repo = DataRepository.from_parquet(args.data)
    factor_service = FactorService(repo)
    universe_builder = UniverseBuilder(repo, config)
    dataset_builder = DatasetBuilder(repo, universe_builder, factor_service)
    label_col = config.model.get("label", "future_5d_excess_return")

    train = dataset_builder.build(
        date.fromisoformat(args.train_start),
        date.fromisoformat(args.train_end),
        horizon=args.horizon,
        label_col=label_col,
    )
    valid = dataset_builder.build(
        date.fromisoformat(args.valid_start),
        date.fromisoformat(args.valid_end),
        horizon=args.horizon,
        label_col=label_col,
    )

    if train.frame.empty or valid.frame.empty:
        raise SystemExit("Training and validation datasets must both contain rows")

    feature_cols = train.feature_cols
    if not feature_cols:
        raise SystemExit("No numeric feature columns were produced")

    model_version = args.model_version or f"lgbm-{args.train_end}-{args.valid_end}"
    trainer = LightGBMTrainer(args.model_dir)
    model = trainer.train(
        train_df=train.frame,
        valid_df=valid.frame,
        feature_cols=feature_cols,
        label_col=label_col,
        model_version=model_version,
    )

    predictions = model.predict(valid.frame[feature_cols])
    correlation = np.corrcoef(predictions, valid.frame[label_col].to_numpy())[0, 1]
    if np.isnan(correlation):
        correlation = 0.0

    print(f"Saved model: {Path(args.model_dir) / f'{model_version}.joblib'}")
    print(f"train_rows={len(train.frame)} valid_rows={len(valid.frame)} features={len(feature_cols)}")
    print(f"validation_corr={correlation:.6f}")
    print("top_features:")
    importances = sorted(
        zip(feature_cols, model.feature_importances_, strict=False),
        key=lambda item: item[1],
        reverse=True,
    )
    for name, importance in importances[:10]:
        print(f"  {name}: {importance}")


if __name__ == "__main__":
    main()
