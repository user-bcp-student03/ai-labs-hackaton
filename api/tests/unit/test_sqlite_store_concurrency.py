"""Req. 'Una sola transacción por clave' bajo concurrencia (tarea 2.2). SQLite real en archivo temporal."""
import threading
from datetime import datetime, timezone

THREADS = 20


def _run_parallel(fn):
    barrier = threading.Barrier(THREADS)
    results, errors = [], []

    def worker(i):
        barrier.wait()
        try:
            results.append(fn(i))
        except Exception as exc:  # se registra para fallar con motivo claro
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(THREADS)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return results, errors


def test_reserve_attempt_concurrente_crea_una_sola_fila(store):
    # Escenario: Una sola transacción por clave (reserva atómica UNIQUE)
    from app.ports.idempotency_store import NewAttempt

    def reserve(i):
        return store.reserve_attempt(NewAttempt(
            payment_id=f"pay-{i}", idempotency_key="k-1", payer_id="TEST-payer-1", amount_cents=100,
            recipient="merchant-demo", channel="merchant-demo", intent_id="intent-1",
            attempt_window_index=1, created_at=datetime(2026, 11, 6, tzinfo=timezone.utc)))

    results, errors = _run_parallel(reserve)
    assert not errors
    assert sum(1 for r in results if r.outcome == "CREATED") == 1
    assert sum(1 for r in results if r.outcome == "EXISTS") == THREADS - 1


def test_submit_concurrente_llama_una_vez_al_proveedor(world, submit):
    # Tarea 2.2: N solicitudes concurrentes con la misma clave crean una sola transacción
    results, errors = _run_parallel(lambda i: submit(world))
    assert not errors
    assert len(world.provider.submit_calls) == 1
    assert sum(1 for r in results if r.request_type == "original") == 1
    assert len({r.attempt.payment_id for r in results}) == 1
