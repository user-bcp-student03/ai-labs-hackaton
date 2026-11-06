"""Contrato de configuración de pasos de onboarding (diseño sección 6): carga, validación y definición inmutable.

El motor solo interpreta esta estructura; no conoce pasos concretos (decisión OQ-19)."""
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.errors import FlowConfigError

SUPPORTED_SCHEMA_VERSION = 1
APPROVAL_APPROVED = "approved"
APPROVAL_EXAMPLE = "example_not_approved"
APPROVAL_STATUSES = (APPROVAL_APPROVED, APPROVAL_EXAMPLE)

FIELD_TEXT = "text"
FIELD_CHECKBOX = "checkbox"
FIELD_TYPES = (FIELD_TEXT, FIELD_CHECKBOX)

RULE_MIN_LENGTH = "min_length"
RULE_MAX_LENGTH = "max_length"
RULE_PATTERN = "pattern"
RULE_KINDS = (RULE_MIN_LENGTH, RULE_MAX_LENGTH, RULE_PATTERN)

MAX_TEXT_FIELD_LENGTH = 500  # acota la entrada y mitiga ReDoS (R-4)
MAX_PATTERN_LENGTH = 200
MAX_TITLE_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 300
MAX_LABEL_LENGTH = 80
MAX_HINT_LENGTH = 200
MAX_MESSAGE_LENGTH = 200
MAX_FLOW_LABEL_LENGTH = 300

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9-]{1,40}$")
FIELD_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
HTML_TOKEN_PATTERN = re.compile(r"^[a-z0-9 -]{1,60}$")
MARKUP_CHARACTERS = ("<", ">")


@dataclass(frozen=True)
class RuleDefinition:
    kind: str
    value: int | str
    message: str


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    type: str
    label: str
    hint: str | None
    required: bool
    required_message: str | None
    autocomplete: str | None
    input_mode: str | None
    rules: tuple[RuleDefinition, ...]

    def max_length(self) -> int | None:
        return next((rule.value for rule in self.rules if rule.kind == RULE_MAX_LENGTH), None)


@dataclass(frozen=True)
class StepDefinition:
    id: str
    order: int
    title: str
    description: str | None
    fields: tuple[FieldDefinition, ...]


@dataclass(frozen=True)
class FlowDefinition:
    schema_version: int
    flow_id: str
    approval_status: str
    label: str | None
    steps: tuple[StepDefinition, ...]


def _fail(where: str, problem: str) -> FlowConfigError:
    return FlowConfigError(f"{where}: {problem}")


