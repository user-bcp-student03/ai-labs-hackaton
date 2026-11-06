"""Aceptación HTTP de la confirmación de pagos de bajo monto del pagador (tareas 3.3, 4.4, 5.1, 5.3, 5.5, 6.3, 7.3)."""
import pytest
from fastapi.testclient import TestClient

H = {"X-Payer-Id": "TEST-payer-1"}
BODY = {"intent_id": "intent-1", "amount_cents": 100, "recipient": "merchant-demo", "channel": "merchant-demo"}
OPEN = {"recipient": "merchant-demo", "amount_cents": 100, "channel": "merchant-demo"}


@pytest.fixture
def make_client(store, provider, clock, make_settings):
    def _make(**settings_overrides):
        from app.main import create_app

        return TestClient(create_app(settings=make_settings(**settings_overrides), provider=provider,
                                     store=store, clock=clock))

    return _make


def _post(client, body=BODY, **headers):
    return client.post("/payments", json=body, headers={**H, **headers})


def test_resumen_previo_a_la_confirmacion_con_destino_monto_e_intencion(client):
    # Escenario: Se muestran destino y monto
    response = client.post("/payments/confirmations", json=OPEN, headers=H)
    body = response.json()
    assert response.status_code == 200
    assert body["can_confirm"] is True
    assert (body["recipient"], body["amount_cents"]) == ("merchant-demo", 100)
    assert body["intent_id"].startswith("intent-")


@pytest.mark.parametrize("faltante", ["recipient", "amount_cents"])
def test_sin_datos_del_destino_o_monto_no_se_habilita_y_se_ofrece_volver(client, faltante):
    # Escenario: No se permite confirmar sin datos del destino
    body = client.post("/payments/confirmations", json={k: v for k, v in OPEN.items() if k != faltante},
                       headers=H).json()
    assert body["can_confirm"] is False
    assert body["intent_id"] is None
    assert [a["id"] for a in body["actions"]] == ["back"]
    assert body["message"]


def test_confirmacion_exige_identidad_y_canal_valido(client):
    assert client.post("/payments/confirmations", json=OPEN).status_code == 401
    assert client.post("/payments/confirmations", json={**OPEN, "channel": "No Válido!"}, headers=H).status_code == 422


def test_monto_sobre_el_limite_se_informa_antes_del_envio(make_client, provider):
    # Escenario: Monto por encima del límite del proveedor
    client = make_client(amount_limits_cents_by_channel={"merchant-demo": 5000})
    opened = client.post("/payments/confirmations", json={**OPEN, "amount_cents": 5001}, headers=H).json()
    assert opened["can_confirm"] is False
    assert opened["limit_cents"] == 5000
    assert "S/ 50.00" in opened["message"]
    sent = _post(client, {**BODY, "amount_cents": 5001})
    assert sent.status_code == 422
    assert sent.json()["detail"]["limit_cents"] == 5000
    assert "S/ 50.00" in sent.json()["detail"]["message"]
    assert provider.submit_calls == []


def test_monto_dentro_del_limite_continua(make_client):
    client = make_client(amount_limits_cents_by_channel={"merchant-demo": 5000})
    assert client.post("/payments/confirmations", json={**OPEN, "amount_cents": 5000}, headers=H).json()["can_confirm"]
    assert _post(client, {**BODY, "amount_cents": 5000}).status_code == 202


def test_estado_en_proceso_y_resultados_terminales_con_etiquetas_distintas(client, provider, clock):
    # Escenarios: Estado pendiente / Un solo resultado terminal / Estados distinguibles
    provider.program("PENDING")
    pendiente = _post(client).json()
    assert (pendiente["status"], pendiente["status_label"], pendiente["actions"]) == ("PENDING", "En proceso", [])
    provider.program("SUCCEEDED")
    exitoso = _post(client, {**BODY, "intent_id": "intent-2", "amount_cents": 200}).json()
    provider.program("REJECTED")
    fallido = _post(client, {**BODY, "intent_id": "intent-3", "amount_cents": 300}).json()
    clock.advance(seconds=121)
    expirado = client.get(f"/payments/{pendiente['payment_id']}", headers=H).json()
    assert expirado["status"] == "EXPIRED"
    etiquetas = {p["status_label"] for p in (exitoso, fallido, expirado)}
    assert len(etiquetas) == 3


def test_resultado_terminal_no_cambia_con_consultas_posteriores(client, provider):
    provider.program("REJECTED")
    created = _post(client).json()
    provider.resolve_status = "SUCCEEDED"
    again = client.get(f"/payments/{created['payment_id']}", headers=H).json()
    assert again["status"] == "FAILED"


@pytest.mark.parametrize("estado", ["REJECTED", "EXPIRADO"])
def test_tras_fallo_o_expiracion_solo_reintentar_y_volver(client, provider, clock, estado):
    # Escenarios: Pago fallido / Pago expirado
    if estado == "REJECTED":
        provider.program("REJECTED")
        pago = _post(client).json()
    else:
        provider.program("PENDING")
        pago = _post(client).json()
        clock.advance(seconds=121)
        pago = client.get(f"/payments/{pago['payment_id']}", headers=H).json()
    assert [a["id"] for a in pago["actions"]] == ["retry", "back"]
    assert [a["label"] for a in pago["actions"]] == ["Reintentar", "Volver"]


