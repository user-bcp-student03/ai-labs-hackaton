"""Servicio de pagos idempotentes (tareas 2.2, 2.3, 3.1, 4.1, 4.2)."""
from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.config import Settings
from app.errors import ProviderError
from app.ports.idempotency_store import (
    OUTCOME_CREATED,
    REQUEST_DUPLICATE,
    REQUEST_ORIGINAL,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    Attempt,
    IdempotencyStorePort,
    NewAttempt,
    RequestRecord,
)
from app.ports.payment_provider import (
    PROVIDER_REJECTED,
    PROVIDER_SUCCEEDED,
    PROVIDER_UNCERTAIN,
    PaymentProviderPort,
    ProviderResult,
)
from app.services.idempotency_key import attempt_window_index, derive_idempotency_key

logger = logging.getLogger(__name__)

PAYMENT_ID_PREFIX = "pay_"
PROVIDER_STATUS_TO_ATTEMPT_STATUS = {PROVIDER_SUCCEEDED: STATUS_SUCCEEDED, PROVIDER_REJECTED: STATUS_FAILED}


@dataclass(frozen=True)
class PaymentOutcome:
    attempt: Attempt
    request_type: str


def new_payment_id() -> str:
    return f"{PAYMENT_ID_PREFIX}{uuid.uuid4().hex}"


class PaymentService:
    def __init__(self, store: IdempotencyStorePort, provider: PaymentProviderPort, settings: Settings,
                 clock: Callable[[], datetime]) -> None:
        self._store = store
        self._provider = provider
        self._settings = settings
        self._clock = clock

    def submit_payment(self, payer_id: str, intent_id: str, amount_cents: int, recipient: str, channel: str,
                       request_id: str, correlation_id: str) -> PaymentOutcome:
        window_index = attempt_window_index(self._clock(), self._settings.attempt_window_seconds)
        return self.submit_in_window(payer_id, intent_id, amount_cents, recipient, channel, request_id,
                                     correlation_id, window_index)

    def submit_in_window(self, payer_id: str, intent_id: str, amount_cents: int, recipient: str, channel: str,
                         request_id: str, correlation_id: str, window_index: int,
                         retry_of_payment_id: str | None = None) -> PaymentOutcome:
        now = self._clock()
        key = derive_idempotency_key(payer_id, amount_cents, recipient, window_index, intent_id)
        reservation = self._store.reserve_attempt(NewAttempt(
            payment_id=new_payment_id(), idempotency_key=key, payer_id=payer_id, amount_cents=amount_cents,
            recipient=recipient, channel=channel, intent_id=intent_id, attempt_window_index=window_index,
            created_at=now, retry_of_payment_id=retry_of_payment_id))
        attempt = reservation.attempt
        is_original = reservation.outcome == OUTCOME_CREATED
        request_type = REQUEST_ORIGINAL if is_original else REQUEST_DUPLICATE
        self._store.append_request(RequestRecord(
            request_id=request_id, correlation_id=correlation_id, idempotency_key=key,
            payment_id=attempt.payment_id, payer_id=payer_id, request_type=request_type, requested_at=now,
            original_requested_at=attempt.created_at, retry_of_payment_id=attempt.retry_of_payment_id))
        if is_original:
            attempt = self._process_with_provider(attempt)
        else:
            self._note_if_key_past_retention(attempt, now)
        return PaymentOutcome(attempt=attempt, request_type=request_type)

    def _process_with_provider(self, attempt: Attempt) -> Attempt:
        result = self._call_provider(attempt)
        status = PROVIDER_STATUS_TO_ATTEMPT_STATUS.get(result.status, STATUS_PENDING)
        self._store.update_attempt(attempt.payment_id, status, result.provider_payment_id)
        logger.info("payment_processed payment_id=%s status=%s", attempt.payment_id, status)
        return self._store.get_attempt(attempt.payment_id)

    def _call_provider(self, attempt: Attempt) -> ProviderResult:
        try:
            return self._provider.submit(attempt.idempotency_key, self._settings.wallet_id, attempt.recipient,
                                         attempt.amount_cents, attempt.channel)
        except ProviderError:
            logger.warning("provider_error payment_id=%s", attempt.payment_id)
            return ProviderResult(provider_payment_id=None, status=PROVIDER_UNCERTAIN)

    def _note_if_key_past_retention(self, attempt: Attempt, now: datetime) -> None:
        # OQ-11 abierta: con return_original (P-4) la retención no se hace cumplir; solo se deja traza.
        retention = self._settings.retention_for(attempt.channel)
        if retention is None or (now - attempt.created_at).total_seconds() <= retention:
            return
        logger.info("key_past_retention payment_id=%s policy=%s", attempt.payment_id,
                    self._settings.expired_key_policy)
