"""Reqs. 'Solicitud repetida devuelve el resultado original' y 'Registro de auditoría de duplicados' (tareas 2.2-2.4, 3.1)."""
import pytest


def test_intento_original_llama_una_vez_al_proveedor(world, submit):
    # Escenario: Intento nuevo recibe clave
    out = submit(world)
    assert out.request_type == "original"
    assert len(world.provider.submit_calls) == 1
    assert out.attempt.idempotency_key


def test_clave_reservada_antes_de_llamar_al_proveedor(world, submit):
    # Escenario: la clave existe antes de crear cualquier transacción financiera (diseño 7.1)
    visto = []
    world.provider.on_submit = lambda key: visto.append(world.store.get_attempt_by_key(key))
    submit(world)
    assert visto and visto[0] is not None and visto[0].status == "PENDING"


def test_clave_del_proveedor_es_la_clave_de_idempotencia(world, submit):
    # Diseño D-6
    out = submit(world)
    assert world.provider.submit_calls[0]["key"] == out.attempt.idempotency_key


def test_pago_legitimo_identico_con_otra_intencion_no_es_duplicado(world, submit):
    # Escenario: Pago legítimo idéntico con otra intención no es duplicado
    a = submit(world, intent_id="intent-1")
    b = submit(world, intent_id="intent-2")
    assert a.attempt.idempotency_key != b.attempt.idempotency_key
    assert (a.request_type, b.request_type) == ("original", "original")
    assert len(world.provider.submit_calls) == 2


def test_mismo_intent_repetido_es_duplicado(world, submit):
    # Escenario: Mismo identificador de intención repetido es duplicado
    a = submit(world)
    b = submit(world)
    assert b.request_type == "duplicate"
    assert b.attempt.payment_id == a.attempt.payment_id


def test_repeticion_con_resultado_terminal_devuelve_el_mismo(world, submit):
    # Escenario: Repetición con resultado terminal
    world.provider.program("SUCCEEDED")
    a = submit(world)
    b = submit(world)
    assert a.attempt.status == b.attempt.status == "SUCCEEDED"
    assert len(world.provider.submit_calls) == 1


def test_repeticion_con_proveedor_rechazado_devuelve_fallido_sin_nuevo_cobro(world, submit):
    # Escenario: Repetición con resultado terminal (FAILED)
    world.provider.program("REJECTED")
    submit(world)
    again = submit(world)
    assert again.attempt.status == "FAILED"
    assert len(world.provider.submit_calls) == 1


def test_repeticion_en_proceso_devuelve_estado_actual_sin_segundo_procesamiento(world, submit):
    # Escenario: Repetición mientras el intento sigue en proceso
    world.provider.program("PENDING")
    submit(world)
    again = submit(world)
    assert again.attempt.status == "PENDING"
    assert len(world.provider.submit_calls) == 1


@pytest.mark.parametrize("canal", ["contact-demo", "merchant-demo"])
def test_mismo_comportamiento_en_cualquier_canal(world, submit, canal):
    # Escenario: Mismo comportamiento en cualquier riel (tarea 2.4, doble)
    a = submit(world, recipient=canal, channel=canal)
    b = submit(world, recipient=canal, channel=canal)
    assert (a.request_type, b.request_type) == ("original", "duplicate")
    assert b.attempt.status == a.attempt.status
    assert len(world.provider.submit_calls) == 1


def test_una_sola_transaccion_por_clave(world, submit):
    # Escenario: Una sola transacción por clave
    for _ in range(6):
        submit(world)
    assert len(world.provider.submit_calls) == 1


def test_timeout_del_proveedor_deja_intento_pendiente(world, submit):
    # Diseño 7.5 / R-4: UNCERTAIN (504) deja PENDING; el pago existe en el proveedor
    world.provider.program("UNCERTAIN", with_id=False)
    out = submit(world)
    assert out.attempt.status == "PENDING"
    assert submit(world).request_type == "duplicate"


def test_resultado_terminal_no_se_sobrescribe(world, submit):
    # Constitución principio 10 / diseño 7.4
    out = submit(world)
    world.store.update_attempt(out.attempt.payment_id, "FAILED", None)
    assert world.store.get_attempt(out.attempt.payment_id).status == "SUCCEEDED"


def test_duplicado_registrado_con_ids_y_clave(world, submit):
    # Escenario: Duplicado registrado
    orig = submit(world, request_id="r-1", correlation_id="c-1")
    submit(world, request_id="r-2", correlation_id="c-2")
    dup = [r for r in world.store.list_requests(_filters()) if r.request_type == "duplicate"]
    assert len(dup) == 1
    assert (dup[0].request_id, dup[0].correlation_id) == ("r-2", "c-2")
    assert dup[0].idempotency_key == orig.attempt.idempotency_key


def test_cada_duplicado_genera_su_registro_y_el_original_no_cambia(world, submit):
    # Escenario: Cada duplicado genera su propio registro
    submit(world, request_id="r-1", correlation_id="c-1")
    antes = [r for r in world.store.list_requests(_filters()) if r.request_type == "original"]
    for i in range(2, 5):
        submit(world, request_id=f"r-{i}", correlation_id=f"c-{i}")
    todos = world.store.list_requests(_filters())
    assert sorted(r.request_id for r in todos if r.request_type == "duplicate") == ["r-2", "r-3", "r-4"]
    assert [r for r in todos if r.request_type == "original"] == antes


def test_politica_clave_vencida_return_original(make_world, submit, clock):
    # Req. Retención (tarea 4.2, decisión P-4): clave vencida devuelve el original, sin segundo cobro
    world = make_world(retention_seconds_by_channel={"default": 60}, attempt_window_seconds=10_000_000)
    a = submit(world)
    clock.advance(seconds=3600)
    b = submit(world)
    assert b.attempt.payment_id == a.attempt.payment_id
    assert len(world.provider.submit_calls) == 1


def _filters(**kw):
    from app.ports.idempotency_store import RequestFilters

    return RequestFilters(**kw)
