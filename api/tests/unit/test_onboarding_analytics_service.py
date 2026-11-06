"""Salida analítica mensual y reporte de duración (tareas 5.3, 6.1, 6.2 parcial, 6.3; req. 'Datos para medir la duración'
y 'Salida analítica'). Servicio real sobre SQLite real y reloj controlado.
Contrato asumido: monthly_output(month) y duration_report(month) devuelven dict con las claves de diseño 9.1 y 9.2.
La atribución de gasto de adquisición (tarea 6.2) está bloqueada por OQ-22: solo se prueba el contrato 'unavailable'."""
from datetime import datetime, timezone

import pytest

MONTHLY_KEYS = {"month", "cohort", "new_active_users", "acquisition_spend", "reference", "pending_definitions"}
DURATION_KEYS = {"month", "cohort", "finished_onboardings", "median_minutes", "reference", "boundary"}


def _utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def _finish(world, drive, user, at, **kwargs):
    world.clock.current = at
    return drive(world, user_id=user, **kwargs)


# --- Salida mensual (tarea 6.1) ---------------------------------------------------------------------------------

def test_salida_mensual_sin_datos_tiene_las_claves_documentadas(onboarding_world):
    # Tarea 6.3: las claves devueltas coinciden con las documentadas (diseño 9.1); 0 usuarios, no null
    out = onboarding_world.analytics.monthly_output("2026-11")
    assert set(out) == MONTHLY_KEYS
    assert out["month"] == "2026-11"
    assert out["cohort"] == "MVP-PE"
    assert out["new_active_users"] == 0
    assert out["reference"] == {"mau_min": 1000, "mau_max": 2000, "cac_target_pen_cents": 1000}
    assert out["pending_definitions"] == ["OQ-05", "OQ-22"]


def test_conteo_mensual_solo_cuenta_wallets_activas_del_mes(onboarding_world, drive):
    # Escenarios: Conteo mensual de nuevos usuarios activos / Usuario sin onboarding finalizado /
    # Definición de «nuevo usuario activo» (wallet activo)
    w = onboarding_world
    _finish(w, drive, "TEST-oct", _utc(2026, 10, 15, 15, 0))
    _finish(w, drive, "TEST-nov-1", _utc(2026, 11, 6, 15, 0))
    _finish(w, drive, "TEST-nov-2", _utc(2026, 11, 20, 15, 0))
    _finish(w, drive, "TEST-dic", _utc(2026, 12, 2, 15, 0))
    _finish(w, drive, "TEST-incompleto", _utc(2026, 11, 7, 15, 0), count=2, close=False)
    _finish(w, drive, "TEST-pasos-sin-cierre", _utc(2026, 11, 8, 15, 0), close=False)
    w.onboarding.start_or_resume("TEST-solo-inicio")
    assert w.analytics.monthly_output("2026-10")["new_active_users"] == 1
    assert w.analytics.monthly_output("2026-11")["new_active_users"] == 2
    assert w.analytics.monthly_output("2026-12")["new_active_users"] == 1


def test_conteo_mensual_excluye_otras_cohortes(make_onboarding_world, drive):
    # Escenario: Conteo mensual de la cohorte MVP Perú (criterio 6)
    mine = make_onboarding_world()
    other = make_onboarding_world(onboarding_store=mine.store, cohort="OTRA-COHORTE")
    _finish(mine, drive, "TEST-mia", _utc(2026, 11, 6, 15, 0))
    _finish(other, drive, "TEST-ajena-1", _utc(2026, 11, 6, 16, 0))
    _finish(other, drive, "TEST-ajena-2", _utc(2026, 11, 6, 17, 0))
    assert mine.analytics.monthly_output("2026-11")["new_active_users"] == 1
    assert other.analytics.monthly_output("2026-11")["new_active_users"] == 2
    assert other.analytics.monthly_output("2026-11")["cohort"] == "OTRA-COHORTE"


@pytest.mark.parametrize("closed_at, month", [
    (_utc(2026, 11, 1, 4, 59, 59), "2026-10"),   # 23:59:59 del 31-oct en Lima (-300)
    (_utc(2026, 11, 1, 5, 0, 0), "2026-11"),     # 00:00:00 del 1-nov en Lima
    (_utc(2026, 12, 1, 4, 59, 59), "2026-11"),   # 23:59:59 del 30-nov en Lima
    (_utc(2026, 12, 1, 5, 0, 0), "2026-12"),     # 00:00:00 del 1-dic en Lima
])
def test_limites_mensuales_usan_el_desfase_configurado_por_defecto(onboarding_world, drive, closed_at, month):
    # Decisión Q-5 / S-2: desfase -300 minutos
    _finish(onboarding_world, drive, "TEST-borde", closed_at)
    assert onboarding_world.analytics.monthly_output(month)["new_active_users"] == 1
    other_months = {"2026-10", "2026-11", "2026-12"} - {month}
    assert all(onboarding_world.analytics.monthly_output(m)["new_active_users"] == 0 for m in other_months)


