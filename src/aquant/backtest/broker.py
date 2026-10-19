from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time

from aquant.core.types import AccountSnapshot, OrderIntent, Position, RiskResult, TargetPosition, Trade


@dataclass
class BacktestBroker:
    config: object
    data_repo: object
    cash: float
    positions: dict[str, int] = field(default_factory=dict)
    cost_price: dict[str, float] = field(default_factory=dict)
    history: list[dict[str, object]] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    risk_events: list[dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_config(cls, config, data_repo) -> "BacktestBroker":
        return cls(
            config=config,
            data_repo=data_repo,
            cash=float(config.backtest["initial_cash"]),
        )

    def get_account(self, trade_date: date | None = None) -> AccountSnapshot:
        positions = []
        market_value = 0.0
        for ts_code, quantity in self.positions.items():
            if quantity <= 0:
                continue
            last_price = (
                self.data_repo.get_price(ts_code, trade_date)
                if trade_date is not None
                else self.cost_price.get(ts_code, 0.0)
            )
            value = quantity * last_price
            market_value += value
            positions.append(
                Position(
                    ts_code=ts_code,
                    quantity=quantity,
                    available_quantity=quantity,
                    market_value=value,
                    cost_price=self.cost_price.get(ts_code, last_price),
                    last_price=last_price,
                )
            )
        return AccountSnapshot(
            account_id="BACKTEST",
            cash=self.cash,
            total_asset=self.cash + market_value,
            market_value=market_value,
            positions=positions,
        )

    def generate_rebalance_orders(
        self,
        targets: list[TargetPosition],
        trade_date: date,
    ) -> list[OrderIntent]:
        lot_size = int(self.config.backtest.get("lot_size", 100))
        account = self.get_account(trade_date)
        target_map = {target.ts_code: target.target_weight for target in targets}
        orders: list[OrderIntent] = []

        # Sell first to free cash and remove names not in the target portfolio.
        for position in account.positions:
            target_value = account.total_asset * target_map.get(position.ts_code, 0.0)
            current_value = position.market_value
            price = self.data_repo.get_price(position.ts_code, trade_date)
            diff_value = target_value - current_value
            if diff_value < -price * lot_size:
                quantity = int(abs(diff_value) // (price * lot_size)) * lot_size
                quantity = min(quantity, position.available_quantity)
                if quantity > 0:
                    orders.append(
                        OrderIntent(
                            strategy_name=self.config.strategy.name,
                            ts_code=position.ts_code,
                            side="SELL",
                            quantity=quantity,
                            limit_price=price,
                            reason="rebalance sell",
                        )
                    )

        # Buy after sells have been generated. This keeps the plan deterministic.
        for target in targets:
            price = self.data_repo.get_price(target.ts_code, trade_date)
            current_qty = self.positions.get(target.ts_code, 0)
            current_value = current_qty * price
            target_value = account.total_asset * target.target_weight
            diff_value = target_value - current_value
            if diff_value > price * lot_size:
                quantity = int(diff_value // (price * lot_size)) * lot_size
                if quantity > 0:
                    orders.append(
                        OrderIntent(
                            strategy_name=self.config.strategy.name,
                            ts_code=target.ts_code,
                            side="BUY",
                            quantity=quantity,
                            limit_price=price,
                            reason="rebalance buy",
                        )
                    )
        return orders

    def execute_order(self, order: OrderIntent, trade_date: date) -> Trade | None:
        price = order.limit_price or self.data_repo.get_price(order.ts_code, trade_date)
        if order.side == "BUY":
            gross = price * order.quantity
            fee = self._buy_fee(gross)
            if gross + fee > self.cash:
                return None
            old_qty = self.positions.get(order.ts_code, 0)
            old_cost = self.cost_price.get(order.ts_code, price)
            new_qty = old_qty + order.quantity
            self.positions[order.ts_code] = new_qty
            self.cost_price[order.ts_code] = ((old_qty * old_cost) + gross) / new_qty
            self.cash -= gross + fee
        else:
            held = self.positions.get(order.ts_code, 0)
            quantity = min(order.quantity, held)
            if quantity <= 0:
                return None
            gross = price * quantity
            fee = self._sell_fee(gross)
            self.positions[order.ts_code] = held - quantity
            self.cash += gross - fee
            if self.positions[order.ts_code] <= 0:
                self.positions.pop(order.ts_code, None)
                self.cost_price.pop(order.ts_code, None)
            order = OrderIntent(
                strategy_name=order.strategy_name,
                ts_code=order.ts_code,
                side=order.side,
                quantity=quantity,
                limit_price=order.limit_price,
                reason=order.reason,
            )

        trade = Trade(
            ts_code=order.ts_code,
            side=order.side,
            price=price,
            quantity=order.quantity,
            amount=price * order.quantity,
            trade_time=datetime.combine(trade_date, time(15, 0)),
        )
        self.trades.append(trade)
        return trade

    def record_risk_event(self, order: OrderIntent, risk: RiskResult, trade_date: date) -> None:
        self.risk_events.append(
            {
                "trade_date": trade_date,
                "ts_code": order.ts_code,
                "side": order.side,
                "quantity": order.quantity,
                "reason": risk.reason,
            }
        )

    def snapshot(self, trade_date: date) -> None:
        account = self.get_account(trade_date)
        self.history.append(
            {
                "trade_date": trade_date,
                "cash": account.cash,
                "market_value": account.market_value,
                "total_asset": account.total_asset,
                "positions": len(account.positions),
            }
        )

    def _buy_fee(self, amount: float) -> float:
        return amount * (
            self.config.backtest["commission_rate"] + self.config.backtest["transfer_fee_rate"]
        )

    def _sell_fee(self, amount: float) -> float:
        return amount * (
            self.config.backtest["commission_rate"]
            + self.config.backtest["transfer_fee_rate"]
            + self.config.backtest["stamp_tax_rate"]
        )
