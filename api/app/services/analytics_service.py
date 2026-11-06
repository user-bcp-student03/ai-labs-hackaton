"""Emisión de eventos de activación y de funnel, y reportes derivados (criterios 5 y 6 de la HU)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings
from app.ports.event_store import (
    EVENT_ABANDONED,
    EVENT_ACTIVATION,
    EVENT_CHECKOUT_STARTED,
    EVENT_FINAL_CONFIRMATION,
    EVENT_TERMINAL_RESULT,
    AnalyticsEvent,
    EventStorePort,
)
from app.ports.idempotency_store import STATUS_EXPIRED, STATUS_FAILED, STATUS_SUCCEEDED, Attempt

PERCENT = 100.0


@dataclass(frozen=True)
class FunnelReport:
    cohort: str
    started: int
    final_confirmations: int
    succeeded: int
    failed: int
    expired: int
    abandoned: int
    drop_rate_pct: float | None
    baseline_pct: float
    target_pct: float


@dataclass(frozen=True)
class ActivePayersReport:
    month: str
    cohort: str
    active_payers: int
    reference_min: int
    reference_max: int
    within_reference_range: bool


class AnalyticsService:
    def __init__(self, store: EventStorePort, settings: Settings, clock: Callable[[], datetime]) -> None:
        self._store = store
        self._settings = settings
        self._clock = clock

    def record_checkout_started(self, payer_id: str, intent_id: str) -> None:
        self._append(EVENT_CHECKOUT_STARTED, payer_id, intent_id)

    def record_final_confirmation(self, attempt: Attempt) -> None:
        self._append(EVENT_FINAL_CONFIRMATION, attempt.payer_id, attempt.intent_id, attempt.payment_id)

    def record_terminal_result(self, attempt: Attempt) -> None:
        self._append(EVENT_TERMINAL_RESULT, attempt.payer_id, attempt.intent_id, attempt.payment_id, attempt.status)
        if attempt.status == STATUS_SUCCEEDED:
            self._append(EVENT_ACTIVATION, attempt.payer_id, attempt.intent_id, attempt.payment_id)

    def record_abandoned(self, payer_id: str, intent_id: str) -> bool:
        """Solo abandona quien abrió la confirmación y no la confirmó; devuelve False si no la abrió."""
        if not self._store.has_event(EVENT_CHECKOUT_STARTED, intent_id, payer_id):
            return False
        if not self._store.has_event(EVENT_FINAL_CONFIRMATION, intent_id):
            self._append(EVENT_ABANDONED, payer_id, intent_id)
        return True

    def checkout_funnel(self, date_from: datetime | None = None, date_to: datetime | None = None,
                        baseline_pct: float | None = None, target_pct: float | None = None) -> FunnelReport:
        cohort = self._settings.cohort
        counts = self._store.count_events(cohort, date_from, date_to)
        started = counts.get((EVENT_CHECKOUT_STARTED, None), 0)
        succeeded = counts.get((EVENT_TERMINAL_RESULT, STATUS_SUCCEEDED), 0)
        return FunnelReport(
            cohort=cohort, started=started, final_confirmations=counts.get((EVENT_FINAL_CONFIRMATION, None), 0),
            succeeded=succeeded, failed=counts.get((EVENT_TERMINAL_RESULT, STATUS_FAILED), 0),
            expired=counts.get((EVENT_TERMINAL_RESULT, STATUS_EXPIRED), 0),
            abandoned=counts.get((EVENT_ABANDONED, None), 0),
            drop_rate_pct=_drop_rate_pct(started, succeeded),
            baseline_pct=self._settings.checkout_drop_baseline_pct if baseline_pct is None else baseline_pct,
            target_pct=self._settings.checkout_drop_target_pct if target_pct is None else target_pct)

    def monthly_active_payers(self, year: int, month: int, reference_min: int | None = None,
                              reference_max: int | None = None) -> ActivePayersReport:
        month_start = datetime(year, month, 1, tzinfo=timezone.utc)
        next_month = datetime(year + month // 12, month % 12 + 1, 1, tzinfo=timezone.utc)
        active = self._store.count_distinct_payers(EVENT_ACTIVATION, self._settings.cohort, month_start, next_month)
        low = self._settings.active_payers_min if reference_min is None else reference_min
        high = self._settings.active_payers_max if reference_max is None else reference_max
        return ActivePayersReport(month=f"{year:04d}-{month:02d}", cohort=self._settings.cohort,
                                  active_payers=active, reference_min=low, reference_max=high,
                                  within_reference_range=low <= active <= high)

    def _append(self, event_type: str, payer_id: str, intent_id: str, payment_id: str | None = None,
                result: str | None = None) -> None:
        self._store.append_event(AnalyticsEvent(
            event_type=event_type, intent_id=intent_id, payer_id=payer_id, cohort=self._settings.cohort,
            occurred_at=self._clock(), payment_id=payment_id, result=result))


def _drop_rate_pct(started: int, succeeded: int) -> float | None:
    # Fórmula decidida (OQ-18): iniciados que no llegan a exitoso entre iniciados.
    if started == 0:
        return None
    return round(max(started - succeeded, 0) / started * PERCENT, 2)
