"""Puerto único del almacén de onboarding (decisión D-2): sesión, progreso, wallet y eventos en un almacén
transaccional, porque el cierre debe ser atómico y los eventos se deduplican en la misma transacción."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"

WALLET_STATUS_ACTIVE = "activo"  # fijo por la spec; el estado previo viene de configuración (OQ-23)

EVENT_STARTED = "onboarding_started"
EVENT_STEP_COMPLETED = "onboarding_step_completed"
EVENT_CLOSED = "onboarding_closed"
EVENT_TYPES = (EVENT_STARTED, EVENT_STEP_COMPLETED, EVENT_CLOSED)
NO_STEP = ""  # step_id de los eventos que no pertenecen a un paso


@dataclass(frozen=True)
class OnboardingSession:
    onboarding_id: str
    user_id: str
    cohort: str
    status: str
    started_at: datetime
    updated_at: datetime
    closed_at: datetime | None


@dataclass(frozen=True)
class Wallet:
    user_id: str
    status: str
    created_at: datetime
    activated_at: datetime | None


@dataclass(frozen=True)
class StartOutcome:
    session: OnboardingSession
    created: bool


@dataclass(frozen=True)
class CloseOutcome:
    session: OnboardingSession
    closed_now: bool


@dataclass(frozen=True)
class EventBoundary:
    """Extremo de una duración: tipo de evento y, si aplica, el paso (formato `event_type[:step_id]`)."""

    event_type: str
    step_id: str = NO_STEP


class OnboardingStorePort(Protocol):
    def start_onboarding(self, onboarding_id: str, user_id: str, cohort: str,
                         wallet_pending_status: str) -> StartOutcome: ...

    def get_session(self, onboarding_id: str) -> OnboardingSession | None: ...

    def get_session_by_user(self, user_id: str) -> OnboardingSession | None: ...

    def get_wallet(self, user_id: str) -> Wallet | None: ...

    def list_completed_step_ids(self, onboarding_id: str) -> list[str]: ...

    def record_step_completed(self, onboarding_id: str, step_id: str) -> bool: ...

    def close_onboarding(self, onboarding_id: str) -> CloseOutcome: ...

    def count_closed_between(self, cohort: str, start: datetime, end: datetime) -> int: ...

    def list_event_intervals(self, cohort: str, start: EventBoundary, end: EventBoundary,
                             end_from: datetime, end_to: datetime) -> list[tuple[datetime, datetime]]: ...
