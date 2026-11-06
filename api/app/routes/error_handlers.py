"""Traducción de rechazos de dominio a HTTP con mensajes accionables y sin detalles internos."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.errors import AmountExceedsLimit, PreviousAttemptInProgress
from app.routes.dependencies import services_of
from app.routes.views import blocked_actions
from app.services.amount_rules import format_amount
from app.services.confirmation_service import REASON_AMOUNT_EXCEEDS_LIMIT, REASON_PREVIOUS_IN_PROGRESS

UNPROCESSABLE = 422  # HTTP_422_UNPROCESSABLE_ENTITY está deprecada en Starlette


def _amount_exceeds_limit(request: Request, exc: AmountExceedsLimit) -> JSONResponse:
    content = services_of(request).content
    detail = {"code": REASON_AMOUNT_EXCEEDS_LIMIT, "limit_cents": exc.limit_cents,
              "message": content.text("message.amount_exceeds_limit", limit=format_amount(exc.limit_cents))}
    return JSONResponse(status_code=UNPROCESSABLE, content={"detail": detail})


def _previous_in_progress(request: Request, exc: PreviousAttemptInProgress) -> JSONResponse:
    content = services_of(request).content
    detail = {"code": REASON_PREVIOUS_IN_PROGRESS, "message": content.text("message.previous_in_progress"),
              "previous_payment_id": exc.previous_payment_id,
              "actions": [item.model_dump() for item in blocked_actions(content, exc.previous_payment_id)]}
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": detail})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AmountExceedsLimit, _amount_exceeds_limit)
    app.add_exception_handler(PreviousAttemptInProgress, _previous_in_progress)
