"""Input boundary: plain data handed to the use case by the controller."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderItemRequest:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CreateOrderRequest:
    customer_id: str
    items: list[OrderItemRequest]
