"""Feed de conciliación y auditoría: GET /idempotency/requests."""
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.routes.dependencies import RequestContext, request_context, services_of
from app.schemas import IDENTIFIER_PATTERN, RequestRecordView, RequestType

router = APIRouter()
KEY_MAX_LENGTH = 64


@router.get("/idempotency/requests", response_model=list[RequestRecordView])
def list_idempotency_requests(
    request: Request,
    context: Annotated[RequestContext, Depends(request_context)],
    idempotency_key: Annotated[str | None, Query(max_length=KEY_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)] = None,
    correlation_id: Annotated[str | None, Query(max_length=KEY_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)] = None,
    request_type: RequestType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    # Sin rol de operador definido, el feed se limita a las solicitudes del pagador autenticado.
    records = services_of(request).audit.list_requests(
        idempotency_key=idempotency_key, correlation_id=correlation_id, request_type=request_type,
        payer_id=context.payer_id, date_from=date_from, date_to=date_to)
    return [RequestRecordView.model_validate(dataclasses.asdict(record)) for record in records]
