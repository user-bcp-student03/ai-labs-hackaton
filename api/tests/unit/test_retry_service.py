"""Req. 'Solicitud repetida devuelve el resultado original' — reintento vinculado (tarea 2.5)."""
import pytest


def _fallar(world, submit, status="REJECTED"):
    world.provider.program(status)
    return submit(world)


def test_reintentar_tras_fallo_crea_nuevo_intento_vinculado(world, submit):
    # Escenario: Reintentar tras fallo o expiración crea un nuevo intento vinculado
    original = _fallar(world, submit)
    retry = world.retries.create_linked_retry(
        payment_id=original.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    assert retry.attempt.payment_id != original.attempt.payment_id
    assert retry.attempt.idempotency_key != original.attempt.idempotency_key
    assert retry.attempt.retry_of_payment_id == original.attempt.payment_id
    assert len(world.provider.submit_calls) == 2


def test_reintentar_tras_expiracion_crea_nuevo_intento(world, submit, db_path):
    # Escenario: Reintentar tras fallo o expiración (EXPIRED)
    original = world.provider.program("PENDING") or submit(world)
    _marcar_expirado(db_path, original.attempt.payment_id)
    retry = world.retries.create_linked_retry(
        payment_id=original.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    assert retry.attempt.retry_of_payment_id == original.attempt.payment_id


def test_clave_original_devuelve_resultado_original_tras_reintento(world, submit):
    # Escenario: La clave original sigue devolviendo el resultado original
    original = _fallar(world, submit)
    world.retries.create_linked_retry(
        payment_id=original.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    again = submit(world)
    assert again.request_type == "duplicate"
    assert again.attempt.payment_id == original.attempt.payment_id
    assert again.attempt.status == "FAILED"


def test_vinculo_almacenado_y_reintento_no_es_duplicado(world, submit):
    # Escenario: Vínculo reintento-original almacenado
    original = _fallar(world, submit)
    retry = world.retries.create_linked_retry(
        payment_id=original.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    guardado = world.store.get_attempt(retry.attempt.payment_id)
    assert guardado.retry_of_payment_id == original.attempt.payment_id
    registros = [r for r in world.store.list_requests(_filters()) if r.payment_id == retry.attempt.payment_id]
    assert [r.request_type for r in registros] == ["original"]


@pytest.mark.parametrize("estado_inicial", ["PENDING", "SUCCEEDED"])
def test_reintento_rechazado_si_original_no_es_fallido_ni_expirado(world, submit, estado_inicial):
    # Decisión P-5: 409 ante reintento sobre intento PENDING (y sobre SUCCEEDED, no fallido)
    from app.errors import RetryNotAllowed

    world.provider.program(estado_inicial)
    original = submit(world)
    with pytest.raises(RetryNotAllowed):
        world.retries.create_linked_retry(
            payment_id=original.attempt.payment_id, payer_id="TEST-payer-1", request_id="r-9", correlation_id="c-9")
    assert len(world.provider.submit_calls) == 1


def _marcar_expirado(db_path, payment_id):
    # EXPIRED lo fija PAYER (OQ-17, S-3): se simula directo en el almacén
    import sqlite3

    con = sqlite3.connect(db_path)
    con.execute("UPDATE payment_attempts SET status='EXPIRED' WHERE payment_id=?", (payment_id,))
    con.commit()
    con.close()


def _filters(**kw):
    from app.ports.idempotency_store import RequestFilters

    return RequestFilters(**kw)
