"""Verificación del intento previo (decisión OQ-03): bloquea un intento nuevo mientras el previo no sea terminal."""
from __future__ import annotations

from app.errors import PreviousAttemptInProgress
from app.ports.idempotency_store import IdempotencyStorePort
from app.services.attempt_lifecycle import AttemptLifecycleService
from app.services.attempt_state import is_terminal


class PreviousAttemptGuard:
    def __init__(self, store: IdempotencyStorePort, lifecycle: AttemptLifecycleService) -> None:
        self._store = store
        self._lifecycle = lifecycle

    def ensure_none_in_progress(self, payer_id: str, amount_cents: int, recipient: str,
                                own_key: str | None = None) -> None:
        # Alcance asumido (OQ-38): misma intención de pago. Sin resultado terminal tras refrescar = en proceso
        # o incierto, incluida una consulta al proveedor que no se completa (OQ-40): el bloqueo falla seguro.
        # own_key excluye al intento de la misma clave, que una solicitud concurrente pudo reservar antes.
        for pending in self._store.list_pending_attempts(payer_id, amount_cents, recipient):
            if pending.idempotency_key == own_key:
                continue
            if not is_terminal(self._lifecycle.refresh(pending).status):
                raise PreviousAttemptInProgress(pending.payment_id)
