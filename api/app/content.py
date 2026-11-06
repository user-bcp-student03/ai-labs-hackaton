"""Contenido visible al pagador. Etiquetas de estados terminales decididas en OQ-16; el resto de textos son propuestas no aprobadas."""
from __future__ import annotations

from collections.abc import Mapping

from app.ports.idempotency_store import STATUS_EXPIRED, STATUS_FAILED, STATUS_PENDING, STATUS_SUCCEEDED

TERMINAL_LABEL_KEYS = tuple(f"status.{status}" for status in (STATUS_SUCCEEDED, STATUS_FAILED, STATUS_EXPIRED))

DEFAULT_CONTENT = {
    f"status.{STATUS_PENDING}": "En proceso",
    f"status.{STATUS_SUCCEEDED}": "Exitoso",
    f"status.{STATUS_FAILED}": "Fallido",
    f"status.{STATUS_EXPIRED}": "Expirado",
    "action.retry": "Reintentar",
    "action.back": "Volver",
    "action.view_previous": "Ver estado del pago anterior",
    "message.amount_exceeds_limit": "El monto excede el límite permitido de {limit} para este canal.",
    "message.missing_data": "Faltan datos del destino o del monto: no se puede confirmar el pago.",
    "message.previous_in_progress": (
        "Tu pago anterior sigue en proceso o pendiente de confirmación. Espera su resultado antes de intentar de nuevo."
    ),
}


class Content:
    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        unknown = set(overrides or {}) - set(DEFAULT_CONTENT)
        if unknown:
            raise ValueError("claves de contenido desconocidas")
        self._texts = {**DEFAULT_CONTENT, **(overrides or {})}
        if len({self._texts[key] for key in TERMINAL_LABEL_KEYS}) != len(TERMINAL_LABEL_KEYS):
            raise ValueError("las etiquetas de los estados terminales deben ser distintas")

    def text(self, key: str, **params: str) -> str:
        return self._texts[key].format(**params)

    def status_label(self, status: str) -> str:
        return self._texts[f"status.{status}"]
