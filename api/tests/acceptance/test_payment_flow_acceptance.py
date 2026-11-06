"""Aceptación HTTP (diseño sección 5 y tarea 6.1). Proveedor doble; el mock real se contrasta solo por MCP (P-6)."""
H = {"X-Payer-Id": "TEST-payer-1", "X-Request-Id": "req-a", "X-Correlation-Id": "corr-a"}
BODY = {"intent_id": "intent-1", "amount_cents": 100, "recipient": "merchant-demo", "channel": "merchant-demo"}


def _post(client, body=BODY, **headers):
    return client.post("/payments", json=body, headers={**H, **headers})


def test_post_payments_original_202_y_duplicado_200(client, provider):
    # Req. Solicitud repetida: original 202, duplicado 200 con request_type=duplicate
    first = _post(client)
    second = _post(client, **{"X-Request-Id": "req-b", "X-Correlation-Id": "corr-b"})
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["request_type"] == "duplicate"
    assert second.json()["payment_id"] == first.json()["payment_id"]
    assert len(provider.submit_calls) == 1


def test_identidad_del_pagador_viene_del_encabezado_no_del_cuerpo(client, provider):
    # Decisión P-3: X-Payer-Id manda; un payer_id en el cuerpo no cambia la clave
    a = _post(client, {**BODY, "payer_id": "TEST-otro"})
    b = _post(client, {**BODY}, **{"X-Request-Id": "req-b"})
    assert b.json()["request_type"] == "duplicate"
    assert a.json()["payment_id"] == b.json()["payment_id"]


def test_pago_con_intencion_distinta_es_transaccion_independiente(client, provider):
    # Escenario: Pago legítimo idéntico con otra intención no es duplicado
    _post(client)
    other = _post(client, {**BODY, "intent_id": "intent-2"}, **{"X-Request-Id": "req-b"})
    assert other.status_code == 202
    assert len(provider.submit_calls) == 2


def test_entrada_invalida_422(client):
    # Escenario: identificador de intención obligatorio; validación de entrada (principio 17)
    assert _post(client, {k: v for k, v in BODY.items() if k != "intent_id"}).status_code == 422
    assert _post(client, {**BODY, "amount_cents": 0}).status_code == 422
    assert _post(client, {**BODY, "amount_cents": -5}).status_code == 422


def test_get_payment_devuelve_intento_con_estado_y_clave(client):
    created = _post(client).json()
    got = client.get(f"/payments/{created['payment_id']}", headers=H)
    assert got.status_code == 200
    assert {"status", "idempotency_key", "retry_of"} <= set(got.json())


def test_retry_sobre_intento_pendiente_409(client, provider):
    # Decisión P-5
    provider.program("PENDING")
    created = _post(client).json()
    r = client.post(f"/payments/{created['payment_id']}/retries", headers={**H, "X-Request-Id": "req-r"})
    assert r.status_code == 409


def test_flujo_extremo_a_extremo(client, provider):
    # Tarea 6.1: original, duplicado, reintento vinculado tras fallo, auditoría y feed
    provider.program("REJECTED")
    original = _post(client).json()
    _post(client, **{"X-Request-Id": "req-dup", "X-Correlation-Id": "corr-dup"})
    retry = client.post(f"/payments/{original['payment_id']}/retries",
                        headers={**H, "X-Request-Id": "req-retry", "X-Correlation-Id": "corr-retry"})
    assert retry.status_code == 202
    assert retry.json()["retry_of"] == original["payment_id"]

    feed = client.get("/idempotency/requests", headers=H).json()
    tipos = sorted(r["request_type"] for r in feed)
    assert tipos == ["duplicate", "original", "original"]
    dup = next(r for r in feed if r["request_type"] == "duplicate")
    assert dup["payment_id"] == original["payment_id"]
    assert {"requested_at", "original_requested_at"} <= set(dup)
    assert not [k for k in dup if "report" in k]
    assert len(provider.submit_calls) == 2


def test_feed_filtra_por_clave_correlacion_y_tipo(client):
    orig = _post(client).json()
    _post(client, **{"X-Request-Id": "req-b", "X-Correlation-Id": "corr-b"})
    key = client.get(f"/payments/{orig['payment_id']}", headers=H).json()["idempotency_key"]
    assert len(client.get("/idempotency/requests", params={"idempotency_key": key}, headers=H).json()) == 2
    assert len(client.get("/idempotency/requests", params={"correlation_id": "corr-b"}, headers=H).json()) == 1
    assert len(client.get("/idempotency/requests", params={"request_type": "duplicate"}, headers=H).json()) == 1
