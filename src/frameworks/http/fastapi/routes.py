"""
FastAPI router — CreateOrder endpoint.

Wiring path (outermost → innermost):
  HTTP request
    → FastAPI router (this file)
      → CreateOrderController   [Layer 3]
        → CreateOrderInteractor [Layer 2]
          → UnitOfWork / OrderRepository [Layer 4 impl]
          → NotificationGateway          [Layer 4 impl]
        → JsonPresenter         [Layer 3]
    ← JsonViewModel
  HTTP response
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.frameworks.http.fastapi.schemas import (
    CreateOrderRequestSchema,
    CreateOrderResponseSchema,
    ErrorResponseSchema,
)
from src.frameworks.http.fastapi.dependencies import get_controller
from src.interface_adapters.controllers.create_order_controller import (
    CreateOrderController,
    ControllerValidationError,
)
from src.interface_adapters.presenters.json_presenter import JsonPresenter

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateOrderResponseSchema,
    responses={
        422: {"model": ErrorResponseSchema, "description": "Validation / domain error"},
        500: {"model": ErrorResponseSchema, "description": "Unexpected server error"},
    },
    summary="Create a new order",
)
def create_order(
    body: CreateOrderRequestSchema,
    controller: CreateOrderController = Depends(get_controller),
) -> CreateOrderResponseSchema:
    """
    Create a new order for a customer.

    - **customer_id**: unique identifier of the customer placing the order
    - **items**: one or more order lines (product_id, quantity, unit_price)
    """
    raw = body.model_dump(mode="json")

    try:
        controller.handle(raw)
    except ControllerValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # The presenter was populated by the interactor inside controller.handle()
    # We access it through the controller's internal interactor presenter.
    vm = controller.presenter.view  # type: ignore[attr-defined]

    if not vm.success:
        code = vm.status_code if vm.status_code in (422, 500) else 500
        raise HTTPException(status_code=code, detail=vm.error)

    return CreateOrderResponseSchema(**vm.data)