def _mapping(value: Any, where: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise _fail(where, "debe ser un objeto")
    return value


def _sequence(value: Any, where: str) -> Sequence:
    if not isinstance(value, list):
        raise _fail(where, "debe ser una lista")
    return value


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _text(container: Mapping, key: str, where: str, max_length: int) -> str:
    value = container.get(key)
    location = f"{where}.{key}"
    if not isinstance(value, str) or not value.strip():
        raise _fail(location, "texto obligatorio")
    if len(value) > max_length:
        raise _fail(location, f"máximo {max_length} caracteres")
    if any(character in value for character in MARKUP_CHARACTERS):
        raise _fail(location, "no admite HTML")
    return value


def _optional_text(container: Mapping, key: str, where: str, max_length: int) -> str | None:
    if container.get(key) is None:
        return None
    return _text(container, key, where, max_length)


def _optional_token(container: Mapping, key: str, where: str) -> str | None:
    value = container.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not HTML_TOKEN_PATTERN.fullmatch(value):
        raise _fail(f"{where}.{key}", "token HTML inválido")
    return value


def _identifier(container: Mapping, key: str, where: str, pattern: re.Pattern[str]) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise _fail(f"{where}.{key}", "identificador con formato inválido")
    return value


def _parse_rule(raw: Any, where: str) -> RuleDefinition:
    raw = _mapping(raw, where)
    kind = raw.get("kind")
    if kind not in RULE_KINDS:
        raise _fail(f"{where}.kind", "regla fuera del vocabulario")
    value = raw.get("value")
    if kind == RULE_PATTERN:
        _validate_pattern(value, where)
    elif not _is_integer(value) or value < 1:
        raise _fail(f"{where}.value", "debe ser un entero positivo")
    return RuleDefinition(kind=kind, value=value, message=_text(raw, "message", where, MAX_MESSAGE_LENGTH))


def _validate_pattern(value: Any, where: str) -> None:
    if not isinstance(value, str) or not value or len(value) > MAX_PATTERN_LENGTH:
        raise _fail(f"{where}.value", f"patrón de 1 a {MAX_PATTERN_LENGTH} caracteres")
    try:
        re.compile(value)
    except re.error:
        raise _fail(f"{where}.value", "patrón que no compila") from None


def _parse_rules(raw: Mapping, field_type: str, where: str) -> tuple[RuleDefinition, ...]:
    rules = tuple(_parse_rule(item, f"{where}.rules[{index}]")
                  for index, item in enumerate(_sequence(raw.get("rules", []), f"{where}.rules")))
    if field_type == FIELD_CHECKBOX:
        if rules:
            raise _fail(f"{where}.rules", "un checkbox no admite reglas")
        return rules
    max_lengths = [rule.value for rule in rules if rule.kind == RULE_MAX_LENGTH]
    if not max_lengths:
        raise _fail(f"{where}.rules", "todo campo de texto declara una regla max_length")
    if max(max_lengths) > MAX_TEXT_FIELD_LENGTH:
        raise _fail(f"{where}.rules", f"max_length no puede superar {MAX_TEXT_FIELD_LENGTH}")
    return rules


def _parse_field(raw: Any, where: str) -> FieldDefinition:
    raw = _mapping(raw, where)
    field_type = raw.get("type")
    if field_type not in FIELD_TYPES:
        raise _fail(f"{where}.type", "tipo fuera del vocabulario")
    required = raw.get("required")
    if not isinstance(required, bool):
        raise _fail(f"{where}.required", "debe ser booleano")
    return FieldDefinition(
        name=_identifier(raw, "name", where, FIELD_NAME_PATTERN),
        type=field_type,
        label=_text(raw, "label", where, MAX_LABEL_LENGTH),
        hint=_optional_text(raw, "hint", where, MAX_HINT_LENGTH),
        required=required,
        required_message=_text(raw, "required_message", where, MAX_MESSAGE_LENGTH) if required else None,
        autocomplete=_optional_token(raw, "autocomplete", where),
        input_mode=_optional_token(raw, "input_mode", where),
        rules=_parse_rules(raw, field_type, where),
    )


def _parse_step(raw: Any, where: str) -> StepDefinition:
    raw = _mapping(raw, where)
    order = raw.get("order")
    if not _is_integer(order) or order < 1:
        raise _fail(f"{where}.order", "debe ser un entero mayor o igual que 1")
    fields = tuple(_parse_field(item, f"{where}.fields[{index}]")
                   for index, item in enumerate(_sequence(raw.get("fields", []), f"{where}.fields")))
    if not fields:
        raise _fail(f"{where}.fields", "al menos un campo")
    if len({field.name for field in fields}) != len(fields):
        raise _fail(f"{where}.fields", "nombres de campo repetidos")
    return StepDefinition(
        id=_identifier(raw, "id", where, IDENTIFIER_PATTERN), order=order,
        title=_text(raw, "title", where, MAX_TITLE_LENGTH),
        description=_optional_text(raw, "description", where, MAX_DESCRIPTION_LENGTH), fields=fields)


def _parse_steps(raw: Any) -> tuple[StepDefinition, ...]:
    steps = tuple(_parse_step(item, f"steps[{index}]")
                  for index, item in enumerate(_sequence(raw, "steps")))
    if not steps:
        raise _fail("steps", "al menos un paso")
    if len({step.id for step in steps}) != len(steps):
        raise _fail("steps", "ids de paso repetidos")
    if len({step.order for step in steps}) != len(steps):
        raise _fail("steps", "órdenes de paso repetidos")
    return tuple(sorted(steps, key=lambda step: step.order))


def parse_flow_definition(raw: Mapping) -> FlowDefinition:
    raw = _mapping(raw, "flujo")
    if raw.get("schema_version") != SUPPORTED_SCHEMA_VERSION or not _is_integer(raw.get("schema_version")):
        raise _fail("schema_version", f"debe ser {SUPPORTED_SCHEMA_VERSION}")
    approval_status = raw.get("approval_status")
    if approval_status not in APPROVAL_STATUSES:
        raise _fail("approval_status", "valor fuera del vocabulario")
    label = (_optional_text(raw, "label", "flujo", MAX_FLOW_LABEL_LENGTH) if approval_status == APPROVAL_APPROVED
            else _text(raw, "label", "flujo", MAX_FLOW_LABEL_LENGTH))
    return FlowDefinition(
        schema_version=SUPPORTED_SCHEMA_VERSION, flow_id=_identifier(raw, "flow_id", "flujo", IDENTIFIER_PATTERN),
        approval_status=approval_status, label=label, steps=_parse_steps(raw.get("steps")))


def load_flow_definition(path: str) -> FlowDefinition:
    try:
        with open(path, encoding="utf-8") as source:
            raw = json.load(source)
    except (OSError, ValueError) as error:
        raise FlowConfigError(f"no se pudo leer la configuración de pasos ({type(error).__name__})") from None
    return parse_flow_definition(raw)
