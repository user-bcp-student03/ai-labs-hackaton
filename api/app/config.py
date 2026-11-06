"""Configuración por variables de entorno. Los valores por defecto de OQ-11, OQ-12 y OQ-13 son propuestas NO aprobadas."""
from __future__ import annotations

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

ENV_ATTEMPT_WINDOW = "IDEM_ATTEMPT_WINDOW_SECONDS"
ENV_RETENTION_BY_CHANNEL = "IDEM_RETENTION_SECONDS_BY_CHANNEL"
ENV_EXPIRED_KEY_POLICY = "IDEM_EXPIRED_KEY_POLICY"
ENV_AUDIT_RETENTION = "IDEM_AUDIT_RETENTION_SECONDS"  # propuesta no aprobada (OQ-13): vacío = sin purga
ENV_WALLET_MOCK_URL = "WALLET_MOCK_URL"
ENV_WALLET_ID = "WALLET_ID"
ENV_DB_PATH = "IDEM_DB_PATH"


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

    def __post_init__(self) -> None:
        if self.attempt_window_seconds <= 0:
            raise ValueError("la ventana de intento debe ser positiva")
        if self.expired_key_policy not in SUPPORTED_EXPIRED_KEY_POLICIES:
            raise ValueError("política de clave vencida no soportada")

    def retention_for(self, channel: str) -> int | None:
        by_channel = self.retention_seconds_by_channel
        return by_channel.get(channel, by_channel.get(DEFAULT_CHANNEL_KEY))


def _parse_retention(raw: str) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for pair in raw.split(","):
        channel, separator, seconds = pair.partition("=")
        if not separator or not channel.strip():
            raise ValueError("formato inválido en retención por canal")
        parsed[channel.strip()] = int(seconds)
    return parsed


def load_settings(env: Mapping[str, str]) -> Settings:
    defaults = Settings()
    retention_raw = env.get(ENV_RETENTION_BY_CHANNEL, "").strip()
    audit_raw = env.get(ENV_AUDIT_RETENTION, "").strip()
    return Settings(
        attempt_window_seconds=int(env.get(ENV_ATTEMPT_WINDOW) or defaults.attempt_window_seconds),
        retention_seconds_by_channel=_parse_retention(retention_raw) if retention_raw else _default_retention(),
        expired_key_policy=env.get(ENV_EXPIRED_KEY_POLICY) or defaults.expired_key_policy,
        audit_retention_seconds=int(audit_raw) if audit_raw else None,
        wallet_mock_url=env.get(ENV_WALLET_MOCK_URL, ""),
        wallet_id=env.get(ENV_WALLET_ID) or defaults.wallet_id,
        db_path=env.get(ENV_DB_PATH) or defaults.db_path,
    )
