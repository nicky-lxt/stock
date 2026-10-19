from __future__ import annotations

from aquant.core.types import AccountSnapshot, OrderIntent, Trade
from aquant.trading.gateway import TradingGateway


class QmtGateway(TradingGateway):
    """QMT/miniQMT adapter placeholder.

    This class intentionally avoids importing xtquant at module import time so the rest of the
    project remains runnable on machines without a broker client. Implement these methods inside
    the QMT runtime environment and keep the surrounding risk/order flow unchanged.
    """

    def connect(self) -> None:
        raise NotImplementedError("QMT connection requires xtquant in a broker client environment")

    def get_account(self) -> AccountSnapshot:
        raise NotImplementedError("QMT account query is not implemented in the scaffold")

    def place_order(self, order: OrderIntent) -> str:
        raise NotImplementedError("QMT order placement is not implemented in the scaffold")

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError("QMT cancellation is not implemented in the scaffold")

    def get_trades(self) -> list[Trade]:
        raise NotImplementedError("QMT trade query is not implemented in the scaffold")
