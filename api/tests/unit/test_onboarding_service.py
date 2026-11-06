"""Servicio de onboarding: motor de pasos, bloqueo, progreso, eventos y cierre
(tareas 2.1, 2.2, 3.1, 4.1, 5.1, 5.2; req. 'Secuencia de pasos', 'Validación bloqueante', 'Activación', 'Eventos').
SQLite real; reloj controlado. Contrato asumido: ver docs/evidence/user-onboarding-mvp-completion/qe-test-evidence.md."""
import logging
import re
import sqlite3
import threading
from datetime import datetime

import pytest

ONB_USER = "TEST-user-1"
ONB_OTHER_USER = "TEST-user-2"
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


def _statuses(state):
    return [(step.id, step.status) for step in state.steps]


def _types(events):
    return [(e["event_type"], e["step_id"]) for e in events]


def test_new_onboarding_id_tiene_prefijo_y_es_unico():
    # Sección 7: onboarding_id = 'ob_' + uuid4 hex
    from app.services.onboarding_service import new_onboarding_id

    first, second = new_onboarding_id(), new_onboarding_id()
    assert re.fullmatch(r"ob_[0-9a-f]{32}", first)
    assert first != second


# --- Req. Secuencia de pasos y paso actual visibles -------------------------------------------------------------

def test_inicio_muestra_todos_los_pasos_y_resalta_el_primero(onboarding_world, example_flow):
    # Escenarios: Se muestra la secuencia al iniciar / Los pasos provienen de configuración
    started = onboarding_world.onboarding.start_or_resume(ONB_USER)
    state = started.onboarding
    assert started.created is True
    assert _statuses(state) == [("datos-personales", "current"), ("contacto", "pending"), ("aceptacion", "pending")]
    assert [s.order for s in state.steps] == [1, 2, 3]
    assert [s.title for s in state.steps] == [s.title for s in example_flow.steps]
    assert state.current_step_id == "datos-personales"
    assert (state.completed_steps, state.total_steps) == (0, 3)
    assert state.status == "IN_PROGRESS"


def test_la_secuencia_el_orden_y_el_paso_actual_son_los_de_la_configuracion(make_onboarding_world, any_flow):
    # Escenarios: Los pasos provienen de configuración / Cambiar la configuración cambia los pasos (2.1)
    world = make_onboarding_world(flow=any_flow)
    state = world.onboarding.start_or_resume(ONB_USER).onboarding
    assert [s.id for s in state.steps] == [s.id for s in any_flow.steps]
    assert [s.title for s in state.steps] == [s.title for s in any_flow.steps]
    assert state.current_step_id == any_flow.steps[0].id
    assert state.total_steps == len(any_flow.steps)


def test_el_orden_lo_da_order_y_no_la_posicion_en_el_archivo(make_onboarding_world, alternate_flow):
    # El JSON alterno lista 'perfil' (order 2) antes que 'bienvenida' (order 1)
    state = make_onboarding_world(flow=alternate_flow).onboarding.start_or_resume(ONB_USER).onboarding
    assert _statuses(state) == [("bienvenida", "current"), ("perfil", "pending")]


def test_el_paso_actual_avanza_y_la_secuencia_sigue_visible(onboarding_world, valid_values):
    # Escenario: El paso actual se actualiza al avanzar
    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    state = onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                    valid_values["datos-personales"])
    assert _statuses(state) == [("datos-personales", "completed"), ("contacto", "current"),
                                ("aceptacion", "pending")]
    assert state.current_step_id == "contacto"
    assert (state.completed_steps, state.total_steps) == (1, 3)


def test_tras_un_error_de_validacion_el_paso_actual_no_cambia(onboarding_world):
    # Escenario: El paso actual sigue visible tras un error
    from app.errors import StepValidationFailed

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepValidationFailed):
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales", {})
    assert onboarding_world.onboarding.get_current(ONB_USER) == state


