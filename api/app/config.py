"""Configuración por variables de entorno. Los valores por defecto de OQ-11, OQ-12 y OQ-13 son propuestas NO aprobadas."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_CHANNEL_KEY = "default"
POLICY_RETURN_ORIGINAL = "return_original"
SUPPORTED_EXPIRED_KEY_POLICIES = (POLICY_RETURN_ORIGINAL,)

# Propuesta no aprobada (OQ-12): ventana de intento de 5 minutos.
DEFAULT_ATTEMPT_WINDOW_SECONDS = 300
# Propuesta no aprobada (OQ-11): retención de claves de 24 h por canal.
DEFAULT_RETENTION_SECONDS = 86400
DEFAULT_WALLET_ID = "wallet-demo"
DEFAULT_DB_PATH = "idempotency.sqlite3"
# Decidida (OQ-17, 2026-11-06): tiempo máximo de un intento de 120 segundos.
DEFAULT_ATTEMPT_TIMEOUT_SECONDS = 120
# Cohorte MVP Perú (OQ-06 decidida: se asigna en el onboarding); mientras no llegue por pagador se usa este valor.
DEFAULT_COHORT = "MVP_PE"
# Parámetros de la épica para comparar reportes (caída en checkout y MAU de los meses 1-3).
DEFAULT_CHECKOUT_DROP_BASELINE_PCT = 30.0
DEFAULT_CHECKOUT_DROP_TARGET_PCT = 8.0
DEFAULT_ACTIVE_PAYERS_MIN = 1000
DEFAULT_ACTIVE_PAYERS_MAX = 2000

ENV_ATTEMPT_WINDOW = "IDEM_ATTEMPT_WINDOW_SECONDS"
ENV_RETENTION_BY_CHANNEL = "IDEM_RETENTION_SECONDS_BY_CHANNEL"
ENV_EXPIRED_KEY_POLICY = "IDEM_EXPIRED_KEY_POLICY"
ENV_AUDIT_RETENTION = "IDEM_AUDIT_RETENTION_SECONDS"  # propuesta no aprobada (OQ-13): vacío = sin purga
ENV_WALLET_MOCK_URL = "WALLET_MOCK_URL"
ENV_WALLET_ID = "WALLET_ID"
ENV_DB_PATH = "IDEM_DB_PATH"
ENV_ATTEMPT_TIMEOUT = "PAY_ATTEMPT_TIMEOUT_SECONDS"
ENV_AMOUNT_LIMITS = "PAY_AMOUNT_LIMITS_CENTS_BY_CHANNEL"  # OQ-15 abierta: vacío = sin límite por canal
ENV_COHORT = "PAY_COHORT"
ENV_CONTENT_JSON = "PAY_CONTENT_JSON"


def _default_retention() -> dict[str, int]:
    return {DEFAULT_CHANNEL_KEY: DEFAULT_RETENTION_SECONDS}


@dataclass(frozen=True)
class Settings:
    attempt_window_seconds: int = DEFAULT_ATTEMPT_WINDOW_SECONDS
    retention_seconds_by_channel: dict[str, int] = field(default_factory=_default_retention)
    expired_key_policy: str = POLICY_RETURN_ORIGINAL
    audit_retention_seconds: int | None = None
    wallet_mock_url: str = ""
    wallet_id: str = DEFAULT_WALLET_ID
    db_path: str = DEFAULT_DB_PATH
    attempt_timeout_seconds: int = DEFAULT_ATTEMPT_TIMEOUT_SECONDS
    amount_limits_cents_by_channel: dict[str, int] = field(default_factory=dict)
    cohort: str = DEFAULT_COHORT
    content_overrides: dict[str, str] = field(default_factory=dict)
    checkout_drop_baseline_pct: float = DEFAULT_CHECKOUT_DROP_BASELINE_PCT
    checkout_drop_target_pct: float = DEFAULT_CHECKOUT_DROP_TARGET_PCT
    active_payers_min: int = DEFAULT_ACTIVE_PAYERS_MIN
    active_payers_max: int = DEFAULT_ACTIVE_PAYERS_MAX

    def __post_init__(self) -> None:
        if self.attempt_window_seconds <= 0:
            raise ValueError("la ventana de intento debe ser positiva")
        if self.expired_key_policy not in SUPPORTED_EXPIRED_KEY_POLICIES:
            raise ValueError("política de clave vencida no soportada")
        if self.attempt_timeout_seconds <= 0:
            raise ValueError("el tiempo máximo del intento debe ser positivo")
        if any(limit <= 0 for limit in self.amount_limits_cents_by_channel.values()):
            raise ValueError("los límites de monto deben ser positivos")

    def retention_for(self, channel: str) -> int | None:
        by_channel = self.retention_seconds_by_channel
        return by_channel.get(channel, by_channel.get(DEFAULT_CHANNEL_KEY))

    def amount_limit_for(self, channel: str) -> int | None:
        by_channel = self.amount_limits_cents_by_channel
        return by_channel.get(channel, by_channel.get(DEFAULT_CHANNEL_KEY))


def _parse_channel_ints(raw: str) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for pair in raw.split(","):
        channel, separator, number = pair.partition("=")
        if not separator or not channel.strip():
            raise ValueError("formato inválido en configuración por canal")
        parsed[channel.strip()] = int(number)
    return parsed


def _parse_content(raw: str) -> dict[str, str]:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not all(isinstance(value, str) for value in parsed.values()):
        raise ValueError("el contenido configurable debe ser un objeto de textos")
    return parsed


def load_settings(env: Mapping[str, str]) -> Settings:
    defaults = Settings()
    retention_raw = env.get(ENV_RETENTION_BY_CHANNEL, "").strip()
    audit_raw = env.get(ENV_AUDIT_RETENTION, "").strip()
    limits_raw = env.get(ENV_AMOUNT_LIMITS, "").strip()
    content_raw = env.get(ENV_CONTENT_JSON, "").strip()
    return Settings(
        attempt_window_seconds=int(env.get(ENV_ATTEMPT_WINDOW) or defaults.attempt_window_seconds),
        retention_seconds_by_channel=_parse_channel_ints(retention_raw) if retention_raw else _default_retention(),
        expired_key_policy=env.get(ENV_EXPIRED_KEY_POLICY) or defaults.expired_key_policy,
        audit_retention_seconds=int(audit_raw) if audit_raw else None,
        wallet_mock_url=env.get(ENV_WALLET_MOCK_URL, ""),
        wallet_id=env.get(ENV_WALLET_ID) or defaults.wallet_id,
        db_path=env.get(ENV_DB_PATH) or defaults.db_path,
        attempt_timeout_seconds=int(env.get(ENV_ATTEMPT_TIMEOUT) or defaults.attempt_timeout_seconds),
        amount_limits_cents_by_channel=_parse_channel_ints(limits_raw) if limits_raw else {},
        cohort=env.get(ENV_COHORT) or defaults.cohort,
        content_overrides=_parse_content(content_raw) if content_raw else {},
    )
