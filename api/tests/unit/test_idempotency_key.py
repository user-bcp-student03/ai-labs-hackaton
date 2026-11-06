"""Req. 'Clave de idempotencia por intento de pago' (tarea 2.1)."""
import re

import pytest

BASE = dict(payer_id="TEST-payer-1", amount_cents=100, recipient="merchant-demo",
            attempt_window_index=7, intent_id="intent-1")


def derive(**overrides):
    from app.services.idempotency_key import derive_idempotency_key

    return derive_idempotency_key(**{**BASE, **overrides})


def test_intento_nuevo_recibe_clave_sha256_hex():
    # Escenario: Intento nuevo recibe clave
    assert re.fullmatch(r"[0-9a-f]{64}", derive())


def test_misma_intencion_repetida_misma_clave():
    # Escenario: Mismo identificador de intención repetido es duplicado
    assert derive() == derive()


@pytest.mark.parametrize("campo,valor", [
    ("payer_id", "TEST-payer-2"), ("amount_cents", 101), ("recipient", "contact-demo"),
    ("attempt_window_index", 8), ("intent_id", "intent-2"),
])
def test_cambio_de_componente_cambia_clave(campo, valor):
    # Escenario: Cambio de algún componente genera otra clave
    assert derive(**{campo: valor}) != derive()


def test_forma_canonica_evita_colisiones_por_concatenacion():
    # Escenario: Cambio de algún componente genera otra clave (forma canónica con separador y longitud, diseño 4)
    assert derive(payer_id="ab", recipient="c") != derive(payer_id="a", recipient="bc")


def test_ventana_de_intento_depende_de_configuracion(clock):
    # Escenario: Duración de la ventana de intento no definida (viene de configuración)
    from app.services.idempotency_key import attempt_window_index

    assert attempt_window_index(clock(), 300) != attempt_window_index(clock(), 60)


def test_ventana_bucket_fijo_misma_ventana_mismo_indice(clock):
    # Decisión P-2: buckets fijos
    from datetime import timedelta

    from app.services.idempotency_key import attempt_window_index

    assert attempt_window_index(clock(), 300) == attempt_window_index(clock() + timedelta(seconds=1), 300)
    assert attempt_window_index(clock(), 300) != attempt_window_index(clock() + timedelta(seconds=300), 300)
