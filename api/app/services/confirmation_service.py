"""Apertura de la pantalla de confirmación: resumen, validación previa, verificación del intento previo e identificador de intención (OQ-01)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.config import Settings
from app.errors import AmountExceedsLimit, PreviousAttemptInProgress
from app.services.amount_rules import ensure_amount_within_limit
from app.services.analytics_service import AnalyticsService
from app.services.previous_attempt_guard import PreviousAttemptGuard

INTENT_ID_PREFIX = "intent-"

REASON_MISSING_DATA = "missing_data"
REASON_AMOUNT_EXCEEDS_LIMIT = "amount_exceeds_limit"
REASON_PREVIOUS_IN_PROGRESS = "previous_attempt_in_progress"


@dataclass(frozen=True)
class Confirmation:
    recipient: str | None
    amount_cents: int | None
    intent_id: str | None = None
    reason: str | None = None
    limit_cents: int | None = None
    previous_payment_id: str | None = None

    @property
    def can_confirm(self) -> bool:
        return self.reason is None


def new_intent_id() -> str:
    return f"{INTENT_ID_PREFIX}{uuid.uuid4().hex}"


class ConfirmationService:
    def __init__(self, settings: Settings, guard: PreviousAttemptGuard, analytics: AnalyticsService) -> None:
        self._settings = settings
        self._guard = guard
        self._analytics = analytics

    def open_confirmation(self, payer_id: str, recipient: str | None, amount_cents: int | None,
                          channel: str) -> Confirmation:
        if recipient is None or amount_cents is None:
            return Confirmation(recipient, amount_cents, reason=REASON_MISSING_DATA)
        try:
            ensure_amount_within_limit(self._settings, channel, amount_cents)
            self._guard.ensure_none_in_progress(payer_id, amount_cents, recipient)
        except AmountExceedsLimit as exceeded:
            return Confirmation(recipient, amount_cents, reason=REASON_AMOUNT_EXCEEDS_LIMIT,
                                limit_cents=exceeded.limit_cents)
        except PreviousAttemptInProgress as blocked:
            return Confirmation(recipient, amount_cents, reason=REASON_PREVIOUS_IN_PROGRESS,
                                previous_payment_id=blocked.previous_payment_id)
        intent_id = new_intent_id()
        self._analytics.record_checkout_started(payer_id, intent_id)
        return Confirmation(recipient, amount_cents, intent_id=intent_id)