def test_el_comportamiento_es_el_mismo_con_cualquier_configuracion(make_onboarding_world, any_flow, valid_values,
                                                                   events_of):
    # Escenario: Cambiar la configuración cambia los pasos sin cambiar el comportamiento
    # (paso actual, bloqueo, progreso, eventos y activación) — mismo motor con ejemplo y alterno
    from app.errors import OnboardingIncomplete, StepValidationFailed

    world = make_onboarding_world(flow=any_flow)
    ids = [s.id for s in any_flow.steps]
    state = world.onboarding.start_or_resume(ONB_USER).onboarding
    oid = state.onboarding_id

    with pytest.raises(StepValidationFailed):  # bloqueo
        world.onboarding.submit_step(ONB_USER, oid, ids[0], {})
    state = world.onboarding.submit_step(ONB_USER, oid, ids[0], valid_values[ids[0]])  # progreso
    assert state.completed_steps == 1
    assert state.current_step_id == (ids[1] if len(ids) > 1 else None)
    with pytest.raises(OnboardingIncomplete):  # cierre bloqueado
        world.onboarding.close(ONB_USER, oid)
    assert world.wallet_access.is_active(ONB_USER) is False
    for step_id in ids[1:]:
        state = world.onboarding.submit_step(ONB_USER, oid, step_id, valid_values[step_id])
    state = world.onboarding.close(ONB_USER, oid)  # activación
    assert (state.status, state.wallet_status) == ("COMPLETED", "activo")
    assert world.wallet_access.is_active(ONB_USER) is True
    expected = [("onboarding_started", "")] + [("onboarding_step_completed", i) for i in ids] + [
        ("onboarding_closed", "")]
    assert _types(events_of(oid)) == expected


# --- Req. Validación bloqueante con mensaje accionable ----------------------------------------------------------

def test_dato_faltante_bloquea_el_avance_sin_evento_ni_progreso(onboarding_world, events_of):
    # Escenario: Falta información obligatoria (tarea 3.1; 5.1: un paso rechazado no genera evento)
    from app.errors import StepValidationFailed

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepValidationFailed) as raised:
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                {"document_number": "TEST-12345"})
    assert [(e.field, e.rule, e.message) for e in raised.value.errors] == [
        ("full_name", "required", "Escribe tu nombre completo.")]
    assert _types(events_of(state.onboarding_id)) == [("onboarding_started", "")]
    assert onboarding_world.onboarding.get_current(ONB_USER).completed_steps == 0


def test_dato_invalido_bloquea_y_devuelve_el_mensaje_configurado(onboarding_world):
    # Escenario: Datos inválidos
    from app.errors import StepValidationFailed

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepValidationFailed) as raised:
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                {"full_name": "Ana Torres", "document_number": "12345"})
    assert [(e.field, e.rule, e.message) for e in raised.value.errors] == [
        ("document_number", "pattern", "Escribe el documento de prueba con el formato TEST-12345.")]


def test_se_corrige_y_se_permite_avanzar(onboarding_world, valid_values):
    # Escenario: Se corrige y se permite avanzar
    from app.errors import StepValidationFailed

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepValidationFailed):
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                {"full_name": "", "document_number": "malo"})
    state = onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                    valid_values["datos-personales"])
    assert state.current_step_id == "contacto"


def test_cambiar_una_regla_configurada_cambia_la_validacion_no_el_bloqueo(make_onboarding_world, example_flow_raw,
                                                                         valid_values):
    # Escenario: Cambiar las reglas configuradas cambia la validación sin cambiar el comportamiento
    from app.errors import StepValidationFailed
    from app.services.flow_config import parse_flow_definition

    phone = example_flow_raw["steps"][1]["fields"][0]
    phone["rules"] = [
        {"kind": "max_length", "value": 10, "message": "El celular de prueba tiene 10 dígitos."},
        {"kind": "pattern", "value": "9[0-9]{9}", "message": "Escribe 10 dígitos que empiecen con 9."},
    ]
    world = make_onboarding_world(flow=parse_flow_definition(example_flow_raw))
    state = world.onboarding.start_or_resume(ONB_USER).onboarding
    world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales", valid_values["datos-personales"])

    with pytest.raises(StepValidationFailed) as raised:  # el valor válido de la regla anterior ahora bloquea
        world.onboarding.submit_step(ONB_USER, state.onboarding_id, "contacto", {"phone": "912345678"})
    assert raised.value.errors[0].message == "Escribe 10 dígitos que empiecen con 9."
    state = world.onboarding.submit_step(ONB_USER, state.onboarding_id, "contacto", {"phone": "9123456789"})
    assert state.current_step_id == "aceptacion"


