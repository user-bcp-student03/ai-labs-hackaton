"""Máquina de estados del intento de pago.

`creado` y `en_proceso` se persisten como PENDING: la reserva de la clave y el envío al proveedor ocurren en la
misma operación, así que no hay un estado `creado` observable. Los tres estados terminales son inmutables.
"""
from __future__ import annotations

from app.ports.idempotency_store import (
    STATUS_EXPIRED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    TERMINAL_STATUSES,
    Attempt,
)
from app.ports.payment_provider import PROVIDER_REJECTED, PROVIDER_SUCCEEDED

PROVIDER_STATUS_TO_ATTEMPT_STATUS = {PROVIDER_SUCCEEDED: STATUS_SUCCEEDED, PROVIDER_REJECTED: STATUS_FAILED}
ALLOWED_TRANSITIONS = {STATUS_PENDING: frozenset(TERMINAL_STATUSES)}
RETRYABLE_STATUSES = (STATUS_FAILED, STATUS_EXPIRED)


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def transaction_reference(attempt: Attempt) -> str:
    # Asignada desde la creación del intento (supuesto OQ-04): identifica al intento y es única por reintento.
    return attempt.payment_id
