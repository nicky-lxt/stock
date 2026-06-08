from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aquant.core.config import load_config
from aquant.data.repository import DataRepository
from aquant.factors.service import FactorService
from aquant.ml.predictor import HeuristicPredictor
from aquant.risk.engine import RiskEngine
from aquant.strategy.portfolio import PortfolioBuilder
from aquant.strategy.universe import UniverseBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly Top5 targets from local data.")
    parser.add_argument("--config", default="configs/strategy_lgbm_top5.yaml")
    parser.add_argument("--data", default="data/sample")
    parser.add_argument("--date", required=True, help="Prediction date, YYYY-MM-DD")
    args = parser.parse_args()

    config = load_config(args.config)
    repo = DataRepository.from_parquet(args.data)
    predict_date = date.fromisoformat(args.date)

    universe_builder = UniverseBuilder(repo, config)
    risk_engine = RiskEngine(config, repo)
    factor_service = FactorService(repo)
    predictor = HeuristicPredictor()
    portfolio_builder = PortfolioBuilder(config, risk_engine)

    universe = universe_builder.build(predict_date)
    factors = factor_service.load_or_calculate(predict_date, universe)
    predictions = predictor.predict(predict_date, factors)
    targets = portfolio_builder.build(predict_date, predictions)

    print("Top predictions:")
    for pred in predictions[:10]:
        print(f"{pred.rank:02d} {pred.ts_code} score={pred.score:.6f}")

    print("\nTarget portfolio:")
    for target in targets:
        print(f"{target.ts_code} weight={target.target_weight:.2%} score={target.score:.6f}")


if __name__ == "__main__":
    main()
