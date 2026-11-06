"""Salida analítica de onboarding: /analytics/onboarding/*. Cerrada por defecto y protegida por token (Q-4)."""
from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from app.routes.onboarding import HTTP_UNPROCESSABLE, configured_service, http_error
from app.services.onboarding_analytics_service import OnboardingAnalyticsService

ANALYTICS_TOKEN_HEADER = "X-Analytics-Token"
ANALYTICS_DISABLED = (status.HTTP_404_NOT_FOUND, "ANALYTICS_DISABLED", "La salida analítica no está disponible.")
ANALYTICS_UNAUTHORIZED = (status.HTTP_401_UNAUTHORIZED, "ANALYTICS_TOKEN_INVALID", "Token analítico inválido.")
INVALID_MONTH = (HTTP_UNPROCESSABLE, "INVALID_MONTH", "El mes debe tener el formato YYYY-MM.")

router = APIRouter()
AnalyticsService = Annotated[OnboardingAnalyticsService, Depends(configured_service("onboarding_analytics"))]


def require_analytics_token(request: Request, service: AnalyticsService,
                            x_analytics_token: Annotated[str | None, Header()] = None) -> None:
    expected = request.app.state.settings.onboarding.analytics_token
    if not expected:
        raise http_error(ANALYTICS_DISABLED)
    # Comparación en tiempo constante; un encabezado ausente se trata como vacío.
    if not hmac.compare_digest((x_analytics_token or "").encode(), expected.encode()):
        raise http_error(ANALYTICS_UNAUTHORIZED)


AccessGranted = Depends(require_analytics_token)


@router.get("/analytics/onboarding/monthly", dependencies=[AccessGranted])
def monthly_output(month: str, service: AnalyticsService) -> dict:
    try:
        return service.monthly_output(month)
    except ValueError:
        raise http_error(INVALID_MONTH) from None


@router.get("/analytics/onboarding/duration", dependencies=[AccessGranted])
def duration_report(month: str, service: AnalyticsService) -> dict:
    try:
        return service.duration_report(month)
    except ValueError:
        raise http_error(INVALID_MONTH) from None
