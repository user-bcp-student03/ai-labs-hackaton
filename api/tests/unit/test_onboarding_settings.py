"""Configuración de onboarding (diseño sección 10; tareas 1.7, 5.3, 6.1). Valores provisionales, no codificados."""
import dataclasses

import pytest


def test_valores_provisionales_por_defecto():
    # Sección 10: OQ-06, OQ-19, OQ-20, OQ-23, S-2 y parámetros de la épica
    from app.config import load_settings

    onb = load_settings({}).onboarding
    assert onb.steps_config_path == ""  # vacío = onboarding deshabilitado
    assert onb.cohort == "MVP-PE"
    assert onb.wallet_pending_status == "pendiente"
    assert onb.duration_start_event == "onboarding_started"
    assert onb.duration_end_event == "onboarding_closed"
    assert onb.report_utc_offset_minutes == -300
    assert (onb.ref_duration_baseline_minutes, onb.ref_duration_target_minutes) == (8, 3)
    assert (onb.ref_mau_min, onb.ref_mau_max) == (1000, 2000)
    assert onb.ref_cac_target_cents == 1000
    assert onb.analytics_token == ""  # vacío = salida analítica deshabilitada (cerrada por defecto)


def test_valores_leidos_de_entorno():
    # Sección 10: ningún valor se fija en servicios; config.py los lee
    from app.config import load_settings

    onb = load_settings({
        "ONB_STEPS_CONFIG_PATH": "config/pasos.json",
        "ONB_COHORT": "OTRA",
        "ONB_WALLET_PENDING_STATUS": "en-revision",
        "ONB_DURATION_START_EVENT": "onboarding_step_completed:datos-personales",
        "ONB_DURATION_END_EVENT": "onboarding_step_completed:contacto",
        "ONB_REPORT_UTC_OFFSET_MINUTES": "0",
        "ONB_REF_DURATION_BASELINE_MINUTES": "10",
        "ONB_REF_DURATION_TARGET_MINUTES": "4",
        "ONB_REF_MAU_MIN": "500",
        "ONB_REF_MAU_MAX": "900",
        "ONB_REF_CAC_TARGET_CENTS": "1500",
        "ONB_ANALYTICS_TOKEN": "TEST-token-x",
    }).onboarding
    assert onb.steps_config_path == "config/pasos.json"
    assert onb.cohort == "OTRA"
    assert onb.wallet_pending_status == "en-revision"
    assert onb.duration_start_event == "onboarding_step_completed:datos-personales"
    assert onb.duration_end_event == "onboarding_step_completed:contacto"
    assert onb.report_utc_offset_minutes == 0
    assert (onb.ref_duration_baseline_minutes, onb.ref_duration_target_minutes) == (10, 4)
    assert (onb.ref_mau_min, onb.ref_mau_max) == (500, 900)
    assert onb.ref_cac_target_cents == 1500
    assert onb.analytics_token == "TEST-token-x"


def test_valor_numerico_invalido_en_entorno_falla_al_cargar():
    from app.config import load_settings

    with pytest.raises(ValueError):
        load_settings({"ONB_REPORT_UTC_OFFSET_MINUTES": "no-es-numero"})


def test_settings_sigue_aceptando_los_overrides_de_hu_idem(make_settings):
    # Regresión (sección 10): Settings(**overrides) de los fixtures existentes no cambia
    settings = make_settings(attempt_window_seconds=60, wallet_id="wallet-x")
    assert settings.attempt_window_seconds == 60
    assert settings.wallet_id == "wallet-x"
    assert settings.onboarding.steps_config_path == ""
    assert settings.db_path == "idempotency.sqlite3"


def test_onboarding_settings_es_inmutable(make_settings):
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_settings().onboarding.cohort = "otra"


def test_token_analitico_no_aparece_en_repr(make_settings):
    # Seguridad: sin secretos en logs (principio 17)
    from app.config import OnboardingSettings

    settings = make_settings(onboarding=OnboardingSettings(analytics_token="TEST-secreto-no-imprimir"))
    assert "TEST-secreto-no-imprimir" not in repr(settings)
