from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aquant.backtest.broker import BacktestBroker
from aquant.backtest.engine import BacktestEngine
from aquant.backtest.metrics import Metrics
from aquant.core.config import load_config
from aquant.data.repository import DataRepository
from aquant.factors.service import FactorService
from aquant.ml.predictor import HeuristicPredictor
from aquant.risk.engine import RiskEngine
from aquant.strategy.portfolio import PortfolioBuilder
from aquant.strategy.universe import UniverseBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AQuant weekly Top5 sample backtest.")
    parser.add_argument("--config", default="configs/strategy_lgbm_top5.yaml")
    parser.add_argument("--data", default="data/sample")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    repo = DataRepository.from_parquet(args.data)

    risk_engine = RiskEngine(config, repo)
    engine = BacktestEngine(
        data_repo=repo,
        universe_builder=UniverseBuilder(repo, config),
        factor_service=FactorService(repo),
        predictor=HeuristicPredictor(),
        portfolio_builder=PortfolioBuilder(config, risk_engine),
        risk_engine=risk_engine,
        broker=BacktestBroker.from_config(config, repo),
        metrics=Metrics(),
    )
    result = engine.run(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print("Backtest summary:")
    for key, value in result["summary"].items():
        if isinstance(value, float):
            print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
