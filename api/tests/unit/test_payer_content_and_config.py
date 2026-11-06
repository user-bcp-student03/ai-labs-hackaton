"""Reqs. 'Etiquetas de estados terminales pendientes de definición' y configuración del flujo del pagador."""
import json

import pytest

from app.config import Settings, load_settings
from app.content import Content


def test_estados_terminales_con_etiquetas_distintas():
    # Escenario: Estados distinguibles
    content = Content()
    etiquetas = {content.status_label(estado) for estado in ("SUCCEEDED", "FAILED", "EXPIRED")}
    assert len(etiquetas) == 3
    assert content.status_label("PENDING") not in etiquetas


def test_textos_se_sobrescriben_por_configuracion():
    content = Content({"status.SUCCEEDED": "Pago listo", "message.amount_exceeds_limit": "Máximo {limit}"})
    assert content.status_label("SUCCEEDED") == "Pago listo"
    assert content.text("message.amount_exceeds_limit", limit="S/ 10.00") == "Máximo S/ 10.00"


def test_etiquetas_terminales_repetidas_o_claves_desconocidas_se_rechazan():
    with pytest.raises(ValueError):
        Content({"status.FAILED": "Exitoso"})
    with pytest.raises(ValueError):
        Content({"clave.inexistente": "x"})


def test_configuracion_por_defecto_sin_limites_de_monto():
    settings = Settings()
    assert settings.amount_limits_cents_by_channel == {}
    assert settings.attempt_timeout_seconds == 120
    assert settings.cohort == "MVP-PE"


def test_configuracion_desde_variables_de_entorno():
    settings = load_settings({
        "PAY_ATTEMPT_TIMEOUT_SECONDS": "45",
        "PAY_AMOUNT_LIMITS_CENTS_BY_CHANNEL": "merchant-demo=5000, default=1000",
        "PAY_COHORT": "PE_TEST",
        "PAY_CONTENT_JSON": json.dumps({"status.EXPIRED": "Vencido"}),
    })
    assert settings.attempt_timeout_seconds == 45
    assert settings.amount_limit_for("merchant-demo") == 5000
    assert settings.amount_limit_for("otro") == 1000
    assert settings.cohort == "PE_TEST"
    assert Content(settings.content_overrides).status_label("EXPIRED") == "Vencido"


@pytest.mark.parametrize("env", [
    {"PAY_CONTENT_JSON": "[1]"},
    {"PAY_CONTENT_JSON": '{"status.FAILED": 3}'},
    {"PAY_AMOUNT_LIMITS_CENTS_BY_CHANNEL": "sin-igual"},
    {"PAY_AMOUNT_LIMITS_CENTS_BY_CHANNEL": "merchant-demo=0"},
    {"PAY_ATTEMPT_TIMEOUT_SECONDS": "0"},
])
def test_configuracion_invalida_se_rechaza(env):
    with pytest.raises(ValueError):
        load_settings(env)
