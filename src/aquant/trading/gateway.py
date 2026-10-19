from __future__ import annotations

from abc import ABC, abstractmethod

from aquant.core.types import AccountSnapshot, OrderIntent, Trade


class TradingGateway(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> AccountSnapshot:
        raise NotImplementedError

    @abstractmethod
    def place_order(self, order: OrderIntent) -> str:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_trades(self) -> list[Trade]:
        raise NotImplementedError
