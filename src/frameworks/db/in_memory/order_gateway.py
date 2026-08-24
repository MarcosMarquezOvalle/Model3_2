"""Thread-safe in-memory implementation of OrderRepository."""

from __future__ import annotations

from threading import Lock
from uuid import UUID

from src.entities.order import Order
from src.use_cases.ports import OrderRepository


class InMemoryOrderGateway(OrderRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Order] = {}
        self._lock = Lock()

    def add(self, order: Order) -> None:
        with self._lock:
            self._store[order.id] = order

    def get(self, order_id: UUID) -> Order | None:
        return self._store.get(order_id)

    def list_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._store.values() if o.customer_id == customer_id]
