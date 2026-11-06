"""Reintento vinculado tras fallo o expiración (tarea 2.5, decisión OQ-02, P-5)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from app.config import Settings
from app.errors import PaymentNotFound, RetryNotAllowed
from app.ports.payment_provider import PaymentProviderPort
from app.ports.payment_store import PaymentStorePort
from app.services.attempt_state import RETRYABLE_STATUSES
from app.services.payment_service import PaymentOutcome, PaymentService

RETRY_INTENT_PREFIX = "retry-of:"


class RetryService:
    def __init__(self, store: PaymentStorePort, provider: PaymentProviderPort, settings: Settings,
                 clock: Callable[[], datetime], payments: PaymentService | None = None) -> None:
        self._store = store
        self._payments = payments or PaymentService(store=store, provider=provider, settings=settings, clock=clock)

    def create_linked_retry(self, payment_id: str, payer_id: str, request_id: str,
                            correlation_id: str) -> PaymentOutcome:
        original = self._store.get_attempt(payment_id)
        if original is None or original.payer_id != payer_id:
            raise PaymentNotFound
        if original.status not in RETRYABLE_STATUSES:
            raise RetryNotAllowed
        # Intención derivada del original: un doble clic sobre el mismo reintento no cobra dos veces.
        return self._payments.submit_in_window(
            payer_id=payer_id, intent_id=f"{RETRY_INTENT_PREFIX}{original.payment_id}",
            amount_cents=original.amount_cents, recipient=original.recipient, channel=original.channel,
            request_id=request_id, correlation_id=correlation_id,
            window_index=original.attempt_window_index, retry_of_payment_id=original.payment_id)
