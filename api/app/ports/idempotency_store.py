"""Puerto del almacén de idempotencia: reserva atómica de claves y registro de solicitudes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

STATUS_PENDING = "PENDING"
STATUS_SUCCEEDED = "SUCCEEDED"
STATUS_FAILED = "FAILED"
STATUS_EXPIRED = "EXPIRED"
TERMINAL_STATUSES = (STATUS_SUCCEEDED, STATUS_FAILED, STATUS_EXPIRED)

OUTCOME_CREATED = "CREATED"
OUTCOME_EXISTS = "EXISTS"

REQUEST_ORIGINAL = "original"
REQUEST_DUPLICATE = "duplicate"


@dataclass(frozen=True)
class NewAttempt:
    payment_id: str
    idempotency_key: str
    payer_id: str
    amount_cents: int
    recipient: str
    channel: str
    intent_id: str
    attempt_window_index: int
    created_at: datetime
    retry_of_payment_id: str | None = None


@dataclass(frozen=True)
class Attempt:
    payment_id: str
    idempotency_key: str
    payer_id: str
    amount_cents: int
    recipient: str
    channel: str
    intent_id: str
    attempt_window_index: int
    status: str
    provider_payment_id: str | None
    retry_of_payment_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ReserveOutcome:
    outcome: str
    attempt: Attempt


@dataclass(frozen=True)
class RequestRecord:
    request_id: str
    correlation_id: str
    idempotency_key: str
    payment_id: str
    payer_id: str
    request_type: str
    requested_at: datetime
    original_requested_at: datetime
    retry_of_payment_id: str | None = None


@dataclass(frozen=True)
class RequestFilters:
    idempotency_key: str | None = None
    correlation_id: str | None = None
    request_type: str | None = None
    payer_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class IdempotencyStorePort(Protocol):
    def reserve_attempt(self, attempt: NewAttempt) -> ReserveOutcome: ...

    def update_attempt(self, payment_id: str, status: str, provider_payment_id: str | None) -> None: ...

    def get_attempt(self, payment_id: str) -> Attempt | None: ...

    def get_attempt_by_key(self, idempotency_key: str) -> Attempt | None: ...

    def list_retries_of(self, payment_id: str) -> list[Attempt]: ...

    def count_attempts(self) -> int: ...

    def append_request(self, record: RequestRecord) -> None: ...

    def list_requests(self, filters: RequestFilters) -> list[RequestRecord]: ...
