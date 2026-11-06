"""Almacén SQLite de onboarding, SQLite real en archivo temporal (diseño secciones 7 y 12; tareas 4.1, 5.1, 5.2)."""
import re
import sqlite3
import threading
from datetime import datetime

import pytest

THREADS = 20
USER = "TEST-user-1"
FIXED_WIDTH_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")


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


def _sql(db_path, statement, params=()):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        with con:
            rows = con.execute(statement, params).fetchall()
    finally:
        con.close()
    return [dict(row) for row in rows]


def _exec(db_path, statement, params=()):
    con = sqlite3.connect(db_path)
    try:
        with con:
            con.execute(statement, params)
    finally:
        con.close()


@pytest.fixture
def onb_store(db_path, clock):
    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    return SqliteOnboardingStore(db_path, clock=clock)


def _start(onb_store, onboarding_id="ob_1", user_id=USER, cohort="MVP-PE", pending="pendiente"):
    return onb_store.start_onboarding(onboarding_id=onboarding_id, user_id=user_id, cohort=cohort,
                                      wallet_pending_status=pending)


def test_crea_las_tablas_del_diseno_y_es_idempotente(db_path, clock, onb_store):
    # Sección 7: tablas propias en el mismo archivo SQLite
    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    SqliteOnboardingStore(db_path, clock=clock)  # abrir dos veces no falla
    names = {row["name"] for row in _sql(db_path, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"onboarding_sessions", "onboarding_step_progress", "onboarding_events", "wallets"} <= names


def test_comparte_archivo_con_el_almacen_de_idempotencia(db_path, store, onb_store):
    # Regresión HU-IDEM: ambos almacenes conviven en el mismo archivo sin interferirse
    from datetime import timezone

    from app.ports.idempotency_store import NewAttempt

    outcome = store.reserve_attempt(NewAttempt(
        payment_id="pay-1", idempotency_key="k-1", payer_id=USER, amount_cents=100, recipient="merchant-demo",
        channel="merchant-demo", intent_id="intent-1", attempt_window_index=1,
        created_at=datetime(2026, 11, 6, tzinfo=timezone.utc)))
    assert outcome.outcome == "CREATED"
    assert _start(onb_store).created is True
    names = {row["name"] for row in _sql(db_path, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"payment_attempts", "payment_requests", "onboarding_sessions"} <= names


def test_start_crea_sesion_wallet_pendiente_y_evento_de_inicio(db_path, clock, onb_store):
    # Req. Eventos / Registro del inicio; tarea 5.1; D-8 (atomicidad)
    outcome = _start(onb_store)
    assert outcome.created is True
    session = outcome.session
    assert (session.onboarding_id, session.user_id, session.cohort, session.status) == (
        "ob_1", USER, "MVP-PE", "IN_PROGRESS")
    assert session.started_at == clock.current
    assert session.closed_at is None
    wallet = onb_store.get_wallet(USER)
    assert (wallet.user_id, wallet.status, wallet.activated_at) == (USER, "pendiente", None)
    events = _sql(db_path, "SELECT * FROM onboarding_events")
    assert len(events) == 1
    event = events[0]
    assert (event["event_type"], event["step_id"], event["onboarding_id"], event["user_id"], event["cohort"]) == (
        "onboarding_started", "", "ob_1", USER, "MVP-PE")
    assert datetime.fromisoformat(event["occurred_at"]) == clock.current


def test_estado_previo_de_la_wallet_viene_del_argumento_no_del_almacen(onb_store):
    # Req. Activación / Nombres de los demás estados (OQ-23): configurable
    _start(onb_store, pending="en-revision")
    assert onb_store.get_wallet(USER).status == "en-revision"


def test_marcas_de_tiempo_en_formato_utc_de_ancho_fijo(db_path, onb_store):
    # Sección 7: mismo formato que sqlite_store, el orden de texto es el orden temporal
    _start(onb_store)
    session = _sql(db_path, "SELECT started_at, updated_at FROM onboarding_sessions")[0]
    event = _sql(db_path, "SELECT occurred_at FROM onboarding_events")[0]
    for text in (session["started_at"], session["updated_at"], event["occurred_at"]):
        assert FIXED_WIDTH_TIMESTAMP.fullmatch(text), text


def test_start_repetido_del_mismo_usuario_reanuda_la_sesion(db_path, onb_store):
    # Decisión Q-11: UNIQUE(user_id); reanudar en vez de reiniciar; tarea 5.2 (inicio sin duplicar)
    first = _start(onb_store, onboarding_id="ob_1")
    second = _start(onb_store, onboarding_id="ob_distinto")
    assert second.created is False
    assert second.session.onboarding_id == first.session.onboarding_id == "ob_1"
    assert len(_sql(db_path, "SELECT * FROM onboarding_sessions")) == 1
    assert len(_sql(db_path, "SELECT * FROM wallets")) == 1
    assert len(_sql(db_path, "SELECT * FROM onboarding_events")) == 1


def test_start_concurrente_crea_una_sola_sesion_y_un_solo_evento(db_path, onb_store):
    # Tarea 5.2: dedup bajo concurrencia
    results, errors = _run_parallel(lambda i: _start(onb_store, onboarding_id=f"ob_{i}"))
    assert not errors
    assert sum(1 for r in results if r.created) == 1
    assert len({r.session.onboarding_id for r in results}) == 1
    assert len(_sql(db_path, "SELECT * FROM onboarding_sessions")) == 1
    assert len(_sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_started'")) == 1


def test_usuarios_distintos_tienen_sesiones_distintas(onb_store):
    _start(onb_store, onboarding_id="ob_1", user_id="TEST-user-1")
    other = _start(onb_store, onboarding_id="ob_2", user_id="TEST-user-2")
    assert other.created is True
    assert other.session.onboarding_id == "ob_2"


def test_user_id_se_trata_como_dato_no_como_sql(db_path, onb_store):
    # Seguridad: consultas parametrizadas (principio 17)
    hostile = "x'; DROP TABLE wallets;--"
    assert _start(onb_store, user_id=hostile).created is True
    assert onb_store.get_session_by_user(hostile).user_id == hostile
    assert onb_store.get_wallet(hostile).status == "pendiente"
    assert _sql(db_path, "SELECT COUNT(*) AS n FROM wallets")[0]["n"] == 1


def test_lecturas_de_lo_inexistente_devuelven_none(onb_store):
    assert onb_store.get_session("ob_no") is None
    assert onb_store.get_session_by_user("TEST-nadie") is None
    assert onb_store.get_wallet("TEST-nadie") is None
    assert onb_store.list_completed_step_ids("ob_no") == []


def test_record_step_completed_registra_progreso_y_evento_una_sola_vez(db_path, onb_store):
    # Req. Eventos / Registro de cada paso finalizado; tarea 5.2: True la primera vez, False al repetir
    _start(onb_store)
    assert onb_store.record_step_completed("ob_1", "datos-personales") is True
    assert onb_store.record_step_completed("ob_1", "datos-personales") is False
    assert onb_store.list_completed_step_ids("ob_1") == ["datos-personales"]
    events = _sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_step_completed'")
    assert len(events) == 1
    assert (events[0]["step_id"], events[0]["onboarding_id"], events[0]["user_id"], events[0]["cohort"]) == (
        "datos-personales", "ob_1", USER, "MVP-PE")


def test_list_completed_step_ids_conserva_el_orden_de_finalizacion(onb_store):
    _start(onb_store)
    for step_id in ("contacto", "datos-personales"):
        onb_store.record_step_completed("ob_1", step_id)
    assert onb_store.list_completed_step_ids("ob_1") == ["contacto", "datos-personales"]


def test_record_step_concurrente_deja_un_solo_progreso_y_un_solo_evento(db_path, onb_store):
    # Tarea 5.2: reenvío del mismo paso en hilos
    _start(onb_store)
    results, errors = _run_parallel(lambda i: onb_store.record_step_completed("ob_1", "contacto"))
    assert not errors
    assert results.count(True) == 1
    assert len(_sql(db_path, "SELECT * FROM onboarding_step_progress")) == 1
    assert len(_sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_step_completed'")) == 1


def test_el_progreso_no_guarda_valores_de_campos(db_path, onb_store):
    # Decisión D-5 / Q-3: solo paso completado y fecha
    _start(onb_store)
    onb_store.record_step_completed("ob_1", "datos-personales")
    columns = {row["name"] for row in _sql(db_path, "PRAGMA table_info(onboarding_step_progress)")}
    assert columns == {"onboarding_id", "step_id", "completed_at"}


def test_close_activa_la_wallet_y_registra_el_cierre_en_una_transaccion(db_path, clock, onb_store):
    # Req. Activación / Onboarding finalizado correctamente; tarea 4.1; D-8
    _start(onb_store)
    clock.advance(minutes=5)
    outcome = onb_store.close_onboarding("ob_1")
    assert outcome.closed_now is True
    assert outcome.session.status == "COMPLETED"
    assert outcome.session.closed_at == clock.current
    wallet = onb_store.get_wallet(USER)
    assert wallet.status == "activo"
    assert wallet.activated_at == clock.current
    closed = _sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_closed'")
    assert len(closed) == 1
    assert (closed[0]["step_id"], closed[0]["cohort"], closed[0]["user_id"]) == ("", "MVP-PE", USER)
    assert datetime.fromisoformat(closed[0]["occurred_at"]) == clock.current


def test_close_repetido_es_idempotente_sin_efectos_nuevos(db_path, clock, onb_store):
    # Req. Activación / tarea 4.1: cierre repetido -> sin cambios y un solo evento de cierre
    _start(onb_store)
    first = onb_store.close_onboarding("ob_1")
    clock.advance(minutes=30)
    second = onb_store.close_onboarding("ob_1")
    assert second.closed_now is False
    assert second.session.status == "COMPLETED"
    assert second.session.closed_at == first.session.closed_at
    assert onb_store.get_wallet(USER).activated_at == first.session.closed_at
    assert len(_sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_closed'")) == 1


def test_close_concurrente_gana_un_solo_hilo(db_path, onb_store):
    # Tarea 4.1: 20 hilos cerrando -> un solo closed_now=True y un solo evento de cierre
    _start(onb_store)
    results, errors = _run_parallel(lambda i: onb_store.close_onboarding("ob_1"))
    assert not errors
    assert sum(1 for r in results if r.closed_now) == 1
    assert all(r.session.status == "COMPLETED" for r in results)
    assert len(_sql(db_path, "SELECT * FROM onboarding_events WHERE event_type = 'onboarding_closed'")) == 1


def test_wallet_no_pasa_a_activo_mientras_no_se_cierre(onb_store):
    # Req. Activación / La wallet no pasa a activo mientras el onboarding no finalice
    _start(onb_store)
    onb_store.record_step_completed("ob_1", "datos-personales")
    assert onb_store.get_wallet(USER).status == "pendiente"
    assert onb_store.get_session("ob_1").status == "IN_PROGRESS"


def _abort_inserts_of(db_path, event_type):
    _exec(db_path, f"CREATE TRIGGER forzar_fallo BEFORE INSERT ON onboarding_events "
                   f"WHEN NEW.event_type = '{event_type}' BEGIN SELECT RAISE(ABORT, 'fallo forzado'); END")


def test_cierre_es_atomico_si_falla_el_evento_no_se_activa_la_wallet(db_path, onb_store):
    # Diseño 7 (transacciones atómicas) / D-8: sesión + wallet + evento o nada
    _start(onb_store)
    _abort_inserts_of(db_path, "onboarding_closed")
    with pytest.raises(sqlite3.DatabaseError):
        onb_store.close_onboarding("ob_1")
    assert onb_store.get_session("ob_1").status == "IN_PROGRESS"
    assert onb_store.get_session("ob_1").closed_at is None
    assert onb_store.get_wallet(USER).status == "pendiente"
    assert onb_store.get_wallet(USER).activated_at is None


def test_inicio_es_atomico_si_falla_el_evento_no_queda_sesion_ni_wallet(db_path, onb_store):
    _abort_inserts_of(db_path, "onboarding_started")
    with pytest.raises(sqlite3.DatabaseError):
        _start(onb_store)
    assert onb_store.get_session_by_user(USER) is None
    assert onb_store.get_wallet(USER) is None


def test_paso_es_atomico_si_falla_el_evento_no_queda_progreso(db_path, onb_store):
    _start(onb_store)
    _abort_inserts_of(db_path, "onboarding_step_completed")
    with pytest.raises(sqlite3.DatabaseError):
        onb_store.record_step_completed("ob_1", "contacto")
    assert onb_store.list_completed_step_ids("ob_1") == []


def test_eventos_son_append_only(db_path, onb_store):
    # Sección 7: triggers RAISE(ABORT) como payment_requests
    _start(onb_store)
    with pytest.raises(sqlite3.DatabaseError):
        _exec(db_path, "UPDATE onboarding_events SET cohort = 'otra'")
    with pytest.raises(sqlite3.DatabaseError):
        _exec(db_path, "DELETE FROM onboarding_events")
    assert len(_sql(db_path, "SELECT * FROM onboarding_events")) == 1


def test_solo_existen_los_tres_tipos_de_evento_de_onboarding(db_path, onb_store):
    # Req. Alcance del término «activación»: no hay evento de activación del pagador (sección 8, CHECK)
    _start(onb_store)
    for event_type in ("payer_activation", "onboarding_abandoned", "activation"):
        with pytest.raises(sqlite3.IntegrityError):
            _exec(db_path, "INSERT INTO onboarding_events (onboarding_id, user_id, cohort, event_type, step_id,"
                           " occurred_at) VALUES ('ob_1', ?, 'MVP-PE', ?, '', '2026-11-06T12:00:00.000000+00:00')",
                  (USER, event_type))


def test_unicidad_de_evento_por_onboarding_tipo_y_paso(db_path, onb_store):
    # Tarea 5.2: UNIQUE (onboarding_id, event_type, step_id)
    _start(onb_store)
    with pytest.raises(sqlite3.IntegrityError):
        _exec(db_path, "INSERT INTO onboarding_events (onboarding_id, user_id, cohort, event_type, step_id,"
                       " occurred_at) VALUES ('ob_1', ?, 'MVP-PE', 'onboarding_started', '',"
                       " '2026-11-06T12:00:00.000000+00:00')", (USER,))


def test_unicidad_de_sesion_por_usuario(db_path, onb_store):
    # Decisión Q-11: UNIQUE(user_id)
    _start(onb_store)
    with pytest.raises(sqlite3.IntegrityError):
        _exec(db_path, "INSERT INTO onboarding_sessions (onboarding_id, user_id, cohort, status, started_at,"
                       " updated_at) VALUES ('ob_2', ?, 'MVP-PE', 'IN_PROGRESS', 'a', 'b')", (USER,))