def test_los_valores_enviados_no_se_reflejan_ni_se_persisten_ni_se_registran(
        onboarding_world, db_path, valid_values, caplog):
    # Decisión D-5 / Q-3; tarea 3.2; principio 17: sin datos personales en el almacén ni en logs
    from app.errors import StepValidationFailed

    secret = "ZZZ-valor-privado-77"
    with caplog.at_level(logging.DEBUG):
        state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
        with pytest.raises(StepValidationFailed) as raised:
            onboarding_world.onboarding.submit_step(
                ONB_USER, state.onboarding_id, "datos-personales",
                {"full_name": "Ana Torres", "document_number": secret})
        assert all(secret not in f"{e.field}{e.rule}{e.message}" for e in raised.value.errors)
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                valid_values["datos-personales"])
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "contacto", valid_values["contacto"])
    con = sqlite3.connect(db_path)
    try:
        dump = "\n".join(con.iterdump())
    finally:
        con.close()
    for value in (secret, "Ana Torres", "TEST-12345", "912345678"):
        assert value not in dump, value
        assert value not in caplog.text, value


# --- Orden, idempotencia y propiedad ----------------------------------------------------------------------------

def test_paso_posterior_al_actual_se_rechaza_sin_efectos(onboarding_world, valid_values, events_of):
    # Diseño 6.2 punto 1 / sección 5: STEP_NOT_CURRENT
    from app.errors import StepNotCurrent

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepNotCurrent):
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "contacto", valid_values["contacto"])
    assert onboarding_world.onboarding.get_current(ONB_USER) == state
    assert _types(events_of(state.onboarding_id)) == [("onboarding_started", "")]


def test_paso_inexistente_se_rechaza(onboarding_world):
    from app.errors import StepNotFound

    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    with pytest.raises(StepNotFound):
        onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "no-existe", {"a": "b"})


def test_reenviar_un_paso_completado_es_idempotente_aun_con_otros_valores(onboarding_world, valid_values, events_of):
    # Decisión Q-7 / tarea 5.2: sin retroceder ni editar; sin evento nuevo ni cambio
    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    after_first = onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                          valid_values["datos-personales"])
    again = onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                    valid_values["datos-personales"])
    different = onboarding_world.onboarding.submit_step(ONB_USER, state.onboarding_id, "datos-personales",
                                                        {"full_name": "Otra Persona", "document_number": "TEST-99999"})
    assert again == different == after_first
    steps = [e for e in events_of(state.onboarding_id) if e["event_type"] == "onboarding_step_completed"]
    assert len(steps) == 1


def test_enviar_el_mismo_paso_en_paralelo_deja_un_unico_evento(onboarding_world, valid_values, events_of):
    # Req. Eventos / Eventos sin duplicados (tarea 5.2, hilos)
    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    results, errors = _run_parallel(lambda i: onboarding_world.onboarding.submit_step(
        ONB_USER, state.onboarding_id, "datos-personales", valid_values["datos-personales"]))
    assert not errors
    assert all(r.completed_steps == 1 for r in results)
    steps = [e for e in events_of(state.onboarding_id) if e["event_type"] == "onboarding_step_completed"]
    assert len(steps) == 1


def test_onboarding_ajeno_o_inexistente_responde_not_found_sin_efectos(onboarding_world, valid_values, events_of):
    # Sección 5: propiedad por user_id (sin enumeración); principio 17
    from app.errors import OnboardingNotFound

    mine = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    for target in (mine.onboarding_id, "ob_inexistente"):
        with pytest.raises(OnboardingNotFound):
            onboarding_world.onboarding.submit_step(ONB_OTHER_USER, target, "datos-personales",
                                                    valid_values["datos-personales"])
        with pytest.raises(OnboardingNotFound):
            onboarding_world.onboarding.close(ONB_OTHER_USER, target)
    assert _types(events_of(mine.onboarding_id)) == [("onboarding_started", "")]