def test_referencia_se_muestra_en_exito_y_coincide_con_el_historial(client, provider):
    # Escenarios: Pago exitoso / Consulta posterior en el historial
    provider.program("REJECTED")
    fallido = _post(client, {**BODY, "intent_id": "intent-f", "amount_cents": 50}).json()
    assert fallido["transaction_reference"] is None
    exitoso = _post(client).json()
    assert exitoso["transaction_reference"]
    historial = client.get("/payments", headers=H).json()
    por_pago = {item["payment_id"]: item for item in historial}
    assert por_pago[exitoso["payment_id"]]["transaction_reference"] == exitoso["transaction_reference"]
    assert por_pago[fallido["payment_id"]]["transaction_reference"] is None
    assert por_pago[exitoso["payment_id"]]["status"] == "SUCCEEDED"


def test_historial_es_solo_del_pagador_autenticado(client):
    _post(client)
    assert client.get("/payments", headers={"X-Payer-Id": "TEST-payer-2"}).json() == []


def test_doble_toque_y_perdida_de_conexion_un_solo_cobro_y_resultado_original(client, provider):
    # Escenario: Repetición de la misma confirmación
    primero = _post(client).json()
    repetido = _post(client)
    assert repetido.status_code == 200
    assert repetido.json()["payment_id"] == primero["payment_id"]
    assert repetido.json()["status"] == primero["status"]
    assert len(provider.submit_calls) == 1


def test_reintentar_crea_nuevo_intento_y_la_clave_original_conserva_su_resultado(client, provider):
    # Escenarios: Reintentar crea un nuevo intento vinculado / La clave original conserva el resultado original
    provider.program("REJECTED")
    original = _post(client).json()
    retry = client.post(f"/payments/{original['payment_id']}/retries", headers=H)
    assert retry.status_code == 202
    assert retry.json()["retry_of"] == original["payment_id"]
    assert retry.json()["payment_id"] != original["payment_id"]
    assert retry.json()["idempotency_key"] != original["idempotency_key"]
    repetido = _post(client).json()
    assert (repetido["payment_id"], repetido["status"]) == (original["payment_id"], "FAILED")
    detalle = client.get(f"/payments/{original['payment_id']}", headers=H).json()
    assert detalle["status"] == "FAILED"
    assert detalle["retried_by"] == [retry.json()["payment_id"]]
    assert len(provider.submit_calls) == 2


def test_bloqueo_con_mensaje_accionable_y_fin_del_bloqueo(client, provider, clock):
    # Escenarios: Mensaje accionable durante el bloqueo / Fin del bloqueo al llegar a un estado terminal
    provider.program("PENDING")
    previo = _post(client).json()
    abierta = client.post("/payments/confirmations", json=OPEN, headers=H).json()
    assert abierta["can_confirm"] is False
    assert abierta["reason"] == "previous_attempt_in_progress"
    assert [(a["id"], a["payment_id"]) for a in abierta["actions"]] == [
        ("view_previous", previo["payment_id"]), ("back", None)]
    assert abierta["actions"][0]["label"] == "Ver estado del pago anterior"

    nuevo = _post(client, {**BODY, "intent_id": "intent-nuevo"})
    assert nuevo.status_code == 409
    assert nuevo.json()["detail"]["code"] == "previous_attempt_in_progress"
    assert nuevo.json()["detail"]["previous_payment_id"] == previo["payment_id"]
    assert len(provider.submit_calls) == 1
    assert len(client.get("/payments", headers=H).json()) == 1

    repeticion = _post(client)
    assert repeticion.status_code == 200
    assert repeticion.json()["payment_id"] == previo["payment_id"]

    clock.advance(seconds=121)
    assert client.post("/payments/confirmations", json=OPEN, headers=H).json()["can_confirm"] is True
    retry = client.post(f"/payments/{previo['payment_id']}/retries", headers=H)
    assert retry.status_code == 202


def test_retry_sobre_intento_en_proceso_sigue_siendo_409(client, provider):
    provider.program("PENDING")
    created = _post(client).json()
    assert client.post(f"/payments/{created['payment_id']}/retries", headers=H).status_code == 409


def test_abandono_de_la_confirmacion_se_registra_para_el_reporte(client):
    opened = client.post("/payments/confirmations", json=OPEN, headers=H).json()
    assert client.post(f"/payments/confirmations/{opened['intent_id']}/abandon", headers=H).status_code == 204
    assert client.post("/payments/confirmations/intent-desconocido/abandon", headers=H).status_code == 404
    assert client.post(f"/payments/confirmations/{opened['intent_id']}/abandon",
                       headers={"X-Payer-Id": "TEST-payer-2"}).status_code == 404
    assert client.get("/analytics/checkout-funnel", headers=H).json()["abandoned"] == 1


def test_reporte_de_embudo_y_conteo_mensual_por_http(client, provider):
    # Escenarios: Reporte de caída en checkout / Conteo mensual de pagadores activos
    for monto in (100, 200):
        opened = client.post("/payments/confirmations", json={**OPEN, "amount_cents": monto}, headers=H).json()
        _post(client, {**BODY, "intent_id": opened["intent_id"], "amount_cents": monto})
    funnel = client.get("/analytics/checkout-funnel", params={"baseline_pct": 30, "target_pct": 8}, headers=H).json()
    assert (funnel["started"], funnel["final_confirmations"], funnel["succeeded"]) == (2, 2, 2)
    assert (funnel["baseline_pct"], funnel["target_pct"]) == (30.0, 8.0)
    mensual = client.get("/analytics/active-payers", params={"month": "2026-11"}, headers=H).json()
    assert mensual["active_payers"] == 1
    assert (mensual["reference_min"], mensual["reference_max"]) == (1000, 2000)
    assert mensual["within_reference_range"] is False
    assert client.get("/analytics/active-payers", params={"month": "2026-13"}, headers=H).status_code == 422
    assert client.get("/analytics/checkout-funnel").status_code == 401
