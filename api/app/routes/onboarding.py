"""Rutas de onboarding: /onboarding/*. HTTP, esquemas e identidad; las reglas viven en el servicio."""
from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import OnboardingIncomplete, OnboardingNotFound, StepNotCurrent, StepNotFound, StepValidationFailed
from app.routes.dependencies import RequestContext, request_context, services_of
from app.schemas_onboarding import FieldView, FlowView, OnboardingView, StepSubmission, StepView
from app.services.flow_config import FlowDefinition
from app.services.onboarding_service import OnboardingService

ONBOARDING_PATH_PREFIX = "/onboarding"
HTTP_UNPROCESSABLE = 422  # la constante de starlette cambió de nombre entre versiones
MAX_ONBOARDING_ID_LENGTH = 64
MAX_STEP_ID_LENGTH = 40

NOT_CONFIGURED = (status.HTTP_503_SERVICE_UNAVAILABLE, "ONBOARDING_NOT_CONFIGURED",
                  "El onboarding no está disponible en este momento.")
INVALID_REQUEST = (HTTP_UNPROCESSABLE, "INVALID_REQUEST", "La solicitud no tiene el formato esperado.")
# Mensajes estáticos: nunca reflejan valores enviados por el cliente.
_STATIC_ERRORS: dict[type[Exception], tuple[int, str, str]] = {
    OnboardingNotFound: (status.HTTP_404_NOT_FOUND, "ONBOARDING_NOT_FOUND", "No encontramos tu onboarding."),
    StepNotFound: (status.HTTP_404_NOT_FOUND, "STEP_NOT_FOUND", "No encontramos ese paso."),
    StepNotCurrent: (status.HTTP_409_CONFLICT, "STEP_NOT_CURRENT", "Completa primero el paso actual."),
}
STEP_VALIDATION_MESSAGE = "Corrige los datos indicados para continuar."
INCOMPLETE_MESSAGE = "Completa todos los pasos antes de finalizar."

router = APIRouter()
Context = Annotated[RequestContext, Depends(request_context)]
OnboardingIdPath = Annotated[str, Path(max_length=MAX_ONBOARDING_ID_LENGTH)]
StepIdPath = Annotated[str, Path(max_length=MAX_STEP_ID_LENGTH)]


def error_detail(code: str, message: str, **extra) -> dict:
    return {"code": code, "message": message, **extra}


def http_error(spec: tuple[int, str, str], **extra) -> HTTPException:
    status_code, code, message = spec
    return HTTPException(status_code=status_code, detail=error_detail(code, message, **extra))


def configured_service(attribute: str) -> Callable:
    """Dependencia que entrega el servicio de onboarding o responde 503 si no hay flujo configurado."""
    def dependency(request: Request):
        service = getattr(services_of(request), attribute, None)
        if service is None:
            raise http_error(NOT_CONFIGURED)
        return service

    return dependency


onboarding_service = configured_service("onboarding")
Service = Annotated[OnboardingService, Depends(onboarding_service)]


def _translate(error: Exception) -> HTTPException:
    if isinstance(error, StepValidationFailed):
        errors = [dataclasses.asdict(item) for item in error.errors]
        return http_error((HTTP_UNPROCESSABLE, "STEP_VALIDATION_FAILED", STEP_VALIDATION_MESSAGE),
                          errors=errors)
    if isinstance(error, OnboardingIncomplete):
        return http_error((status.HTTP_409_CONFLICT, "ONBOARDING_INCOMPLETE", INCOMPLETE_MESSAGE),
                          pending_step_ids=error.pending_step_ids)
    return http_error(_STATIC_ERRORS[type(error)])


DOMAIN_ERRORS = (OnboardingNotFound, StepNotFound, StepNotCurrent, StepValidationFailed, OnboardingIncomplete)


def _flow_view(flow: FlowDefinition) -> FlowView:
    return FlowView(
        flow_id=flow.flow_id, approval_status=flow.approval_status, label=flow.label,
        steps=[StepView(
            id=step.id, order=step.order, title=step.title, description=step.description,
            fields=[FieldView(
                name=field.name, type=field.type, label=field.label, hint=field.hint, required=field.required,
                max_length=field.max_length(), autocomplete=field.autocomplete, input_mode=field.input_mode)
                for field in step.fields]) for step in flow.steps])


def _onboarding_view(state) -> OnboardingView:
    return OnboardingView.model_validate(dataclasses.asdict(state))


async def sanitized_validation_handler(request: Request, error: RequestValidationError):
    """En /onboarding/* el 422 de formato no devuelve el cuerpo enviado; el resto conserva el comportamiento base."""
    if not request.url.path.startswith(ONBOARDING_PATH_PREFIX):
        return await request_validation_exception_handler(request, error)
    status_code, code, message = INVALID_REQUEST
    return JSONResponse(status_code=status_code, content={"detail": error_detail(code, message)})


@router.get("/onboarding/flow", response_model=FlowView)
def get_flow(service: Service):
    # La definición no es dato personal: no exige identidad (el cliente la usa para construir el formulario).
    return _flow_view(service.flow)


@router.post("/onboarding", response_model=OnboardingView)
def start_or_resume_onboarding(service: Service, context: Context, response: Response):
    started = service.start_or_resume(context.payer_id)
    response.status_code = status.HTTP_201_CREATED if started.created else status.HTTP_200_OK
    return _onboarding_view(started.onboarding)


@router.get("/onboarding/current", response_model=OnboardingView)
def get_current_onboarding(service: Service, context: Context):
    try:
        return _onboarding_view(service.get_current(context.payer_id))
    except DOMAIN_ERRORS as error:
        raise _translate(error) from None


@router.put("/onboarding/{onboarding_id}/steps/{step_id}", response_model=OnboardingView)
def submit_step(onboarding_id: OnboardingIdPath, step_id: StepIdPath, body: StepSubmission, service: Service,
                context: Context):
    try:
        return _onboarding_view(service.submit_step(context.payer_id, onboarding_id, step_id, body.values))
    except DOMAIN_ERRORS as error:
        raise _translate(error) from None


@router.post("/onboarding/{onboarding_id}/close", response_model=OnboardingView)
def close_onboarding(onboarding_id: OnboardingIdPath, service: Service, context: Context):
    try:
        return _onboarding_view(service.close(context.payer_id, onboarding_id))
    except DOMAIN_ERRORS as error:
        raise _translate(error) from None
