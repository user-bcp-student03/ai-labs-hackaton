"""Ciclo de vida del intento: resultado terminal único, transiciones asíncronas del proveedor y expiración."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from app.config import Settings
from app.errors import ProviderError
from app.ports.event_store import DISCREPANCY_LATE_CONFIRMATION, Discrepancy
from app.ports.idempotency_store import STATUS_EXPIRED, STATUS_SUCCEEDED, Attempt
from app.ports.payment_provider import PaymentProviderPort
from app.ports.payment_store import PaymentStorePort
from app.services.analytics_service import AnalyticsService
from app.services.attempt_state import PROVIDER_STATUS_TO_ATTEMPT_STATUS, can_transition, is_terminal

logger = logging.getLogger(__name__)


class AttemptLifecycleService:
    def __init__(self, store: PaymentStorePort, provider: PaymentProviderPort, settings: Settings,
                 clock: Callable[[], datetime], analytics: AnalyticsService) -> None:
        self._store = store
        self._provider = provider
        self._settings = settings
        self._clock = clock
        self._analytics = analytics

    def record_result(self, payment_id: str, status: str, provider_payment_id: str | None) -> Attempt:
        """Aplica el estado solo si el intento no es terminal; el evento terminal se emite una sola vez."""
        applied = self._store.update_attempt(payment_id, status, provider_payment_id)
        attempt = self._store.get_attempt(payment_id)
        if applied and is_terminal(status):
            self._analytics.record_terminal_result(attempt)
        return attempt

    def apply_provider_signal(self, payment_id: str, provider_status: str) -> Attempt | None:
        attempt = self._store.get_attempt(payment_id)
        target = PROVIDER_STATUS_TO_ATTEMPT_STATUS.get(provider_status)
        if attempt is None or target is None:
            return attempt
        if can_transition(attempt.status, target):
            return self.record_result(payment_id, target, None)
        if attempt.status == STATUS_EXPIRED and target == STATUS_SUCCEEDED:
            self._register_late_confirmation(attempt)
        logger.info("terminal_signal_ignored payment_id=%s status=%s", payment_id, attempt.status)
        return attempt

    def refresh(self, attempt: Attempt) -> Attempt:
        """Consulta al proveedor y expira por tiempo máximo; una consulta que falla deja el intento sin cambios."""
        if is_terminal(attempt.status):
            return attempt
        attempt = self._resolve_with_provider(attempt)
        if is_terminal(attempt.status) or not self._timed_out(attempt):
            return attempt
        return self.record_result(attempt.payment_id, STATUS_EXPIRED, None)

    def _resolve_with_provider(self, attempt: Attempt) -> Attempt:
        if attempt.provider_payment_id is None:
            return attempt
        try:
            result = self._provider.resolve(attempt.provider_payment_id)
        except ProviderError:
            logger.warning("provider_resolve_failed payment_id=%s", attempt.payment_id)
            return attempt
        target = PROVIDER_STATUS_TO_ATTEMPT_STATUS.get(result.status)
        return attempt if target is None else self.record_result(attempt.payment_id, target, None)

    def _timed_out(self, attempt: Attempt) -> bool:
        elapsed = (self._clock() - attempt.created_at).total_seconds()
        return elapsed >= self._settings.attempt_timeout_seconds

    def _register_late_confirmation(self, attempt: Attempt) -> None:
        # OQ-10 abierta: se conserva el resultado terminal y solo se deja la discrepancia para operaciones.
        self._store.record_discrepancy(Discrepancy(
            payment_id=attempt.payment_id, kind=DISCREPANCY_LATE_CONFIRMATION, detected_at=self._clock()))
