"""Aplicación FastAPI y cableado de dependencias."""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI

from app.config import Settings, load_settings
from app.ports.idempotency_store import IdempotencyStorePort
from app.ports.payment_provider import PaymentProviderPort
from app.repositories.sqlite_store import SqliteIdempotencyStore
from app.routes import idempotency_audit, payments
from app.services.payment_service import PaymentService
from app.services.request_audit_service import RequestAuditService
from app.services.retry_service import RetryService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(provider: PaymentProviderPort, settings: Settings | None = None,
               store: IdempotencyStorePort | None = None,
               clock: Callable[[], datetime] = _utc_now) -> FastAPI:
    settings = settings or load_settings(os.environ)
    store = store or SqliteIdempotencyStore(settings.db_path, clock=clock)
    app = FastAPI(title="Wallet API - idempotencia de pagos")
    app.state.services = SimpleNamespace(
        store=store,
        payments=PaymentService(store=store, provider=provider, settings=settings, clock=clock),
        retries=RetryService(store=store, provider=provider, settings=settings, clock=clock),
        audit=RequestAuditService(store=store),
    )
    app.include_router(payments.router)
    app.include_router(idempotency_audit.router)
    return app
