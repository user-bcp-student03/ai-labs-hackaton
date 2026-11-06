"""Motor de validación de un paso, función pura (diseño 6.2). Las reglas y los mensajes salen de la configuración."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from app.services.flow_config import (
    FIELD_CHECKBOX,
    RULE_MAX_LENGTH,
    RULE_MIN_LENGTH,
    RULE_PATTERN,
    FieldDefinition,
    RuleDefinition,
    StepDefinition,
)

RULE_REQUIRED = "required"
RULE_UNKNOWN_FIELD = "unknown_field"
UNKNOWN_FIELD_MESSAGE = "Este campo no forma parte del paso; elimínalo."

_RULE_CHECKS: dict[str, Callable[[str, RuleDefinition], bool]] = {
    RULE_MIN_LENGTH: lambda text, rule: len(text) >= rule.value,
    RULE_MAX_LENGTH: lambda text, rule: len(text) <= rule.value,
    RULE_PATTERN: lambda text, rule: re.fullmatch(rule.value, text) is not None,
}


@dataclass(frozen=True)
class FieldError:
    field: str
    rule: str
    message: str


def _required_error(field: FieldDefinition) -> FieldError | None:
    if not field.required:
        return None
    return FieldError(field.name, RULE_REQUIRED, field.required_message)


def _checkbox_error(field: FieldDefinition, value: object) -> FieldError | None:
    return None if value is True else _required_error(field)


def _text_error(field: FieldDefinition, value: object) -> FieldError | None:
    text = value.strip() if isinstance(value, str) else ""  # un tipo inesperado cuenta como dato faltante
    if not text:
        return _required_error(field)
    failed = next((rule for rule in field.rules if not _RULE_CHECKS[rule.kind](text, rule)), None)
    return FieldError(field.name, failed.kind, failed.message) if failed else None


def _field_error(field: FieldDefinition, value: object) -> FieldError | None:
    if field.type == FIELD_CHECKBOX:
        return _checkbox_error(field, value)
    return _text_error(field, value)


def validate_step_values(step: StepDefinition, values: Mapping[str, str | bool]) -> list[FieldError]:
    errors = [error for field in step.fields if (error := _field_error(field, values.get(field.name)))]
    known = {field.name for field in step.fields}
    errors.extend(FieldError(name, RULE_UNKNOWN_FIELD, UNKNOWN_FIELD_MESSAGE) for name in values if name not in known)
    return errors
