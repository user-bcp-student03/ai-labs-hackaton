"""Puerto combinado del almacén de pagos: idempotencia, auditoría, eventos y discrepancias."""
from __future__ import annotations

from typing import Protocol

from app.ports.event_store import EventStorePort
from app.ports.idempotency_store import IdempotencyStorePort


class PaymentStorePort(IdempotencyStorePort, EventStorePort, Protocol):
    pass
