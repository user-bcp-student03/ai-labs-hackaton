"""Rutas de pagos del pagador: confirmación, envío, consulta, historial y reintento."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status

from app.errors import PaymentNotFound, RetryNotAllowed
from app.ports.idempotency_store import REQUEST_ORIGINAL, Attempt
from app.routes.dependencies import RequestContext, request_context, services_of
from app.routes.views import ACTION_BACK, action, blocked_actions, payment_view
from app.schemas import (
    IDENTIFIER_PATTERN,
    MAX_INTENT_ID_LENGTH,
    ConfirmationRequest,
    ConfirmationView,
    HistoryItemView,
    PaymentDetailView,
    PaymentRequest,
    SubmittedPaymentView,
)
from app.services.amount_rules import format_amount
from app.services.confirmation_service import (
    REASON_AMOUNT_EXCEEDS_LIMIT,
    REASON_MISSING_DATA,
    REASON_PREVIOUS_IN_PROGRESS,
    Confirmation,
)
from app.services.payment_service import PaymentOutcome

router = APIRouter()
Context = Annotated[RequestContext, Depends(request_context)]
IntentId = Annotated[str, Path(min_length=1, max_length=MAX_INTENT_ID_LENGTH, pattern=IDENTIFIER_PATTERN)]

REJECTION_MESSAGE_KEYS = {
    REASON_MISSING_DATA: "message.missing_data",
    REASON_AMOUNT_EXCEEDS_LIMIT: "message.amount_exceeds_limit",
    REASON_PREVIOUS_IN_PROGRESS: "message.previous_in_progress",
}


def _submitted_view(request: Request, outcome: PaymentOutcome) -> SubmittedPaymentView:
    return payment_view(SubmittedPaymentView, outcome.attempt, services_of(request).content,
                        request_type=outcome.request_type)


def _status_code_for(outcome: PaymentOutcome) -> int:
    return status.HTTP_202_ACCEPTED if outcome.request_type == REQUEST_ORIGINAL else status.HTTP_200_OK


def _owned_attempt(request: Request, payment_id: str, payer_id: str) -> Attempt:
    attempt = services_of(request).store.get_attempt(payment_id)
    if attempt is None or attempt.payer_id != payer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pago no encontrado")
    return attempt


def _confirmation_view(request: Request, confirmation: Confirmation) -> ConfirmationView:
    content = services_of(request).content
    if confirmation.can_confirm:
        return ConfirmationView(
            can_confirm=True, intent_id=confirmation.intent_id, recipient=confirmation.recipient,
            amount_cents=confirmation.amount_cents)
    params = {}
    if confirmation.limit_cents is not None:
        params["limit"] = format_amount(confirmation.limit_cents)
    actions = [action(content, ACTION_BACK)]
    if confirmation.previous_payment_id is not None:
        actions = blocked_actions(content, confirmation.previous_payment_id)
    return ConfirmationView(
        can_confirm=False, recipient=confirmation.recipient, amount_cents=confirmation.amount_cents,
        reason=confirmation.reason, message=content.text(REJECTION_MESSAGE_KEYS[confirmation.reason], **params),
        limit_cents=confirmation.limit_cents, actions=actions)


@router.post("/payments/confirmations", response_model=ConfirmationView)
def open_confirmation(body: ConfirmationRequest, request: Request, context: Context):
    confirmation = services_of(request).confirmations.open_confirmation(
        payer_id=context.payer_id, recipient=body.recipient, amount_cents=body.amount_cents, channel=body.channel)
    return _confirmation_view(request, confirmation)


@router.post("/payments/confirmations/{intent_id}/abandon", status_code=status.HTTP_204_NO_CONTENT)
def abandon_confirmation(intent_id: IntentId, request: Request, context: Context):
    if not services_of(request).analytics.record_abandoned(context.payer_id, intent_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="confirmación no encontrada")


@router.post("/payments", response_model=SubmittedPaymentView)
def create_payment(body: PaymentRequest, request: Request, response: Response, context: Context):
    outcome = services_of(request).payments.submit_payment(
        payer_id=context.payer_id, intent_id=body.intent_id, amount_cents=body.amount_cents,
        recipient=body.recipient, channel=body.channel, request_id=context.request_id,
        correlation_id=context.correlation_id)
    response.status_code = _status_code_for(outcome)
    return _submitted_view(request, outcome)


@router.get("/payments", response_model=list[HistoryItemView])
def list_payment_history(request: Request, context: Context):
    services = services_of(request)
    items = []
    for stored in services.store.list_attempts_by_payer(context.payer_id):
        attempt = services.lifecycle.refresh(stored)
        items.append(payment_view(HistoryItemView, attempt, services.content, amount_cents=attempt.amount_cents,
                                  recipient=attempt.recipient, created_at=attempt.created_at))
    return items


@router.get("/payments/{payment_id}", response_model=PaymentDetailView)
def get_payment(payment_id: str, request: Request, context: Context):
    services = services_of(request)
    attempt = services.lifecycle.refresh(_owned_attempt(request, payment_id, context.payer_id))
    retries = services.store.list_retries_of(attempt.payment_id)
    return payment_view(PaymentDetailView, attempt, services.content,
                        retried_by=[retry.payment_id for retry in retries])


@router.post("/payments/{payment_id}/retries", response_model=SubmittedPaymentView)
def retry_payment(payment_id: str, request: Request, response: Response, context: Context):
    try:
        outcome = services_of(request).retries.create_linked_retry(
            payment_id=payment_id, payer_id=context.payer_id, request_id=context.request_id,
            correlation_id=context.correlation_id)
    except PaymentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pago no encontrado") from None
    except RetryNotAllowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="el intento no admite reintento") from None
    response.status_code = _status_code_for(outcome)
    return _submitted_view(request, outcome)
