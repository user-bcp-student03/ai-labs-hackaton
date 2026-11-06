"""Reqs. 'Evento de activación del pagador' e 'Instrumentación del funnel de checkout' (tareas 7.1 a 7.3)."""
import sqlite3
from datetime import datetime, timezone

import pytest


def _filas(db_path, tipo):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    filas = con.execute("SELECT * FROM analytics_events WHERE event_type=?", (tipo,)).fetchall()
    con.close()
    return filas


def test_evento_de_activacion_por_pago_exitoso_con_sus_atributos(world, submit, db_path):
    # Escenario: Evento por pago exitoso
    attempt = submit(world).attempt
    (evento,) = _filas(db_path, "activation")
    assert evento["payment_id"] == attempt.payment_id
    assert evento["payer_id"] == attempt.payer_id
    assert evento["cohort"] == world.settings.cohort
    assert datetime.fromisoformat(evento["occurred_at"]) == world.clock()


@pytest.mark.parametrize("resultado", ["REJECTED", "PENDING"])
def test_sin_evento_de_activacion_en_pagos_no_exitosos(world, submit, db_path, resultado):
    # Escenario: Sin evento en pagos no exitosos
    world.provider.program(resultado)
    submit(world)
    assert _filas(db_path, "activation") == []


def test_sin_eventos_duplicados_ante_repeticion_o_senales_repetidas(world, submit, db_path):
    # Escenario: Sin eventos duplicados
    attempt = submit(world).attempt
    submit(world)
    world.lifecycle.apply_provider_signal(attempt.payment_id, "SUCCEEDED")
    assert len(_filas(db_path, "activation")) == 1
    assert len(_filas(db_path, "final_confirmation")) == 1


def test_reporte_de_caida_en_checkout_entrega_conteos_y_comparacion(world, submit):
    # Escenario: Reporte de caída en checkout
    for index in range(4):
        world.analytics.record_checkout_started("TEST-payer-1", f"i-{index}")
    world.provider.program("SUCCEEDED")
    submit(world, intent_id="i-0")
    world.provider.program("REJECTED")
    submit(world, intent_id="i-1", amount_cents=200)
    world.analytics.record_abandoned("TEST-payer-1", "i-2")
    report = world.analytics.checkout_funnel()
    assert (report.started, report.final_confirmations, report.succeeded, report.failed, report.expired) == (
        4, 2, 1, 1, 0)
    assert report.abandoned == 1
    assert report.drop_rate_pct == 75.0
    assert (report.baseline_pct, report.target_pct) == (30.0, 8.0)


def test_parametros_de_comparacion_del_reporte_son_configurables(world):
    report = world.analytics.checkout_funnel(baseline_pct=25.0, target_pct=10.0)
    assert (report.baseline_pct, report.target_pct, report.drop_rate_pct) == (25.0, 10.0, None)


def test_abandono_solo_si_abrio_la_confirmacion_y_no_la_confirmo(world, submit):
    assert world.analytics.record_abandoned("TEST-payer-1", "i-x") is False
    assert world.analytics.record_abandoned("TEST-payer-2", "i-0") is False
    world.analytics.record_checkout_started("TEST-payer-1", "i-0")
    assert world.analytics.record_abandoned("TEST-payer-2", "i-0") is False
    submit(world, intent_id="i-0")
    assert world.analytics.record_abandoned("TEST-payer-1", "i-0") is True
    assert world.analytics.checkout_funnel().abandoned == 0


def test_el_reporte_filtra_por_periodo_y_cohorte(make_world, submit, clock):
    world = make_world(cohort="OTRA")
    submit(world)
    assert world.analytics.checkout_funnel().succeeded == 1
    hoy = clock()
    assert world.analytics.checkout_funnel(date_to=hoy).succeeded == 0
    assert world.analytics.checkout_funnel(date_from=hoy).succeeded == 1
    otra = make_world(cohort="MVP-PE")
    assert otra.analytics.checkout_funnel().succeeded == 0


def test_conteo_mensual_de_pagadores_activos_distintos_y_rango_de_referencia(world, submit, clock):
    # Escenario: Conteo mensual de pagadores activos
    for payer, intent in (("TEST-p1", "a"), ("TEST-p1", "b"), ("TEST-p2", "c")):
        submit(world, payer_id=payer, intent_id=intent)
    report = world.analytics.monthly_active_payers(2026, 11, reference_min=1, reference_max=2)
    assert report.active_payers == 2
    assert report.within_reference_range
    assert not world.analytics.monthly_active_payers(2026, 11).within_reference_range
    assert (report.reference_min, report.reference_max) == (1, 2)
    assert world.analytics.monthly_active_payers(2026, 10).active_payers == 0
    assert world.analytics.monthly_active_payers(2026, 12).active_payers == 0
    clock.current = datetime(2026, 12, 31, 23, 0, tzinfo=timezone.utc)
    submit(world, payer_id="TEST-p3", intent_id="d")
    assert world.analytics.monthly_active_payers(2026, 12).active_payers == 1
    assert world.analytics.monthly_active_payers(2027, 1).active_payers == 0
