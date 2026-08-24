"""
FastAPI application factory.

Importing this module does NOT start the server — call ``create_app()`` or
run via ``uvicorn src.frameworks.http.fastapi.app:create_app() --factory``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.frameworks.http.fastapi.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="CreateOrder Service",
        description=(
            "Clean Architecture demo — CreateOrder use case exposed via FastAPI.\n\n"
            "Layers: **Entities → Use Cases → Interface Adapters → Frameworks**."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    return app


# Uvicorn entry-point:  uvicorn src.frameworks.http.fastapi.app:app
app = create_app()
