"""Consulta de auditoría y feed de conciliación (tareas 3.2, 5.1, 5.2). Sin día de reporte (OQ-14)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.ports.idempotency_store import IdempotencyStorePort, RequestFilters, RequestRecord


@dataclass(frozen=True)
class Totals:
    transactions: int


class RequestAuditService:
    def __init__(self, store: IdempotencyStorePort) -> None:
        self._store = store

    def list_requests(self, idempotency_key: str | None = None, correlation_id: str | None = None,
                      request_type: str | None = None, payer_id: str | None = None,
                      date_from: datetime | None = None, date_to: datetime | None = None) -> list[RequestRecord]:
        return self._store.list_requests(RequestFilters(
            idempotency_key=idempotency_key, correlation_id=correlation_id, request_type=request_type,
            payer_id=payer_id, date_from=date_from, date_to=date_to))

    def totals(self) -> Totals:
        # Las solicitudes duplicadas no son transacciones: se cuentan solo los intentos.
        return Totals(transactions=self._store.count_attempts())
