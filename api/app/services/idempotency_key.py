"""Derivación de la clave de idempotencia (tarea 2.1). Funciones puras."""
from __future__ import annotations

import hashlib
from datetime import datetime

COMPONENT_SEPARATOR = "|"


def attempt_window_index(now: datetime, window_seconds: int) -> int:
    """Índice de bucket fijo (decisión P-2; riesgo R-1 aceptado)."""
    return int(now.timestamp() // window_seconds)


def derive_idempotency_key(payer_id: str, amount_cents: int, recipient: str,
                           attempt_window_index: int, intent_id: str) -> str:
    components = (payer_id, str(amount_cents), recipient, str(attempt_window_index), intent_id)
    canonical = COMPONENT_SEPARATOR.join(f"{len(part)}:{part}" for part in components)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
