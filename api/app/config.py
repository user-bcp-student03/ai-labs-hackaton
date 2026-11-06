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

# Onboarding (HU-ONB). Las propuestas marcadas como no aprobadas NO resuelven la pregunta abierta citada.
ENV_ONB_STEPS_CONFIG_PATH = "ONB_STEPS_CONFIG_PATH"  # vacío = onboarding deshabilitado (OQ-19)
ENV_ONB_COHORT = "ONB_COHORT"
ENV_ONB_WALLET_PENDING_STATUS = "ONB_WALLET_PENDING_STATUS"
ENV_ONB_DURATION_START_EVENT = "ONB_DURATION_START_EVENT"
ENV_ONB_DURATION_END_EVENT = "ONB_DURATION_END_EVENT"
ENV_ONB_REPORT_UTC_OFFSET_MINUTES = "ONB_REPORT_UTC_OFFSET_MINUTES"
ENV_ONB_REF_DURATION_BASELINE_MINUTES = "ONB_REF_DURATION_BASELINE_MINUTES"
ENV_ONB_REF_DURATION_TARGET_MINUTES = "ONB_REF_DURATION_TARGET_MINUTES"
ENV_ONB_REF_MAU_MIN = "ONB_REF_MAU_MIN"
ENV_ONB_REF_MAU_MAX = "ONB_REF_MAU_MAX"
ENV_ONB_REF_CAC_TARGET_CENTS = "ONB_REF_CAC_TARGET_CENTS"
ENV_ONB_ANALYTICS_TOKEN = "ONB_ANALYTICS_TOKEN"  # vacío = salida analítica cerrada

# Propuesta no aprobada (OQ-06): cohorte única asignada al iniciar.
DEFAULT_ONB_COHORT = "MVP-PE"
# Propuesta no aprobada (OQ-23): nombre del estado previo a `activo`.
DEFAULT_ONB_WALLET_PENDING_STATUS = "pendiente"
# Propuesta no aprobada (OQ-20): frontera de duración, formato `event_type[:step_id]`.
DEFAULT_ONB_DURATION_START_EVENT = "onboarding_started"
DEFAULT_ONB_DURATION_END_EVENT = "onboarding_closed"
# Supuesto S-2, no aprobado: desfase horario de Lima para los límites mensuales.
DEFAULT_ONB_REPORT_UTC_OFFSET_MINUTES = -300
# Parámetros de referencia de la épica, no resultados garantizados.
DEFAULT_ONB_REF_DURATION_BASELINE_MINUTES = 8
DEFAULT_ONB_REF_DURATION_TARGET_MINUTES = 3
DEFAULT_ONB_REF_MAU_MIN = 1000
DEFAULT_ONB_REF_MAU_MAX = 2000
DEFAULT_ONB_REF_CAC_TARGET_CENTS = 1000


def _default_retention() -> dict[str, int]:
    return {DEFAULT_CHANNEL_KEY: DEFAULT_RETENTION_SECONDS}


@dataclass(frozen=True)
class OnboardingSettings:
    steps_config_path: str = ""
    cohort: str = DEFAULT_ONB_COHORT
    wallet_pending_status: str = DEFAULT_ONB_WALLET_PENDING_STATUS
    duration_start_event: str = DEFAULT_ONB_DURATION_START_EVENT
    duration_end_event: str = DEFAULT_ONB_DURATION_END_EVENT
    report_utc_offset_minutes: int = DEFAULT_ONB_REPORT_UTC_OFFSET_MINUTES
    ref_duration_baseline_minutes: int = DEFAULT_ONB_REF_DURATION_BASELINE_MINUTES
    ref_duration_target_minutes: int = DEFAULT_ONB_REF_DURATION_TARGET_MINUTES
    ref_mau_min: int = DEFAULT_ONB_REF_MAU_MIN
    ref_mau_max: int = DEFAULT_ONB_REF_MAU_MAX
    ref_cac_target_cents: int = DEFAULT_ONB_REF_CAC_TARGET_CENTS
    analytics_token: str = field(default="", repr=False)


@dataclass(frozen=True)
class Settings:
    attempt_window_seconds: int = DEFAULT_ATTEMPT_WINDOW_SECONDS
    retention_seconds_by_channel: dict[str, int] = field(default_factory=_default_retention)
    expired_key_policy: str = POLICY_RETURN_ORIGINAL
    audit_retention_seconds: int | None = None
    wallet_mock_url: str = ""
    wallet_id: str = DEFAULT_WALLET_ID
    db_path: str = DEFAULT_DB_PATH
    onboarding: OnboardingSettings = field(default_factory=OnboardingSettings)

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


def _load_onboarding_settings(env: Mapping[str, str]) -> OnboardingSettings:
    defaults = OnboardingSettings()

    def number(name: str, default: int) -> int:
        return int(env.get(name) or default)

    return OnboardingSettings(
        steps_config_path=env.get(ENV_ONB_STEPS_CONFIG_PATH, "").strip(),
        cohort=env.get(ENV_ONB_COHORT) or defaults.cohort,
        wallet_pending_status=env.get(ENV_ONB_WALLET_PENDING_STATUS) or defaults.wallet_pending_status,
        duration_start_event=env.get(ENV_ONB_DURATION_START_EVENT) or defaults.duration_start_event,
        duration_end_event=env.get(ENV_ONB_DURATION_END_EVENT) or defaults.duration_end_event,
        report_utc_offset_minutes=number(ENV_ONB_REPORT_UTC_OFFSET_MINUTES, defaults.report_utc_offset_minutes),
        ref_duration_baseline_minutes=number(ENV_ONB_REF_DURATION_BASELINE_MINUTES,
                                             defaults.ref_duration_baseline_minutes),
        ref_duration_target_minutes=number(ENV_ONB_REF_DURATION_TARGET_MINUTES, defaults.ref_duration_target_minutes),
        ref_mau_min=number(ENV_ONB_REF_MAU_MIN, defaults.ref_mau_min),
        ref_mau_max=number(ENV_ONB_REF_MAU_MAX, defaults.ref_mau_max),
        ref_cac_target_cents=number(ENV_ONB_REF_CAC_TARGET_CENTS, defaults.ref_cac_target_cents),
        analytics_token=env.get(ENV_ONB_ANALYTICS_TOKEN, ""),
    )


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
        onboarding=_load_onboarding_settings(env),
    )
