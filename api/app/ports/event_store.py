"""Puerto de eventos de analítica y discrepancias del flujo de pago del pagador."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

EVENT_CHECKOUT_STARTED = "checkout_started"
EVENT_FINAL_CONFIRMATION = "final_confirmation"
EVENT_TERMINAL_RESULT = "terminal_result"
EVENT_ABANDONED = "abandoned"
EVENT_ACTIVATION = "activation"

DISCREPANCY_LATE_CONFIRMATION = "late_confirmation_after_expiry"


@dataclass(frozen=True)
class AnalyticsEvent:
    event_type: str
    intent_id: str
    payer_id: str
    cohort: str
    occurred_at: datetime
    payment_id: str | None = None
    result: str | None = None


@dataclass(frozen=True)
class Discrepancy:
    payment_id: str
    kind: str
    detected_at: datetime


class EventStorePort(Protocol):
    def append_event(self, event: AnalyticsEvent) -> bool:
        """Registra el evento una sola vez por (tipo, intención); devuelve False si ya existía."""
        ...

    def has_event(self, event_type: str, intent_id: str, payer_id: str | None = None) -> bool: ...

    def count_events(self, cohort: str, date_from: datetime | None,
                     date_to: datetime | None) -> dict[tuple[str, str | None], int]:
        """Conteo por (tipo de evento, resultado) en [date_from, date_to)."""
        ...

    def count_distinct_payers(self, event_type: str, cohort: str, date_from: datetime | None,
                              date_to: datetime | None) -> int: ...

    def record_discrepancy(self, discrepancy: Discrepancy) -> bool: ...

    def list_discrepancies(self) -> list[Discrepancy]: ...
