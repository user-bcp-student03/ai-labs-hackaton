"""Cableado condicional del onboarding en create_app (diseño 3.3 y trampa de la sección 1; decisión D-9).
Sin flujo configurado: sin archivos, rutas nuevas con 503 y rutas de pagos intactas."""
import inspect
import json
import sqlite3

import pytest

HEADERS = {"X-Payer-Id": "TEST-user-1"}
TOKEN = "TEST-analytics-token"
NEW_ROUTES = [
    ("GET", "/onboarding/flow", None),
    ("POST", "/onboarding", None),
    ("GET", "/onboarding/current", None),
    ("PUT", "/onboarding/ob_x/steps/datos-personales", {"values": {}}),
    ("POST", "/onboarding/ob_x/close", None),
    ("GET", "/wallet", None),
    ("GET", "/wallet/payments-entry", None),
]
ANALYTICS_ROUTES = ["/analytics/onboarding/monthly?month=2026-11", "/analytics/onboarding/duration?month=2026-11"]


def _tables(path):
    con = sqlite3.connect(path)
    try:
        return {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        con.close()


def _client_without_flow(store, provider, clock, make_settings, **onboarding):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from app.main import create_app

    base = make_settings()
    settings = replace(base, onboarding=replace(base.onboarding, **onboarding))
    return TestClient(create_app(settings=settings, provider=provider, store=store, clock=clock))


def test_create_app_acepta_las_llamadas_actuales_y_los_parametros_nuevos_son_solo_por_palabra_clave():
    # Diseño 3.3: compatibilidad hacia atrás; onboarding_flow y onboarding_store keyword-only y opcionales
    from app.main import create_app

    params = inspect.signature(create_app).parameters
    assert list(params)[:4] == ["provider", "settings", "store", "clock"]
    for name in ("onboarding_flow", "onboarding_store"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert params[name].default is None


def test_sin_flujo_los_servicios_de_onboarding_son_none(client):
    # Diseño 3.3: .onboarding, .wallet_access y .onboarding_analytics son None
    services = client.app.state.services
    assert services.onboarding is None
    assert services.wallet_access is None
    assert services.onboarding_analytics is None


def test_sin_flujo_no_se_crea_ningun_archivo_ni_tablas_de_onboarding(tmp_path, monkeypatch, store, db_path, provider,
                                                                      clock, make_settings):
    # Trampa de la sección 1: db_path por defecto es relativo; las 52 pruebas de HU-IDEM no deben crear archivos
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    client = _client_without_flow(store, provider, clock, make_settings)
    client.get("/onboarding/flow", headers=HEADERS)
    client.post("/onboarding", headers=HEADERS)
    assert list(workdir.iterdir()) == []
    assert not [name for name in _tables(db_path) if name.startswith("onboarding_") or name == "wallets"]


@pytest.mark.parametrize("method, path, body", NEW_ROUTES)
def test_sin_flujo_las_rutas_nuevas_responden_503(store, provider, clock, make_settings, method, path, body):
    # Diseño 3.3 / sección 5: 503 ONBOARDING_NOT_CONFIGURED
    client = _client_without_flow(store, provider, clock, make_settings)
    response = client.request(method, path, headers=HEADERS, json=body)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ONBOARDING_NOT_CONFIGURED"


@pytest.mark.parametrize("path", ANALYTICS_ROUTES)
def test_sin_flujo_la_salida_analitica_tambien_responde_503(store, provider, clock, make_settings, path):
    client = _client_without_flow(store, provider, clock, make_settings, analytics_token=TOKEN)
    response = client.get(path, headers={"X-Analytics-Token": TOKEN})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ONBOARDING_NOT_CONFIGURED"


def test_sin_flujo_las_rutas_de_pagos_siguen_igual(client):
    # Regresión HU-IDEM / principio 18: contratos existentes protegidos
    body = {"intent_id": "intent-1", "amount_cents": 100, "recipient": "merchant-demo", "channel": "merchant-demo"}
    first = client.post("/payments", json=body, headers=HEADERS)
    second = client.post("/payments", json=body, headers=HEADERS)
    assert (first.status_code, second.status_code) == (202, 200)
    assert client.get("/idempotency/requests", headers=HEADERS).status_code == 200


def test_con_flujo_por_parametro_se_montan_servicios_y_rutas(onb_client):
    services = onb_client.app.state.services
    assert services.onboarding is not None
    assert services.wallet_access is not None
    assert services.onboarding_analytics is not None
    assert onb_client.get("/onboarding/flow", headers=HEADERS).status_code == 200


def test_con_flujo_el_almacen_por_defecto_usa_el_mismo_archivo_sqlite(onb_client, db_path):
    # Diseño 3.3: SqliteOnboardingStore(settings.db_path, clock): mismo archivo, tablas propias
    tables = _tables(db_path)
    assert {"payment_attempts", "onboarding_sessions", "onboarding_step_progress", "onboarding_events",
            "wallets"} <= tables


def test_con_flujo_las_rutas_de_pagos_siguen_igual_y_no_exigen_wallet_activa(onb_client, provider):
    # Decisión Q-1: POST /payments no se condiciona a wallet activo en este cambio
    body = {"intent_id": "intent-1", "amount_cents": 100, "recipient": "merchant-demo", "channel": "merchant-demo"}
    response = onb_client.post("/payments", json=body, headers={"X-Payer-Id": "TEST-sin-onboarding"})
    assert response.status_code == 202
    assert len(provider.submit_calls) == 1


def test_el_flujo_se_carga_desde_steps_config_path_al_iniciar(store, provider, clock, make_settings, tests_data_dir):
    # Diseño 3.3: onboarding habilitado si settings.onboarding.steps_config_path no está vacío
    path = str(tests_data_dir / "onboarding-flow-alternate.json")
    client = _client_without_flow(store, provider, clock, make_settings, steps_config_path=path)
    assert client.app.state.services.onboarding is not None
    body = client.get("/onboarding/flow", headers=HEADERS).json()
    assert body["flow_id"] == "onboarding-alterno"
    assert [step["id"] for step in body["steps"]] == ["bienvenida", "perfil"]


@pytest.mark.parametrize("content", ["{no es json", json.dumps({"schema_version": 2}), json.dumps([])])
def test_configuracion_invalida_detiene_el_arranque_con_flow_config_error(tmp_path, store, provider, clock,
                                                                         make_settings, content):
    # Diseño 3.3: configuración inválida detiene el arranque
    from app.errors import FlowConfigError

    broken = tmp_path / "pasos-rotos.json"
    broken.write_text(content, encoding="utf-8")
    with pytest.raises(FlowConfigError):
        _client_without_flow(store, provider, clock, make_settings, steps_config_path=str(broken))


def test_un_almacen_de_onboarding_inyectado_se_usa_en_lugar_del_por_defecto(tmp_path, store, db_path, provider, clock,
                                                                         make_settings, example_flow):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    other_path = str(tmp_path / "onboarding-aparte.sqlite3")
    injected = SqliteOnboardingStore(other_path, clock=clock)
    settings = make_settings(db_path=db_path)
    app = create_app(settings=settings, provider=provider, store=store, clock=clock, onboarding_flow=example_flow,
                     onboarding_store=injected)
    response = TestClient(app).post("/onboarding", headers=HEADERS)
    assert response.status_code == 201
    assert injected.get_session_by_user("TEST-user-1") is not None
    assert "onboarding_sessions" not in _tables(db_path)
