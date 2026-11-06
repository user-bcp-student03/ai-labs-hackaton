"""Excepciones de dominio; las rutas las traducen a HTTP sin exponer detalles internos."""


class RetryNotAllowed(Exception):
    """El intento original no está en un estado terminal fallido o expirado."""


class PaymentNotFound(Exception):
    """El intento no existe o no pertenece al pagador autenticado."""


class ProviderError(Exception):
    """El proveedor no respondió de forma utilizable; el resultado queda incierto."""