def test_el_desfase_horario_es_configurable(make_onboarding_world, drive):
    # Decisión Q-5: ONB_REPORT_UTC_OFFSET_MINUTES
    utc_world = make_onboarding_world(report_utc_offset_minutes=0)
    _finish(utc_world, drive, "TEST-borde", _utc(2026, 12, 1, 4, 59, 59))
    assert utc_world.analytics.monthly_output("2026-12")["new_active_users"] == 1
    assert utc_world.analytics.monthly_output("2026-11")["new_active_users"] == 0
    lima_world = make_onboarding_world(onboarding_store=utc_world.store)
    assert lima_world.analytics.monthly_output("2026-11")["new_active_users"] == 1


def test_gasto_de_adquisicion_siempre_no_disponible_y_nunca_cero(onboarding_world, drive):
    # Escenario: Mes sin gasto de adquisición disponible; OQ-22 abierta -> siempre 'unavailable'
    for month in ("2026-11", "2026-12"):
        spend = onboarding_world.analytics.monthly_output(month)["acquisition_spend"]
        assert spend == {"status": "unavailable", "amount_pen_cents": None}
    _finish(onboarding_world, drive, "TEST-activo", _utc(2026, 11, 6, 15, 0))
    spend = onboarding_world.analytics.monthly_output("2026-11")["acquisition_spend"]
    assert spend["status"] == "unavailable"
    assert spend["amount_pen_cents"] is None
    assert spend["amount_pen_cents"] != 0


def test_parametros_de_referencia_son_configurables(make_onboarding_world):
    # Escenarios: Campos de la salida mensual / Reporte consolidado fuera de alcance (solo parámetros)
    world = make_onboarding_world(ref_mau_min=500, ref_mau_max=900, ref_cac_target_cents=1500)
    assert world.analytics.monthly_output("2026-11")["reference"] == {
        "mau_min": 500, "mau_max": 900, "cac_target_pen_cents": 1500}


def test_la_salida_mensual_no_calcula_mau_ni_cac(onboarding_world):
    # Escenario: Reporte consolidado fuera de alcance (OQ-07): sin resultados de MAU/CAC, solo conteo y referencia
    out = onboarding_world.analytics.monthly_output("2026-11")
    assert not {"mau", "cac", "cac_pen_cents", "target_met"} & set(out)


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "nov-2026", "", "2026-11-01"])
def test_mes_con_formato_invalido_lanza_value_error(onboarding_world, month):
    # Supuesto de contrato: month = YYYY-MM; otro formato es ValueError (la ruta lo traduce a 422)
    with pytest.raises(ValueError):
        onboarding_world.analytics.monthly_output(month)
    with pytest.raises(ValueError):
        onboarding_world.analytics.duration_report(month)


# --- Reporte de duración (tarea 5.3) ----------------------------------------------------------------------------

def test_reporte_de_duracion_sin_datos_tiene_claves_y_mediana_nula(onboarding_world):
    # Escenario: Reporte periódico de duración; sin datos median_minutes es null, no 0
    out = onboarding_world.analytics.duration_report("2026-11")
    assert set(out) == DURATION_KEYS
    assert out["month"] == "2026-11"
    assert out["cohort"] == "MVP-PE"
    assert out["finished_onboardings"] == 0
    assert out["median_minutes"] is None
    assert out["reference"] == {"baseline_minutes": 8, "target_minutes": 3}


def test_frontera_por_defecto_se_publica_como_provisional(onboarding_world):
    # Escenarios: Frontera de eventos no definida / Frontera pendiente de definición oficial (OQ-20)
    assert onboarding_world.analytics.duration_report("2026-11")["boundary"] == {
        "start": "onboarding_started", "end": "onboarding_closed", "status": "provisional_oq20"}


def test_mediana_con_cantidad_impar_de_onboardings(onboarding_world, drive):
    # Escenario: Cálculo de la mediana de la cohorte. Duración = cierre - inicio: 4, 8 y 12 minutos
    for index, minutes in enumerate((1, 2, 3)):
        _finish(onboarding_world, drive, f"TEST-u{index}", _utc(2026, 11, 6, 12 + index), minutes_between=minutes)
    out = onboarding_world.analytics.duration_report("2026-11")
    assert out["finished_onboardings"] == 3
    assert out["median_minutes"] == pytest.approx(8.0)


