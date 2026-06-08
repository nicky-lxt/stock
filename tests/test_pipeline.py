from __future__ import annotations

from datetime import date

from aquant.backtest.broker import BacktestBroker
from aquant.backtest.engine import BacktestEngine
from aquant.backtest.metrics import Metrics
from aquant.core.config import load_config
from aquant.data.repository import DataRepository
from aquant.data.sample import make_sample_daily_bars, make_sample_index_members
from aquant.factors.service import FactorService
from aquant.ml.predictor import HeuristicPredictor
from aquant.risk.engine import RiskEngine
from aquant.strategy.portfolio import PortfolioBuilder
from aquant.strategy.universe import UniverseBuilder


def make_repo() -> DataRepository:
    bars = make_sample_daily_bars(start="2023-01-02", periods=160, stock_count=8)
    members = make_sample_index_members(bars)
    return DataRepository(bars, members)


def test_config_loads() -> None:
    config = load_config("configs/strategy_lgbm_top5.yaml")
    assert config.strategy.portfolio.max_positions == 5
    assert config.strategy.universe["indexes"] == ["000300.SH", "000905.SH"]


def test_universe_factors_and_portfolio() -> None:
    config = load_config("configs/strategy_lgbm_top5.yaml")
    repo = make_repo()
    trade_date = repo.get_trading_days(date(2023, 1, 2), date(2023, 12, 31))[-1]

    universe = UniverseBuilder(repo, config).build(trade_date)
    factors = FactorService(repo).load_or_calculate(trade_date, universe)
    predictions = HeuristicPredictor().predict(trade_date, factors)
    risk_engine = RiskEngine(config, repo)
    targets = PortfolioBuilder(config, risk_engine).build(trade_date, predictions)

    assert len(universe) == 8
    assert len(factors) == 8
    assert len(targets) == 5
    assert round(sum(target.target_weight for target in targets), 6) == 1.0


def test_backtest_smoke() -> None:
    config = load_config("configs/strategy_lgbm_top5.yaml")
    repo = make_repo()
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

    result = engine.run(date(2023, 4, 3), date(2023, 8, 11))

    assert result["summary"]["trading_days"] > 0
    assert result["summary"]["end_asset"] > 0
