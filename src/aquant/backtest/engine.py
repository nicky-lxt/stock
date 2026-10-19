from __future__ import annotations

from datetime import date


class BacktestEngine:
    def __init__(
        self,
        data_repo,
        universe_builder,
        factor_service,
        predictor,
        portfolio_builder,
        risk_engine,
        broker,
        metrics,
    ):
        self.data_repo = data_repo
        self.universe_builder = universe_builder
        self.factor_service = factor_service
        self.predictor = predictor
        self.portfolio_builder = portfolio_builder
        self.risk_engine = risk_engine
        self.broker = broker
        self.metrics = metrics

    def run(self, start: date, end: date) -> dict[str, object]:
        for trade_date in self.data_repo.get_trading_days(start, end):
            if self._is_rebalance_day(trade_date):
                universe = self.universe_builder.build(trade_date)
                if universe.empty:
                    self.broker.snapshot(trade_date)
                    continue

                factors = self.factor_service.load_or_calculate(trade_date, universe)
                if factors.empty:
                    self.broker.snapshot(trade_date)
                    continue

                predictions = self.predictor.predict(trade_date, factors)
                targets = self.portfolio_builder.build(trade_date, predictions)
                orders = self.broker.generate_rebalance_orders(targets, trade_date)

                # Execute sells before buys so the concentrated portfolio can rebalance cleanly.
                orders = sorted(orders, key=lambda order: 0 if order.side == "SELL" else 1)
                for order in orders:
                    account = self.broker.get_account(trade_date)
                    risk = self.risk_engine.check_order(order, account, trade_date)
                    if risk.approved and risk.adjusted_order is not None:
                        self.broker.execute_order(risk.adjusted_order, trade_date)
                    else:
                        self.broker.record_risk_event(order, risk, trade_date)

            self.broker.snapshot(trade_date)

        return self.metrics.generate(self.broker.history)

    def _is_rebalance_day(self, trade_date: date) -> bool:
        return trade_date.weekday() == 0
