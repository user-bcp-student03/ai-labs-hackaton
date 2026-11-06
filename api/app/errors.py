"""Excepciones de dominio; las rutas las traducen a HTTP sin exponer detalles internos."""
from __future__ import annotations

from collections.abc import Sequence


class RetryNotAllowed(Exception):
    """El intento original no está en un estado terminal fallido o expirado."""


class PaymentNotFound(Exception):
    """El intento no existe o no pertenece al pagador autenticado."""


class ProviderError(Exception):
    """El proveedor no respondió de forma utilizable; el resultado queda incierto."""


class AmountExceedsLimit(Exception):
    """El monto supera el límite configurado para el canal."""

    def __init__(self, limit_cents: int) -> None:
        super().__init__("monto sobre el límite")
        self.limit_cents = limit_cents


class PreviousAttemptInProgress(Exception):
    """Un intento previo de la misma intención de pago sigue en proceso o incierto (decisión OQ-03)."""

    def __init__(self, previous_payment_id: str) -> None:
        super().__init__("intento previo sin resultado terminal")
        self.previous_payment_id = previous_payment_id


class FlowConfigError(Exception):
    """La configuración de pasos de onboarding no cumple el contrato; detiene el arranque."""


class OnboardingNotFound(Exception):
    """El onboarding no existe o no pertenece al usuario autenticado."""


class StepNotFound(Exception):
    """El paso no existe en la configuración del flujo."""


class StepNotCurrent(Exception):
    """El paso enviado es posterior al paso actual."""


class StepValidationFailed(Exception):
    """El paso tiene datos faltantes o inválidos; `errors` lleva un error accionable por campo."""

    def __init__(self, errors: Sequence) -> None:
        super().__init__("validación del paso fallida")
        self.errors = list(errors)


class OnboardingIncomplete(Exception):
    """Quedan pasos requeridos sin completar; `pending_step_ids` los enumera en orden."""

    def __init__(self, pending_step_ids: Sequence[str]) -> None:
        super().__init__("onboarding incompleto")
        self.pending_step_ids = list(pending_step_ids)


class WalletNotActive(Exception):
    """La wallet del usuario no está en estado `activo`."""
