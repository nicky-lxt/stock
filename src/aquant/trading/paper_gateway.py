from __future__ import annotations

from aquant.core.types import AccountSnapshot, OrderIntent, Trade
from aquant.trading.gateway import TradingGateway


class PaperGateway(TradingGateway):
    def __init__(self, account: AccountSnapshot):
        self.account = account
        self.trades: list[Trade] = []

    def connect(self) -> None:
        return None

    def get_account(self) -> AccountSnapshot:
        return self.account

    def place_order(self, order: OrderIntent) -> str:
        return f"PAPER-{order.ts_code}-{order.side}-{order.quantity}"

    def cancel_order(self, order_id: str) -> bool:
        return order_id.startswith("PAPER-")

    def get_trades(self) -> list[Trade]:
        return self.trades
