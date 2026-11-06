"""Construcción de vistas del pagador: textos desde contenido configurable y acciones siguientes."""
from __future__ import annotations

from typing import TypeVar

from app.content import Content
from app.ports.idempotency_store import STATUS_SUCCEEDED, Attempt
from app.schemas import ActionView, PaymentView
from app.services.attempt_state import RETRYABLE_STATUSES, transaction_reference

ACTION_RETRY = "retry"
ACTION_BACK = "back"
ACTION_VIEW_PREVIOUS = "view_previous"

ViewT = TypeVar("ViewT", bound=PaymentView)


def action(content: Content, action_id: str, payment_id: str | None = None) -> ActionView:
    return ActionView(id=action_id, label=content.text(f"action.{action_id}"), payment_id=payment_id)


def blocked_actions(content: Content, previous_payment_id: str) -> list[ActionView]:
    return [action(content, ACTION_VIEW_PREVIOUS, previous_payment_id), action(content, ACTION_BACK)]


def attempt_actions(content: Content, attempt: Attempt) -> list[ActionView]:
    if attempt.status in RETRYABLE_STATUSES:
        return [action(content, ACTION_RETRY), action(content, ACTION_BACK)]
    return []


def payment_view(view_type: type[ViewT], attempt: Attempt, content: Content, **extra: object) -> ViewT:
    # La referencia se muestra al pagador solo cuando el pago es exitoso.
    reference = transaction_reference(attempt) if attempt.status == STATUS_SUCCEEDED else None
    return view_type(
        payment_id=attempt.payment_id, status=attempt.status, status_label=content.status_label(attempt.status),
        idempotency_key=attempt.idempotency_key, retry_of=attempt.retry_of_payment_id,
        transaction_reference=reference, actions=attempt_actions(content, attempt), **extra)
