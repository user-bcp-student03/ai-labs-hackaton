"""Reportes de analítica del flujo del pagador: caída en checkout y pagadores activos del mes."""
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.routes.dependencies import RequestContext, request_context, services_of
from app.schemas import ActivePayersView, FunnelReportView

router = APIRouter(prefix="/analytics")
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
Context = Annotated[RequestContext, Depends(request_context)]


@router.get("/checkout-funnel", response_model=FunnelReportView)
def checkout_funnel(
    request: Request,
    context: Context,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    baseline_pct: Annotated[float | None, Query(ge=0, le=100)] = None,
    target_pct: Annotated[float | None, Query(ge=0, le=100)] = None,
):
    # Sin rol de operador definido (decisión P-3), el reporte agregado exige solo identidad.
    report = services_of(request).analytics.checkout_funnel(date_from, date_to, baseline_pct, target_pct)
    return FunnelReportView.model_validate(dataclasses.asdict(report))


@router.get("/active-payers", response_model=ActivePayersView)
def active_payers(
    request: Request,
    context: Context,
    month: Annotated[str, Query(pattern=MONTH_PATTERN)],
    reference_min: Annotated[int | None, Query(ge=0)] = None,
    reference_max: Annotated[int | None, Query(ge=0)] = None,
):
    year, month_number = (int(part) for part in month.split("-"))
    report = services_of(request).analytics.monthly_active_payers(year, month_number, reference_min, reference_max)
    return ActivePayersView.model_validate(dataclasses.asdict(report))
