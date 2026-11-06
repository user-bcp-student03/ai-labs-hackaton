"""Modelos HTTP del onboarding. La validación de tamaños y tipos del borde se hace aquí; las reglas de los pasos
las evalúa el motor con la configuración, no estos modelos."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StrictBool, StrictStr

MAX_STEP_VALUES = 50
MAX_FIELD_NAME_LENGTH = 64
MAX_SUBMITTED_TEXT_LENGTH = 2000  # holgura sobre el máximo configurable (500) para devolver el mensaje de la regla

FieldName = Annotated[str, Field(max_length=MAX_FIELD_NAME_LENGTH)]
SubmittedValue = Annotated[StrictStr, Field(max_length=MAX_SUBMITTED_TEXT_LENGTH)] | StrictBool


class StepSubmission(BaseModel):
    values: Annotated[dict[FieldName, SubmittedValue], Field(max_length=MAX_STEP_VALUES)]


class StepStateView(BaseModel):
    id: str
    order: int
    title: str
    status: str


class OnboardingView(BaseModel):
    onboarding_id: str
    status: str
    cohort: str
    wallet_status: str
    current_step_id: str | None
    steps: list[StepStateView]
    completed_steps: int
    total_steps: int


class FieldView(BaseModel):
    """Campo publicado al cliente; no incluye patrones ni mensajes de reglas (el servidor es autoritativo)."""

    name: str
    type: str
    label: str
    hint: str | None = None
    required: bool
    max_length: int | None = None
    autocomplete: str | None = None
    input_mode: str | None = None


class StepView(BaseModel):
    id: str
    order: int
    title: str
    description: str | None = None
    fields: list[FieldView]


class FlowView(BaseModel):
    flow_id: str
    approval_status: str
    label: str | None = None
    steps: list[StepView]


class WalletView(BaseModel):
    status: str
    activated_at: datetime | None = None


class PaymentsEntryView(BaseModel):
    allowed: bool
