"""
HTTP request / response schemas for FastAPI.

These are pure HTTP-layer DTOs. They are intentionally separate from the
use-case request/response models so that changes in the API contract (field
names, validation messages, HTTP shape) never bleed into the use case.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OrderItemSchema(BaseModel):
    product_id: str = Field(..., min_length=1, examples=["sku-001"])
    quantity: int = Field(..., gt=0, examples=[2])
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, examples=["19.99"])


class CreateOrderRequestSchema(BaseModel):
    customer_id: str = Field(..., min_length=1, examples=["cust-abc"])
    items: list[OrderItemSchema] = Field(..., min_length=1)

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("items must not be empty")
        return v


class OrderItemResponseSchema(BaseModel):
    product_id: str
    quantity: int
    unit_price: str  # serialised as string to avoid float precision loss


class CreateOrderResponseSchema(BaseModel):
    order_id: UUID
    customer_id: str
    status: str
    total: str  # serialised as string
    item_count: int


class ErrorResponseSchema(BaseModel):
    detail: str
