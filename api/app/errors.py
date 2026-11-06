"""Excepciones de dominio; las rutas las traducen a HTTP sin exponer detalles internos."""


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
