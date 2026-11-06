"""Reqs. 'Auditoría de duplicados' y 'Distinción de originales y duplicados para conciliación' (tareas 3.2, 5.1, 5.2)."""
import dataclasses


def test_auditoria_relaciona_duplicado_con_original_por_clave_y_correlacion(world, submit):
    # Escenario: Trazabilidad entre original y duplicado
    orig = submit(world, request_id="r-1", correlation_id="c-1")
    submit(world, request_id="r-2", correlation_id="c-2")
    por_clave = world.audit.list_requests(idempotency_key=orig.attempt.idempotency_key)
    assert {r.request_type for r in por_clave} == {"original", "duplicate"}
    por_corr = world.audit.list_requests(correlation_id="c-2")
    assert [r.request_id for r in por_corr] == ["r-2"]
    assert por_corr[0].payment_id == orig.attempt.payment_id


def test_intento_original_identificado(world, submit):
    # Escenario: Intento original identificado
    submit(world)
    assert [r.request_type for r in world.audit.list_requests()] == ["original"]


def test_reintento_duplicado_identificado_con_vinculo(world, submit):
    # Escenario: Reintento duplicado identificado
    orig = submit(world)
    submit(world)
    dup = world.audit.list_requests(request_type="duplicate")
    assert len(dup) == 1 and dup[0].payment_id == orig.attempt.payment_id


def test_datos_expuestos_por_solicitud_con_ambas_fechas(make_world, submit, clock):
    # Escenarios: Datos expuestos por solicitud / Día de reporte del duplicado no asignado aquí
    # Ventana amplia: con buckets fijos (P-2), 25 h con la ventana por defecto generaría otra clave.
    world = make_world(attempt_window_seconds=10_000_000)
    submit(world)
    t0 = clock()
    clock.advance(days=1, hours=1)
    submit(world)
    dup = world.audit.list_requests(request_type="duplicate")[0]
    assert dup.requested_at != dup.original_requested_at
    assert dup.original_requested_at == t0
    campos = {f.name for f in dataclasses.fields(dup)}
    assert {"request_type", "payment_id", "requested_at", "original_requested_at"} <= campos
    assert not {c for c in campos if "report" in c}


def test_reintento_vinculado_se_distingue_del_duplicado(world, submit):
    # Escenario: Reintento vinculado distinguido del duplicado
    world.provider.program("REJECTED")
    orig = submit(world)
    retry = world.retries.create_linked_retry(
        payment_id=orig.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    fila = [r for r in world.audit.list_requests() if r.payment_id == retry.attempt.payment_id]
    assert [r.request_type for r in fila] == ["original"]
    assert fila[0].retry_of_payment_id == orig.attempt.payment_id


def test_duplicados_no_cuentan_como_transacciones(world, submit):
    # Escenario: Duplicados no cuentan como transacciones adicionales (tarea 5.2)
    submit(world)
    for _ in range(3):
        submit(world)
    submit(world, intent_id="intent-2")
    assert world.audit.totals().transactions == 2
