"""Rutas de pagos: POST /payments, GET /payments/{id}, POST /payments/{id}/retries."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.errors import PaymentNotFound, RetryNotAllowed
from app.ports.idempotency_store import REQUEST_ORIGINAL, Attempt
from app.routes.dependencies import RequestContext, request_context, services_of
from app.schemas import PaymentDetailView, PaymentRequest, SubmittedPaymentView
from app.services.payment_service import PaymentOutcome

router = APIRouter()
Context = Annotated[RequestContext, Depends(request_context)]


def _submitted_view(outcome: PaymentOutcome) -> SubmittedPaymentView:
    attempt = outcome.attempt
    return SubmittedPaymentView(
        payment_id=attempt.payment_id, status=attempt.status, idempotency_key=attempt.idempotency_key,
        retry_of=attempt.retry_of_payment_id, request_type=outcome.request_type)


def _status_code_for(outcome: PaymentOutcome) -> int:
    return status.HTTP_202_ACCEPTED if outcome.request_type == REQUEST_ORIGINAL else status.HTTP_200_OK


def _owned_attempt(request: Request, payment_id: str, payer_id: str) -> Attempt:
    attempt = services_of(request).store.get_attempt(payment_id)
    if attempt is None or attempt.payer_id != payer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pago no encontrado")
    return attempt


@router.post("/payments", response_model=SubmittedPaymentView)
def create_payment(body: PaymentRequest, request: Request, response: Response, context: Context):
    outcome = services_of(request).payments.submit_payment(
        payer_id=context.payer_id, intent_id=body.intent_id, amount_cents=body.amount_cents,
        recipient=body.recipient, channel=body.channel, request_id=context.request_id,
        correlation_id=context.correlation_id)
    response.status_code = _status_code_for(outcome)
    return _submitted_view(outcome)


@router.get("/payments/{payment_id}", response_model=PaymentDetailView)
def get_payment(payment_id: str, request: Request, context: Context):
    attempt = _owned_attempt(request, payment_id, context.payer_id)
    retries = services_of(request).store.list_retries_of(attempt.payment_id)
    return PaymentDetailView(
        payment_id=attempt.payment_id, status=attempt.status, idempotency_key=attempt.idempotency_key,
        retry_of=attempt.retry_of_payment_id, retried_by=[retry.payment_id for retry in retries])


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
    return _submitted_view(outcome)
