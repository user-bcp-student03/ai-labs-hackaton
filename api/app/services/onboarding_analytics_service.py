"""Salida analítica de onboarding: conteo mensual de nuevos usuarios activos y reporte de duración.

El gasto de adquisición queda siempre `unavailable` mientras OQ-22 siga abierta (tarea 6.2 bloqueada)."""
from __future__ import annotations

import re
import statistics
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.ports.onboarding_store import EventBoundary, OnboardingStorePort

MONTH_PATTERN = re.compile(r"^([1-9]\d{3})-(0[1-9]|1[0-2])$")
BOUNDARY_SEPARATOR = ":"
SECONDS_PER_MINUTE = 60
SPEND_UNAVAILABLE = "unavailable"
PENDING_DEFINITIONS = ["OQ-05", "OQ-22"]
BOUNDARY_STATUS_PROVISIONAL = "provisional_oq20"


def _parse_boundary(raw: str) -> EventBoundary:
    event_type, _, step_id = raw.partition(BOUNDARY_SEPARATOR)
    return EventBoundary(event_type=event_type, step_id=step_id)


class OnboardingAnalyticsService:
    def __init__(self, store: OnboardingStorePort, settings: Settings) -> None:
        self._store = store
        self._settings = settings.onboarding

    def monthly_output(self, month: str) -> dict:
        start, end = self._month_window(month)
        settings = self._settings
        return {
            "month": month,
            "cohort": settings.cohort,
            "new_active_users": self._store.count_closed_between(settings.cohort, start, end),
            "acquisition_spend": {"status": SPEND_UNAVAILABLE, "amount_pen_cents": None},
            "reference": {"mau_min": settings.ref_mau_min, "mau_max": settings.ref_mau_max,
                          "cac_target_pen_cents": settings.ref_cac_target_cents},
            "pending_definitions": list(PENDING_DEFINITIONS),
        }

    def duration_report(self, month: str) -> dict:
        start, end = self._month_window(month)
        settings = self._settings
        intervals = self._store.list_event_intervals(
            settings.cohort, _parse_boundary(settings.duration_start_event),
            _parse_boundary(settings.duration_end_event), start, end)
        minutes = [(ended - started).total_seconds() / SECONDS_PER_MINUTE for started, ended in intervals]
        return {
            "month": month,
            "cohort": settings.cohort,
            "finished_onboardings": len(minutes),
            "median_minutes": statistics.median(minutes) if minutes else None,
            "reference": {"baseline_minutes": settings.ref_duration_baseline_minutes,
                          "target_minutes": settings.ref_duration_target_minutes},
            "boundary": {"start": settings.duration_start_event, "end": settings.duration_end_event,
                         "status": BOUNDARY_STATUS_PROVISIONAL},
        }

    def _month_window(self, month: str) -> tuple[datetime, datetime]:
        """Límites UTC del mes calendario evaluado con el desfase horario configurado (supuesto S-2)."""
        match = MONTH_PATTERN.fullmatch(month)
        if match is None:
            raise ValueError("el mes debe tener el formato YYYY-MM")
        year, number = int(match.group(1)), int(match.group(2))
        offset = timedelta(minutes=self._settings.report_utc_offset_minutes)
        first_day = datetime(year, number, 1, tzinfo=timezone.utc)
        next_month = datetime(year + (number == 12), number % 12 + 1, 1, tzinfo=timezone.utc)
        return first_day - offset, next_month - offset