def test_get_current_sin_onboarding_lanza_not_found(onboarding_world):
    from app.errors import OnboardingNotFound

    with pytest.raises(OnboardingNotFound):
        onboarding_world.onboarding.get_current(ONB_USER)


# --- Inicio y reanudación (decisión Q-11) ----------------------------------------------------------------------

def test_iniciar_de_nuevo_reanuda_la_misma_sesion(onboarding_world, valid_values, events_of):
    # Decisión Q-11: una sesión por usuario; reanudar en el paso actual; un solo evento de inicio
    first = onboarding_world.onboarding.start_or_resume(ONB_USER)
    onboarding_world.onboarding.submit_step(ONB_USER, first.onboarding.onboarding_id, "datos-personales",
                                            valid_values["datos-personales"])
    resumed = onboarding_world.onboarding.start_or_resume(ONB_USER)
    assert resumed.created is False
    assert resumed.onboarding.onboarding_id == first.onboarding.onboarding_id
    assert resumed.onboarding.current_step_id == "contacto"
    started = [e for e in events_of(first.onboarding.onboarding_id) if e["event_type"] == "onboarding_started"]
    assert len(started) == 1


def test_usuario_con_onboarding_completado_recibe_su_sesion_completed(onboarding_world, drive):
    # Decisión Q-11
    done = drive(onboarding_world)
    resumed = onboarding_world.onboarding.start_or_resume(ONB_USER)
    assert resumed.created is False
    assert resumed.onboarding.onboarding_id == done.onboarding_id
    assert resumed.onboarding.status == "COMPLETED"


def test_inicio_concurrente_crea_una_sola_sesion(onboarding_world, events_of):
    # Tarea 5.2: reintentos del cliente en paralelo
    results, errors = _run_parallel(lambda i: onboarding_world.onboarding.start_or_resume(ONB_USER))
    assert not errors
    assert sum(1 for r in results if r.created) == 1
    assert len({r.onboarding.onboarding_id for r in results}) == 1
    assert len(events_of()) == 1


def test_cohorte_y_estado_previo_de_la_wallet_vienen_de_la_configuracion(make_onboarding_world):
    # Escenario: Nombres de los demás estados de la wallet (OQ-23); cohorte configurable (OQ-06)
    world = make_onboarding_world(cohort="OTRA-COHORTE", wallet_pending_status="en-revision")
    state = world.onboarding.start_or_resume(ONB_USER).onboarding
    assert (state.cohort, state.wallet_status) == ("OTRA-COHORTE", "en-revision")


def test_por_defecto_cohorte_mvp_pe_y_wallet_pendiente(onboarding_world):
    state = onboarding_world.onboarding.start_or_resume(ONB_USER).onboarding
    assert (state.cohort, state.wallet_status) == ("MVP-PE", "pendiente")


# --- Req. Activación del estado de la wallet --------------------------------------------------------------------

def test_cierre_correcto_activa_la_wallet(onboarding_world, drive):
    # Escenario: Onboarding finalizado correctamente (tarea 4.1)
    state = drive(onboarding_world)
    assert (state.status, state.wallet_status, state.current_step_id) == ("COMPLETED", "activo", None)
    assert state.completed_steps == state.total_steps == 3
    assert all(step.status == "completed" for step in state.steps)
    assert onboarding_world.wallet_access.is_active(ONB_USER) is True


def test_cierre_incompleto_lanza_incomplete_con_los_pasos_pendientes(onboarding_world, drive, events_of):
    # Escenarios: Onboarding incompleto / La wallet no pasa a activo mientras el onboarding no finalice
    from app.errors import OnboardingIncomplete

    state = drive(onboarding_world, count=1, close=False)
    with pytest.raises(OnboardingIncomplete) as raised:
        onboarding_world.onboarding.close(ONB_USER, state.onboarding_id)
    assert list(raised.value.pending_step_ids) == ["contacto", "aceptacion"]
    assert onboarding_world.wallet_access.is_active(ONB_USER) is False
    assert onboarding_world.onboarding.get_current(ONB_USER).wallet_status == "pendiente"
    assert not [e for e in events_of(state.onboarding_id) if e["event_type"] == "onboarding_closed"]


