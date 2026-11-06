"""Req. 'Retención de claves configurable por canal' (tareas 1.1, 4.1, 4.2)."""
import pytest


def test_valores_provisionales_por_defecto():
    # Escenarios: Ventana de retención no definida / Duración de la ventana de intento no definida
    from app.config import load_settings

    s = load_settings({})
    assert s.attempt_window_seconds == 300
    assert s.retention_seconds_by_channel == {"default": 86400}
    assert s.expired_key_policy == "return_original"
    assert s.audit_retention_seconds is None
    assert s.wallet_mock_url == ""
    assert s.wallet_id == "wallet-demo"


def test_valores_leidos_de_entorno():
    # Tarea 1.1: valores de configuración, no codificados
    from app.config import load_settings

    s = load_settings({
        "IDEM_ATTEMPT_WINDOW_SECONDS": "60",
        "IDEM_RETENTION_SECONDS_BY_CHANNEL": "default=100,merchant-demo=500",
        "IDEM_AUDIT_RETENTION_SECONDS": "3600",
    })
    assert s.attempt_window_seconds == 60
    assert s.retention_seconds_by_channel == {"default": 100, "merchant-demo": 500}
    assert s.audit_retention_seconds == 3600


def test_ventana_de_retencion_por_canal_y_fallback_a_default(make_settings):
    # Escenario: Ventana de retención por canal
    s = make_settings(retention_seconds_by_channel={"default": 100, "merchant-demo": 500})
    assert s.retention_for("merchant-demo") == 500
    assert s.retention_for("contact-demo") == 100


def test_politica_de_clave_vencida_por_defecto_es_return_original(make_settings):
    # Tarea 4.2 / OQ-11 (decisión P-4)
    assert make_settings().expired_key_policy == "return_original"
