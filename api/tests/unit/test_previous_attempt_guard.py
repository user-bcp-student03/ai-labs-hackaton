"""Req. 'Verificación del intento previo antes de un nuevo intento' (tarea 5.4, decisión OQ-03)."""
import pytest

from app.errors import PreviousAttemptInProgress


def _previo_pendiente(world, submit):
    world.provider.program("PENDING")
    return submit(world, intent_id="intent-previo").attempt


def test_previo_en_proceso_bloquea_el_nuevo_intento(world, submit):
    # Escenario: Previo en proceso bloquea el nuevo intento
    previo = _previo_pendiente(world, submit)
    with pytest.raises(PreviousAttemptInProgress) as bloqueo:
        submit(world, intent_id="intent-nuevo")
    assert bloqueo.value.previous_payment_id == previo.payment_id
    assert len(world.provider.submit_calls) == 1
    assert world.store.count_attempts() == 1


def test_previo_incierto_bloquea_incluida_una_consulta_que_no_se_completa(world, submit):
    # Escenario: Previo incierto bloquea el nuevo intento
    _previo_pendiente(world, submit)
    world.provider.resolve_fails = True
    with pytest.raises(PreviousAttemptInProgress):
        submit(world, intent_id="intent-nuevo")
    assert world.store.count_attempts() == 1


def test_previo_sin_respuesta_del_proveedor_bloquea(world, submit):
    # El proveedor falló al enviar: el intento queda PENDING sin id de proveedor (incierto)
    world.provider.program("UNCERTAIN", with_id=False)
    submit(world, intent_id="intent-previo")
    with pytest.raises(PreviousAttemptInProgress):
        submit(world, intent_id="intent-nuevo")


@pytest.mark.parametrize("resultado_previo", ["REJECTED", "SUCCEEDED"])
def test_previo_terminal_permite_el_nuevo_intento(world, submit, resultado_previo):
    # Escenario: Previo terminal permite el nuevo intento
    world.provider.program(resultado_previo)
    submit(world, intent_id="intent-previo")
    assert submit(world, intent_id="intent-nuevo").request_type == "original"
    assert len(world.provider.submit_calls) == 2


def test_previo_expirado_permite_el_nuevo_intento_y_el_bloqueo_se_levanta(world, submit, clock):
    # Escenario: Fin del bloqueo al llegar a un estado terminal
    _previo_pendiente(world, submit)
    with pytest.raises(PreviousAttemptInProgress):
        submit(world, intent_id="intent-nuevo")
    clock.advance(seconds=world.settings.attempt_timeout_seconds)
    assert submit(world, intent_id="intent-nuevo").request_type == "original"


def test_bloqueo_se_levanta_cuando_el_proveedor_informa_fallo(world, submit):
    _previo_pendiente(world, submit)
    world.provider.resolve_status = "REJECTED"
    assert submit(world, intent_id="intent-nuevo").request_type == "original"


def test_repeticion_con_el_mismo_identificador_no_es_un_nuevo_intento(world, submit):
    # Escenario: Repetición de la misma confirmación no es un nuevo intento
    previo = _previo_pendiente(world, submit)
    repeticion = submit(world, intent_id="intent-previo")
    assert repeticion.request_type == "duplicate"
    assert repeticion.attempt.payment_id == previo.payment_id


def test_alcance_limitado_a_la_misma_intencion_de_pago(world, submit):
    # Escenario: Alcance y definición de incierto (pagador, monto y destino)
    _previo_pendiente(world, submit)
    assert submit(world, intent_id="i-2", amount_cents=200).request_type == "original"
    assert submit(world, intent_id="i-3", recipient="contact-demo", channel="contact-demo").request_type == "original"
    assert submit(world, intent_id="i-4", payer_id="TEST-payer-2").request_type == "original"


def test_reintento_vinculado_bloqueado_si_hay_otro_intento_en_proceso(world, submit):
    world.provider.program("REJECTED")
    fallido = submit(world, intent_id="intent-1").attempt
    world.provider.program("PENDING")
    submit(world, intent_id="intent-2")
    with pytest.raises(PreviousAttemptInProgress):
        world.retries.create_linked_retry(
            payment_id=fallido.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
