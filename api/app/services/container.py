"""Cableado de servicios compartido por la aplicación y las pruebas."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from types import SimpleNamespace

from app.config import Settings
from app.content import Content
from app.ports.payment_provider import PaymentProviderPort
from app.ports.payment_store import PaymentStorePort
from app.services.analytics_service import AnalyticsService
from app.services.attempt_lifecycle import AttemptLifecycleService
from app.services.confirmation_service import ConfirmationService
from app.services.payment_service import PaymentService
from app.services.previous_attempt_guard import PreviousAttemptGuard
from app.services.request_audit_service import RequestAuditService
from app.services.retry_service import RetryService


def build_services(store: PaymentStorePort, provider: PaymentProviderPort, settings: Settings,
                   clock: Callable[[], datetime]) -> SimpleNamespace:
    analytics = AnalyticsService(store, settings, clock)
    lifecycle = AttemptLifecycleService(store, provider, settings, clock, analytics)
    guard = PreviousAttemptGuard(store, lifecycle)
    payments = PaymentService(store, provider, settings, clock, analytics=analytics, lifecycle=lifecycle,
                              guard=guard)
    return SimpleNamespace(
        store=store, content=Content(settings.content_overrides), analytics=analytics, lifecycle=lifecycle,
        payments=payments, retries=RetryService(store, provider, settings, clock, payments=payments),
        confirmations=ConfirmationService(settings, guard, analytics), audit=RequestAuditService(store=store))
