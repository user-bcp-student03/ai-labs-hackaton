"""Reqs. 'Resumen previo a la confirmación final' e identificador de intención (tareas 3.x, 5.2; decisión OQ-01)."""
from app.services.confirmation_service import (
    REASON_AMOUNT_EXCEEDS_LIMIT,
    REASON_MISSING_DATA,
    REASON_PREVIOUS_IN_PROGRESS,
)

PAYER = "TEST-payer-1"


def _abrir(world, **overrides):
    params = dict(payer_id=PAYER, recipient="merchant-demo", amount_cents=100, channel="merchant-demo")
    params.update(overrides)
    return world.confirmations.open_confirmation(**params)


def test_confirmacion_con_destino_y_monto_genera_identificador_de_intencion(world):
    # Escenarios: Se muestran destino y monto / Identificador de intención al abrir la confirmación
    confirmation = _abrir(world)
    assert confirmation.can_confirm
    assert (confirmation.recipient, confirmation.amount_cents) == ("merchant-demo", 100)
    assert confirmation.intent_id.startswith("intent-")


def test_cada_apertura_genera_un_identificador_distinto(world):
    assert _abrir(world).intent_id != _abrir(world).intent_id


def test_el_identificador_se_envia_tal_cual_a_idempotencia(world, submit):
    # La clave la deriva payment-idempotency; este flujo solo aporta el identificador
    intent_id = _abrir(world).intent_id
    attempt = submit(world, intent_id=intent_id).attempt
    assert attempt.intent_id == intent_id
    assert submit(world, intent_id=intent_id).request_type == "duplicate"


def test_no_se_habilita_sin_destino_o_monto(world):
    # Escenario: No se permite confirmar sin datos del destino
    for faltante in ({"recipient": None}, {"amount_cents": None}):
        confirmation = _abrir(world, **faltante)
        assert not confirmation.can_confirm
        assert confirmation.reason == REASON_MISSING_DATA
        assert confirmation.intent_id is None


def test_monto_sobre_el_limite_no_se_habilita_y_informa_el_limite(make_world):
    world = make_world(amount_limits_cents_by_channel={"merchant-demo": 5000})
    confirmation = _abrir(world, amount_cents=5001)
    assert (confirmation.can_confirm, confirmation.reason) == (False, REASON_AMOUNT_EXCEEDS_LIMIT)
    assert confirmation.limit_cents == 5000
    assert confirmation.intent_id is None


def test_intento_previo_en_proceso_bloquea_sin_crear_intento_ni_identificador(world, submit):
    # Escenario: Mensaje accionable durante el bloqueo (no se crea cobro, intento ni referencia)
    world.provider.program("PENDING")
    previo = submit(world).attempt
    confirmation = _abrir(world)
    assert (confirmation.can_confirm, confirmation.reason) == (False, REASON_PREVIOUS_IN_PROGRESS)
    assert confirmation.previous_payment_id == previo.payment_id
    assert confirmation.intent_id is None
    assert world.store.count_attempts() == 1