def test_completar_todos_los_pasos_sin_cerrar_no_activa_la_wallet(onboarding_world, drive):
    # Decisión de diseño 4: la transición a activo solo ocurre en el cierre exitoso
    state = drive(onboarding_world, close=False)
    assert state.status == "IN_PROGRESS"
    assert state.current_step_id is None
    assert state.wallet_status == "pendiente"
    assert onboarding_world.wallet_access.is_active(ONB_USER) is False


def test_cierre_repetido_es_idempotente(onboarding_world, drive, events_of):
    # Tarea 4.1: cierre repetido -> sin efectos nuevos, un solo evento de cierre, activated_at estable
    done = drive(onboarding_world, minutes_between=1)
    activated_at = onboarding_world.store.get_wallet(ONB_USER).activated_at
    onboarding_world.clock.advance(hours=1)
    again = onboarding_world.onboarding.close(ONB_USER, done.onboarding_id)
    assert again == done
    assert onboarding_world.store.get_wallet(ONB_USER).activated_at == activated_at
    assert len([e for e in events_of(done.onboarding_id) if e["event_type"] == "onboarding_closed"]) == 1


def test_cierre_concurrente_activa_una_sola_vez(onboarding_world, drive, events_of):
    # Tarea 4.1 / 5.2: 20 hilos cerrando
    state = drive(onboarding_world, close=False)
    results, errors = _run_parallel(lambda i: onboarding_world.onboarding.close(ONB_USER, state.onboarding_id))
    assert not errors
    assert all(r.status == "COMPLETED" and r.wallet_status == "activo" for r in results)
    assert len([e for e in events_of(state.onboarding_id) if e["event_type"] == "onboarding_closed"]) == 1


# --- Req. Eventos de analítica del onboarding -------------------------------------------------------------------

def test_recorrido_completo_registra_inicio_pasos_y_cierre_coherentes(onboarding_world, drive, clock, events_of):
    # Escenarios: Registro del inicio / de cada paso finalizado / del cierre del flujo (tarea 5.1)
    start = clock.current
    state = drive(onboarding_world, minutes_between=2)
    events = events_of(state.onboarding_id)
    assert _types(events) == [
        ("onboarding_started", ""), ("onboarding_step_completed", "datos-personales"),
        ("onboarding_step_completed", "contacto"), ("onboarding_step_completed", "aceptacion"),
        ("onboarding_closed", "")]
    assert {e["cohort"] for e in events} == {"MVP-PE"}
    assert {e["user_id"] for e in events} == {ONB_USER}
    assert {e["onboarding_id"] for e in events} == {state.onboarding_id}
    stamps = [datetime.fromisoformat(e["occurred_at"]) for e in events]
    assert stamps[0] == start
    assert stamps == sorted(stamps)
    assert [(s - start).total_seconds() / 60 for s in stamps] == [0, 2, 4, 6, 8]  # reloj del servidor


def test_abandonar_no_genera_evento_de_cierre_ni_activa(onboarding_world, drive, events_of):
    # Escenario: Registro del cierre del flujo (OQ-21 provisional: cierre solo por finalización exitosa)
    state = drive(onboarding_world, count=2, close=False)
    assert "onboarding_closed" not in {e["event_type"] for e in events_of(state.onboarding_id)}
    assert onboarding_world.wallet_access.is_active(ONB_USER) is False


def test_los_eventos_son_solo_los_tres_tipos_sin_activacion_del_pagador(onboarding_world, drive, events_of):
    # Escenario: Alcance del término «activación» (no se emite el evento de activación del pagador)
    drive(onboarding_world)
    types = {e["event_type"] for e in events_of()}
    assert types == {"onboarding_started", "onboarding_step_completed", "onboarding_closed"}
    assert not any("activation" in t or "payer" in t for t in types)
