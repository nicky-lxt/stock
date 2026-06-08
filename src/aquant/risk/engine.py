from __future__ import annotations

from datetime import date

from aquant.core.types import AccountSnapshot, OrderIntent, RiskResult


class RiskEngine:
    def __init__(self, config, data_repo):
        self.config = config
        self.data_repo = data_repo

    def check_candidate(self, ts_code: str, trade_date: date) -> bool:
        if self.data_repo.is_st(ts_code, trade_date):
            return False
        if self.data_repo.is_suspended(ts_code, trade_date):
            return False
        if self.data_repo.is_limit_up(ts_code, trade_date):
            return False
        min_amount = self.config.strategy.filters["min_avg_amount_20d"]
        return self.data_repo.avg_amount(ts_code, trade_date, 20) >= min_amount

    def check_order(
        self,
        order: OrderIntent,
        account: AccountSnapshot,
        trade_date: date,
    ) -> RiskResult:
        if self.config.risk.kill_switch_enabled:
            return RiskResult(False, "REJECT", "Kill switch enabled")

        if self.config.risk.reduce_only and order.side == "BUY":
            return RiskResult(False, "REJECT", "Reduce-only mode rejects buys")

        if order.quantity <= 0:
            return RiskResult(False, "REJECT", "Invalid quantity")

        if order.quantity % self.config.backtest.get("lot_size", 100) != 0:
            return RiskResult(False, "REJECT", "A-share quantity must be a full lot")

        if self.data_repo.is_suspended(order.ts_code, trade_date):
            return RiskResult(False, "REJECT", "Suspended stock")

        if order.side == "BUY":
            if self.data_repo.is_st(order.ts_code, trade_date):
                return RiskResult(False, "REJECT", "ST stock blocked")
            if self.data_repo.is_limit_up(order.ts_code, trade_date):
                return RiskResult(False, "REJECT", "Cannot buy limit-up stock")
            position_value = self._position_value_after_buy(order, account, trade_date)
            max_weight = (
                self.config.risk.max_single_position_manual
                if order.manual_confirmed
                else self.config.risk.max_single_position_auto
            )
            if account.total_asset > 0 and position_value / account.total_asset > max_weight:
                return RiskResult(False, "REJECT", "Single position limit exceeded")

        if order.side == "SELL" and self.data_repo.is_limit_down(order.ts_code, trade_date):
            return RiskResult(False, "REJECT", "Cannot sell limit-down stock in V1 matcher")

        return RiskResult(True, "APPROVE", "Risk check passed", order)

    def _position_value_after_buy(
        self,
        order: OrderIntent,
        account: AccountSnapshot,
        trade_date: date,
    ) -> float:
        price = order.limit_price or self.data_repo.get_price(order.ts_code, trade_date)
        current = 0.0
        for position in account.positions:
            if position.ts_code == order.ts_code:
                current = position.market_value
                break
        return current + price * order.quantity
