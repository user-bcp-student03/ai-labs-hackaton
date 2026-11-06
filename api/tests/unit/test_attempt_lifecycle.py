"""Reqs. 'Resultado terminal único por intento' y 'Siguiente acción' — ciclo de vida del intento (tareas 4.1, 4.2, 4.4)."""
import sqlite3

import pytest


def _pendiente(world, submit, **overrides):
    world.provider.program("PENDING")
    return submit(world, **overrides).attempt


def _eventos(db_path, tipo):
    con = sqlite3.connect(db_path)
    filas = con.execute("SELECT * FROM analytics_events WHERE event_type=?", (tipo,)).fetchall()
    con.close()
    return filas


def test_maquina_de_estados_solo_avanza_desde_en_proceso_a_terminal():
    from app.services.attempt_state import can_transition, is_terminal

    for terminal in ("SUCCEEDED", "FAILED", "EXPIRED"):
        assert is_terminal(terminal)
        assert can_transition("PENDING", terminal)
        assert not any(can_transition(terminal, otro) for otro in ("PENDING", "SUCCEEDED", "FAILED", "EXPIRED"))
    assert not is_terminal("PENDING")


def test_estado_pendiente_antes_del_resultado(world, submit):
    # Escenario: Estado pendiente antes del resultado
    assert _pendiente(world, submit).status == "PENDING"


def test_senal_del_proveedor_cierra_el_intento_en_proceso(world, submit):
    attempt = _pendiente(world, submit)
    done = world.lifecycle.apply_provider_signal(attempt.payment_id, "SUCCEEDED")
    assert done.status == "SUCCEEDED"


def test_senales_repetidas_no_cambian_ni_duplican_el_resultado(world, submit, db_path):
    # Escenario: Un solo resultado terminal
    attempt = _pendiente(world, submit)
    world.lifecycle.apply_provider_signal(attempt.payment_id, "SUCCEEDED")
    world.lifecycle.apply_provider_signal(attempt.payment_id, "SUCCEEDED")
    after = world.lifecycle.apply_provider_signal(attempt.payment_id, "REJECTED")
    assert after.status == "SUCCEEDED"
    assert len(_eventos(db_path, "terminal_result")) == 1
    assert len(_eventos(db_path, "activation")) == 1


def test_senal_no_terminal_o_de_pago_desconocido_se_ignora(world, submit):
    attempt = _pendiente(world, submit)
    assert world.lifecycle.apply_provider_signal(attempt.payment_id, "PENDING").status == "PENDING"
    assert world.lifecycle.apply_provider_signal("pay_inexistente", "SUCCEEDED") is None


def test_expira_al_vencer_el_tiempo_maximo(make_world, submit, clock):
    # Escenario: Expiración sin respuesta (OQ-17 configurable)
    world = make_world(attempt_timeout_seconds=60)
    attempt = _pendiente(world, submit)
    clock.advance(seconds=59)
    assert world.lifecycle.refresh(attempt).status == "PENDING"
    clock.advance(seconds=1)
    assert world.lifecycle.refresh(attempt).status == "EXPIRED"


def test_refresh_consulta_al_proveedor_antes_de_expirar(world, submit, clock):
    attempt = _pendiente(world, submit)
    clock.advance(seconds=10_000)
    world.provider.resolve_status = "SUCCEEDED"
    assert world.lifecycle.refresh(attempt).status == "SUCCEEDED"
    assert world.provider.resolve_calls == ["fake-pay-1"]


def test_consulta_fallida_deja_el_intento_sin_cambios_y_la_expiracion_sigue_siendo_por_tiempo(world, submit, clock):
    attempt = _pendiente(world, submit)
    world.provider.resolve_fails = True
    assert world.lifecycle.refresh(attempt).status == "PENDING"
    clock.advance(seconds=world.settings.attempt_timeout_seconds)
    assert world.lifecycle.refresh(attempt).status == "EXPIRED"


def test_confirmacion_tardia_tras_expirar_no_cambia_el_resultado_y_registra_discrepancia(world, submit, clock, db_path):
    # Escenario: Intento expirado con confirmación tardía (OQ-10)
    attempt = _pendiente(world, submit)
    clock.advance(seconds=world.settings.attempt_timeout_seconds)
    world.lifecycle.refresh(attempt)
    late = world.lifecycle.apply_provider_signal(attempt.payment_id, "SUCCEEDED")
    assert late.status == "EXPIRED"
    assert [d.payment_id for d in world.store.list_discrepancies()] == [attempt.payment_id]
    assert _eventos(db_path, "activation") == []
    assert len(world.provider.submit_calls) == 1


def test_expirado_emite_un_unico_resultado_terminal_sin_activacion(world, submit, clock, db_path):
    attempt = _pendiente(world, submit)
    clock.advance(seconds=world.settings.attempt_timeout_seconds)
    world.lifecycle.refresh(attempt)
    world.lifecycle.refresh(attempt)
    assert [fila[7] for fila in _eventos(db_path, "terminal_result")] == ["EXPIRED"]
    assert _eventos(db_path, "activation") == []


def test_configuracion_de_tiempo_maximo_invalida(make_settings):
    with pytest.raises(ValueError):
        make_settings(attempt_timeout_seconds=0)