def test_mediana_con_cantidad_par_promedia_los_dos_centrales(onboarding_world, drive):
    for index, minutes in enumerate((1, 2, 3, 4)):  # 4, 8, 12 y 16 minutos
        _finish(onboarding_world, drive, f"TEST-u{index}", _utc(2026, 11, 6, 12 + index), minutes_between=minutes)
    assert onboarding_world.analytics.duration_report("2026-11")["median_minutes"] == pytest.approx(10.0)


def test_la_mediana_resiste_un_valor_extremo(onboarding_world, drive):
    # La mediana, no el promedio: 4, 8 y 400 minutos -> 8
    for index, minutes in enumerate((1, 2, 100)):
        _finish(onboarding_world, drive, f"TEST-u{index}", _utc(2026, 11, 6, 12 + index), minutes_between=minutes)
    assert onboarding_world.analytics.duration_report("2026-11")["median_minutes"] == pytest.approx(8.0)


def test_excluye_onboardings_sin_evento_de_fin_otra_cohorte_y_otro_mes(make_onboarding_world, drive):
    # Escenario: Cálculo de la mediana (solo onboardings con evento de fin, de la cohorte y del mes del fin)
    world = make_onboarding_world()
    other = make_onboarding_world(onboarding_store=world.store, cohort="OTRA-COHORTE")
    _finish(world, drive, "TEST-ok", _utc(2026, 11, 6, 12), minutes_between=1)          # 4 min, noviembre
    _finish(world, drive, "TEST-sin-fin", _utc(2026, 11, 6, 13), count=1, close=False, minutes_between=1)
    _finish(other, drive, "TEST-otra", _utc(2026, 11, 6, 14), minutes_between=30)
    _finish(world, drive, "TEST-dic", _utc(2026, 12, 3, 12), minutes_between=60)          # fin en diciembre
    out = world.analytics.duration_report("2026-11")
    assert out["finished_onboardings"] == 1
    assert out["median_minutes"] == pytest.approx(4.0)
    assert world.analytics.duration_report("2026-12")["median_minutes"] == pytest.approx(240.0)


def test_el_onboarding_pertenece_al_mes_de_su_evento_de_fin_con_desfase(onboarding_world, drive):
    # Diseño 9.2: el mes lo da el evento de fin, evaluado con el desfase configurado (-300)
    _finish(onboarding_world, drive, "TEST-cruza-mes", _utc(2026, 12, 1, 4, 50), minutes_between=1)
    assert onboarding_world.analytics.duration_report("2026-11")["finished_onboardings"] == 1
    assert onboarding_world.analytics.duration_report("2026-12")["finished_onboardings"] == 0


def test_frontera_de_prueba_distinta_de_la_provisional(make_onboarding_world, drive):
    # Escenario: Cálculo de la mediana de la cohorte con una frontera de prueba (fin = paso 'contacto'); tarea 5.3
    world = make_onboarding_world(duration_end_event="onboarding_step_completed:contacto")
    for index, minutes in enumerate((1, 2, 3)):  # inicio -> contacto = 2m: 2, 4 y 6 minutos
        _finish(world, drive, f"TEST-u{index}", _utc(2026, 11, 6, 12 + index), count=2, close=False,
                minutes_between=minutes)
    _finish(world, drive, "TEST-no-llego", _utc(2026, 11, 6, 20), count=1, close=False, minutes_between=1)
    out = world.analytics.duration_report("2026-11")
    assert out["finished_onboardings"] == 3
    assert out["median_minutes"] == pytest.approx(4.0)
    assert out["boundary"]["start"] == "onboarding_started"
    assert out["boundary"]["end"] == "onboarding_step_completed:contacto"


def test_frontera_con_evento_de_paso_tambien_como_inicio(make_onboarding_world, drive):
    # Formato 'event_type[:step_id]' en ambos extremos (ONB_DURATION_START_EVENT / ONB_DURATION_END_EVENT)
    world = make_onboarding_world(duration_start_event="onboarding_step_completed:datos-personales")
    _finish(world, drive, "TEST-u", _utc(2026, 11, 6, 12), minutes_between=2)  # paso 1 en +2, cierre en +8 -> 6
    out = world.analytics.duration_report("2026-11")
    assert out["finished_onboardings"] == 1
    assert out["median_minutes"] == pytest.approx(6.0)
    assert out["boundary"]["start"] == "onboarding_step_completed:datos-personales"


def test_valores_8_y_3_son_parametros_configurables_no_resultados(make_onboarding_world):
    # Escenario: Valores de referencia no garantizados
    world = make_onboarding_world(ref_duration_baseline_minutes=10, ref_duration_target_minutes=4)
    out = world.analytics.duration_report("2026-11")
    assert out["reference"] == {"baseline_minutes": 10, "target_minutes": 4}
    assert not {"target_met", "reduction", "achieved"} & set(out)
