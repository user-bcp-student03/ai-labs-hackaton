"""Aplicación FastAPI y cableado de dependencias."""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import Settings, load_settings
from app.ports.idempotency_store import IdempotencyStorePort
from app.ports.onboarding_store import OnboardingStorePort
from app.ports.payment_provider import PaymentProviderPort
from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore
from app.repositories.sqlite_store import SqliteIdempotencyStore
from app.routes import idempotency_audit, onboarding, onboarding_analytics, payments, wallet
from app.services.flow_config import FlowDefinition, load_flow_definition
from app.services.onboarding_analytics_service import OnboardingAnalyticsService
from app.services.onboarding_service import OnboardingService
from app.services.payment_service import PaymentService
from app.services.request_audit_service import RequestAuditService
from app.services.retry_service import RetryService
from app.services.wallet_access_service import WalletAccessService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _onboarding_services(settings: Settings, flow: FlowDefinition | None,
                         onboarding_store: OnboardingStorePort | None,
                         clock: Callable[[], datetime]) -> dict[str, object | None]:
    """Sin flujo configurado no se crea almacén ni archivo: las rutas de onboarding responden 503 (D-9)."""
    config_path = settings.onboarding.steps_config_path
    flow = flow or (load_flow_definition(config_path) if config_path else None)  # inválida: detiene el arranque
    if flow is None:
        return {"onboarding": None, "wallet_access": None, "onboarding_analytics": None}
    onboarding_store = onboarding_store or SqliteOnboardingStore(settings.db_path, clock=clock)
    return {
        "onboarding": OnboardingService(store=onboarding_store, flow=flow, settings=settings, clock=clock),
        "wallet_access": WalletAccessService(store=onboarding_store),
        "onboarding_analytics": OnboardingAnalyticsService(store=onboarding_store, settings=settings),
    }


def create_app(provider: PaymentProviderPort, settings: Settings | None = None,
               store: IdempotencyStorePort | None = None,
               clock: Callable[[], datetime] = _utc_now, *,
               onboarding_flow: FlowDefinition | None = None,
               onboarding_store: OnboardingStorePort | None = None) -> FastAPI:
    settings = settings or load_settings(os.environ)
    store = store or SqliteIdempotencyStore(settings.db_path, clock=clock)
    app = FastAPI(title="Wallet API - idempotencia de pagos")
    app.state.settings = settings
    app.state.services = SimpleNamespace(
        store=store,
        payments=PaymentService(store=store, provider=provider, settings=settings, clock=clock),
        retries=RetryService(store=store, provider=provider, settings=settings, clock=clock),
        audit=RequestAuditService(store=store),
        **_onboarding_services(settings, onboarding_flow, onboarding_store, clock),
    )
    app.add_exception_handler(RequestValidationError, onboarding.sanitized_validation_handler)
    app.include_router(payments.router)
    app.include_router(idempotency_audit.router)
    app.include_router(onboarding.router)
    app.include_router(wallet.router)
    app.include_router(onboarding_analytics.router)
    return app
