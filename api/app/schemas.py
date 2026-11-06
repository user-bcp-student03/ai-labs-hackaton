"""Modelos de entrada y salida HTTP. La validación de entradas se hace aquí, en el borde."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StrictInt

MAX_AMOUNT_CENTS = 100_000_000  # tope del mock (principio 17: límites de tamaño)
MAX_INTENT_ID_LENGTH = 64
IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]+$"
CHANNEL_PATTERN = r"^[a-z0-9-]{1,32}$"
Recipient = Literal["contact-demo", "merchant-demo"]  # lista permitida
RequestType = Literal["original", "duplicate"]


class PaymentRequest(BaseModel):
    intent_id: Annotated[str, Field(min_length=1, max_length=MAX_INTENT_ID_LENGTH, pattern=IDENTIFIER_PATTERN)]
    amount_cents: Annotated[StrictInt, Field(gt=0, le=MAX_AMOUNT_CENTS)]
    recipient: Recipient
    channel: Annotated[str, Field(pattern=CHANNEL_PATTERN)]


class PaymentView(BaseModel):
    payment_id: str
    status: str
    idempotency_key: str
    retry_of: str | None = None


class SubmittedPaymentView(PaymentView):
    request_type: RequestType


class PaymentDetailView(PaymentView):
    retried_by: list[str]


class RequestRecordView(BaseModel):
    request_id: str
    correlation_id: str
    idempotency_key: str
    payment_id: str
    request_type: RequestType
    requested_at: datetime
    original_requested_at: datetime
    retry_of_payment_id: str | None = None
