"""Req. 'Validación de monto antes del envío' (tarea 2.3). OQ-15 abierta: el límite viene de configuración."""
import pytest

CANAL = "merchant-demo"


def test_sin_limite_configurado_no_se_rechaza_ningun_monto(world, submit):
    # Escenario: Regla de monto bajo pendiente de definición (sin valor fijo en el código)
    assert world.settings.amount_limit_for(CANAL) is None
    assert submit(world, amount_cents=99_000_000).attempt.status == "SUCCEEDED"


def test_monto_dentro_del_limite_permite_continuar(make_world, submit):
    # Escenario: Monto dentro del límite
    world = make_world(amount_limits_cents_by_channel={CANAL: 5000})
    assert submit(world, amount_cents=5000).request_type == "original"


def test_monto_sobre_el_limite_no_envia_ni_crea_intento(make_world, submit):
    # Escenario: Monto por encima del límite del proveedor
    from app.errors import AmountExceedsLimit

    world = make_world(amount_limits_cents_by_channel={CANAL: 5000})
    with pytest.raises(AmountExceedsLimit) as error:
        submit(world, amount_cents=5001)
    assert error.value.limit_cents == 5000
    assert world.provider.submit_calls == []
    assert world.store.count_attempts() == 0


def test_limite_por_defecto_aplica_a_canales_sin_regla_propia(make_world, submit):
    from app.errors import AmountExceedsLimit

    world = make_world(amount_limits_cents_by_channel={"default": 1000, CANAL: 9000})
    assert submit(world, amount_cents=9000).attempt.status == "SUCCEEDED"
    with pytest.raises(AmountExceedsLimit):
        submit(world, amount_cents=1001, recipient="contact-demo", channel="contact-demo", intent_id="i-2")


def test_formato_del_limite_en_soles():
    from app.services.amount_rules import format_amount

    assert format_amount(5000) == "S/ 50.00"
    assert format_amount(5) == "S/ 0.05"
