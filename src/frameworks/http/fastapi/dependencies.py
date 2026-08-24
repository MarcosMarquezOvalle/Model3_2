"""
FastAPI dependency injection.

Provides one factory per dependency.  Each ``Depends(...)`` call gets a fresh
presenter+controller per request so there is no shared mutable state across
concurrent requests.

The UnitOfWork is also per-request; in a real service you would configure it
from environment variables or an app-level settings object.
"""
from __future__ import annotations

import os

from fastapi import Depends

from src.frameworks.db.in_memory.unit_of_work import InMemoryUnitOfWork
from src.frameworks.db.sqlalchemy.unit_of_work import build_sqlite_uow, SqlAlchemyUnitOfWork
from src.frameworks.notifications.http_simulator import HttpNotificationSimulatorGateway
from src.interface_adapters.controllers.create_order_controller import CreateOrderController
from src.interface_adapters.presenters.json_presenter import JsonPresenter
from src.use_cases.create_order.interactor import CreateOrderInteractor
from src.use_cases.ports import UnitOfWork, NotificationGateway

# ---------------------------------------------------------------------------
# Singletons (created once at startup, shared across requests)
# ---------------------------------------------------------------------------

_DB_URL: str = os.getenv("DATABASE_URL", "")

def _build_uow() -> UnitOfWork:
    if _DB_URL:
        return build_sqlite_uow(_DB_URL)   # swap for postgres URL in prod
    return InMemoryUnitOfWork()

_UOW: UnitOfWork = _build_uow()

_NOTIFIER: NotificationGateway = HttpNotificationSimulatorGateway(
    endpoint=os.getenv(
        "NOTIFICATION_WEBHOOK_URL",
        "https://notifications.example.com/webhooks/orders",
    )
)


# ---------------------------------------------------------------------------
# Per-request factories
# ---------------------------------------------------------------------------

def get_presenter() -> JsonPresenter:
    """Fresh presenter per request — holds per-request view state."""
    return JsonPresenter()


def get_interactor(
    presenter: JsonPresenter = Depends(get_presenter),
) -> CreateOrderInteractor:
    return CreateOrderInteractor(
        uow=_UOW,
        presenter=presenter,
        notifier=_NOTIFIER,
    )


def get_controller(
    interactor: CreateOrderInteractor = Depends(get_interactor),
) -> CreateOrderController:
    ctrl = CreateOrderController(interactor)
    # Expose the presenter on the controller so the route can read the view.
    ctrl.presenter = interactor._presenter  # type: ignore[attr-defined]
    return ctrl
