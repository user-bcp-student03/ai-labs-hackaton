"""Aplicación FastAPI y cableado de dependencias."""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import FastAPI

from app.config import Settings, load_settings
from app.ports.payment_provider import PaymentProviderPort
from app.ports.payment_store import PaymentStorePort
from app.repositories.sqlite_store import SqliteIdempotencyStore
from app.routes import analytics, idempotency_audit, payments
from app.routes.error_handlers import register_error_handlers
from app.services.container import build_services


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(provider: PaymentProviderPort, settings: Settings | None = None,
               store: PaymentStorePort | None = None,
               clock: Callable[[], datetime] = _utc_now) -> FastAPI:
    settings = settings or load_settings(os.environ)
    store = store or SqliteIdempotencyStore(settings.db_path, clock=clock)
    app = FastAPI(title="Wallet API - pagos de bajo monto e idempotencia")
    app.state.services = build_services(store, provider, settings, clock)
    app.include_router(payments.router)
    app.include_router(analytics.router)
    app.include_router(idempotency_audit.router)
    register_error_handlers(app)
    return app
