"""Servicio de onboarding: estado de pasos, validación bloqueante, progreso y cierre. Las reglas vienen de la
configuración (FlowDefinition); el servicio no conoce pasos concretos. Sin acceso a HTTP ni a SQL."""
from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime

from app.config import Settings
from app.errors import OnboardingIncomplete, OnboardingNotFound, StepNotCurrent, StepNotFound, StepValidationFailed
from app.ports.onboarding_store import STATUS_COMPLETED, OnboardingSession, OnboardingStorePort
from app.services.flow_config import FlowDefinition, StepDefinition
from app.services.step_engine import validate_step_values

ONBOARDING_ID_PREFIX = "ob_"
STEP_COMPLETED = "completed"
STEP_CURRENT = "current"
STEP_PENDING = "pending"


@dataclass(frozen=True)
class StepState:
    id: str
    order: int
    title: str
    status: str


@dataclass(frozen=True)
class OnboardingState:
    onboarding_id: str
    status: str
    cohort: str
    wallet_status: str
    current_step_id: str | None
    steps: tuple[StepState, ...]
    completed_steps: int
    total_steps: int


@dataclass(frozen=True)
class StartedOnboarding:
    created: bool
    onboarding: OnboardingState


def new_onboarding_id() -> str:
    return f"{ONBOARDING_ID_PREFIX}{uuid.uuid4().hex}"


class OnboardingService:
    def __init__(self, store: OnboardingStorePort, flow: FlowDefinition, settings: Settings,
                 clock: Callable[[], datetime] | None = None) -> None:
        # `clock` se acepta por simetría con los demás servicios: el almacén es quien sella las marcas de tiempo.
        self._store = store
        self._flow = flow
        self._settings = settings.onboarding
        self._steps_by_id = {step.id: step for step in flow.steps}

    @property
    def flow(self) -> FlowDefinition:
        return self._flow

    def start_or_resume(self, user_id: str) -> StartedOnboarding:
        outcome = self._store.start_onboarding(
            onboarding_id=new_onboarding_id(), user_id=user_id, cohort=self._settings.cohort,
            wallet_pending_status=self._settings.wallet_pending_status)
        return StartedOnboarding(created=outcome.created, onboarding=self._state_of(outcome.session))

    def get_current(self, user_id: str) -> OnboardingState:
        session = self._store.get_session_by_user(user_id)
        if session is None:
            raise OnboardingNotFound
        return self._state_of(session)

    def submit_step(self, user_id: str, onboarding_id: str, step_id: str,
                    values: Mapping[str, str | bool]) -> OnboardingState:
        session = self._owned_session(user_id, onboarding_id)
        step = self._step(step_id)
        completed = self._store.list_completed_step_ids(session.onboarding_id)
        if step.id in completed:
            return self._state_of(session, completed)  # reenvío idempotente: sin validar ni emitir eventos (Q-7)
        if step.id != self._current_step_id(completed):
            raise StepNotCurrent
        errors = validate_step_values(step, values)
        if errors:
            raise StepValidationFailed(errors)
        self._store.record_step_completed(session.onboarding_id, step.id)
        return self._state_of(session)

    def close(self, user_id: str, onboarding_id: str) -> OnboardingState:
        session = self._owned_session(user_id, onboarding_id)
        if session.status != STATUS_COMPLETED:
            self._require_all_steps_completed(session)
            session = self._store.close_onboarding(session.onboarding_id).session
        return self._state_of(session)

    def _owned_session(self, user_id: str, onboarding_id: str) -> OnboardingSession:
        session = self._store.get_session(onboarding_id)
        if session is None or session.user_id != user_id:
            raise OnboardingNotFound  # ajeno e inexistente son indistinguibles (sin enumeración)
        return session

    def _step(self, step_id: str) -> StepDefinition:
        step = self._steps_by_id.get(step_id)
        if step is None:
            raise StepNotFound
        return step

    def _current_step_id(self, completed: list[str]) -> str | None:
        return next((step.id for step in self._flow.steps if step.id not in completed), None)

    def _require_all_steps_completed(self, session: OnboardingSession) -> None:
        completed = self._store.list_completed_step_ids(session.onboarding_id)
        pending = [step.id for step in self._flow.steps if step.id not in completed]
        if pending:
            raise OnboardingIncomplete(pending)

    def _state_of(self, session: OnboardingSession, completed: list[str] | None = None) -> OnboardingState:
        completed = self._store.list_completed_step_ids(session.onboarding_id) if completed is None else completed
        current = self._current_step_id(completed)
        wallet = self._store.get_wallet(session.user_id)
        steps = tuple(self._step_state(step, completed, current) for step in self._flow.steps)
        return OnboardingState(
            onboarding_id=session.onboarding_id, status=session.status, cohort=session.cohort,
            wallet_status=wallet.status if wallet else self._settings.wallet_pending_status,
            current_step_id=current, steps=steps, completed_steps=len(completed),
            total_steps=len(self._flow.steps))

    @staticmethod
    def _step_state(step: StepDefinition, completed: list[str], current: str | None) -> StepState:
        if step.id in completed:
            status = STEP_COMPLETED
        else:
            status = STEP_CURRENT if step.id == current else STEP_PENDING
        return StepState(id=step.id, order=step.order, title=step.title, status=status)
