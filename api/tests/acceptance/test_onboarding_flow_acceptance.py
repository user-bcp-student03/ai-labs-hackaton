"""Aceptación HTTP del onboarding y recorrido de extremo a extremo (tarea 7.1; diseño secciones 5, 6, 8 y 9).
Proveedor de pagos doble; SQLite real. Contrato HTTP asumido: ver qe-test-evidence.md (OnboardingView, FlowView, errores)."""
import pytest

USER = "TEST-user-1"
OTHER = "TEST-user-2"
TOKEN = "TEST-analytics-token"
FIELD_KEYS = {"name", "type", "label", "required"}  # hint, max_length, autocomplete e input_mode son opcionales
VIEW_KEYS = {"onboarding_id", "status", "cohort", "wallet_status", "current_step_id", "steps", "completed_steps",
             "total_steps"}


def H(user=USER):
    return {"X-Payer-Id": user}


def _start(client, user=USER):
    return client.post("/onboarding", headers=H(user))


def _put(client, onboarding_id, step_id, values, user=USER):
    return client.put(f"/onboarding/{onboarding_id}/steps/{step_id}", json={"values": values}, headers=H(user))


def _close(client, onboarding_id, user=USER):
    return client.post(f"/onboarding/{onboarding_id}/close", headers=H(user))


def _statuses(view):
    return [(step["id"], step["status"]) for step in view["steps"]]


def _complete_all(client, valid_values, user=USER, clock=None, minutes=0, close=True):
    view = _start(client, user).json()
    for step in view["steps"]:
        if clock is not None:
            clock.advance(minutes=minutes)
        view = _put(client, view["onboarding_id"], step["id"], valid_values[step["id"]], user).json()
    if close:
        if clock is not None:
            clock.advance(minutes=minutes)
        view = _close(client, view["onboarding_id"], user).json()
    return view


# --- GET /onboarding/flow ---------------------------------------------------------------------------------------

def test_flow_publica_la_configuracion_y_la_etiqueta_de_ejemplo(onb_client, example_flow):
    # Req. Los pasos de ejemplo no son requisitos regulatorios; Los pasos provienen de configuración (2.1)
    response = onb_client.get("/onboarding/flow", headers=H())
    assert response.status_code == 200
    body = response.json()
    assert body["flow_id"] == example_flow.flow_id
    assert body["approval_status"] == "example_not_approved"
    assert body["label"] == example_flow.label
    assert [s["id"] for s in body["steps"]] == ["datos-personales", "contacto", "aceptacion"]
    assert [s["order"] for s in body["steps"]] == [1, 2, 3]
    fields = {f["name"]: f for s in body["steps"] for f in s["fields"]}
    assert all(set(f) >= FIELD_KEYS for f in fields.values())
    assert fields["document_number"]["required"] is True
    assert fields["document_number"]["max_length"] == 25
    assert fields["phone"]["autocomplete"] == "tel-national"
    assert fields["phone"]["input_mode"] == "tel"
    assert fields["accept_terms"]["type"] == "checkbox"


def test_flow_no_expone_patrones_ni_mensajes_de_reglas(onb_client):
    # Sección 5: FlowView no expone patrones ni mensajes de reglas (el servidor es autoritativo, D-6)
    text = onb_client.get("/onboarding/flow", headers=H()).text
    for fragment in ("TEST-[A-Za-z0-9]", "9[0-9]{8}", "rules", "pattern", "required_message",
                     "Escribe el documento de prueba con el formato"):
        assert fragment not in text, fragment


def test_flow_cambia_con_la_configuracion_sin_cambiar_el_contrato(make_onb_client, alternate_flow):
    # Req. Cambiar la configuración cambia los pasos sin cambiar el comportamiento
    body = make_onb_client(flow=alternate_flow).get("/onboarding/flow", headers=H()).json()
    assert body["flow_id"] == "onboarding-alterno"
    assert [s["id"] for s in body["steps"]] == ["bienvenida", "perfil"]
    assert set(body) >= {"flow_id", "approval_status", "label", "steps"}


# --- Identidad y no ingestión de eventos ------------------------------------------------------------------------

@pytest.mark.parametrize("method, path, body", [
    ("POST", "/onboarding", None),
    ("GET", "/onboarding/current", None),
    ("PUT", "/onboarding/ob_x/steps/datos-personales", {"values": {}}),
    ("POST", "/onboarding/ob_x/close", None),
    ("GET", "/wallet", None),
    ("GET", "/wallet/payments-entry", None),
])
def test_sin_identidad_se_responde_401(onb_client, method, path, body):
    # Decisión P-3 / principio 17: la identidad viene de X-Payer-Id
    assert onb_client.request(method, path, json=body).status_code == 401


@pytest.mark.parametrize("path", ["/onboarding/events", "/analytics/onboarding/events"])
def test_el_cliente_no_puede_enviar_eventos(onb_client, path):
    # Decisión D-7: los eventos los emite el servidor; no hay endpoint de ingestión
    assert onb_client.post(path, json={"event_type": "onboarding_closed"}, headers=H()).status_code in (404, 405)


# --- Inicio, paso actual y progreso -----------------------------------------------------------------------------

def test_current_sin_onboarding_responde_404(onb_client):
    response = onb_client.get("/onboarding/current", headers=H())
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ONBOARDING_NOT_FOUND"


def test_inicio_responde_201_con_la_secuencia_y_el_primer_paso_actual(onb_client):
    # Req. Se muestra la secuencia al iniciar
    response = _start(onb_client)
    assert response.status_code == 201
    view = response.json()
    assert set(view) >= VIEW_KEYS
    assert view["status"] == "IN_PROGRESS"
    assert view["cohort"] == "MVP-PE"
    assert view["wallet_status"] == "pendiente"
    assert view["current_step_id"] == "datos-personales"
    assert (view["completed_steps"], view["total_steps"]) == (0, 3)
    assert _statuses(view) == [("datos-personales", "current"), ("contacto", "pending"), ("aceptacion", "pending")]
    assert all({"id", "order", "title", "status"} <= set(step) for step in view["steps"])


def test_iniciar_otra_vez_reanuda_con_200_y_el_mismo_id(onb_client, valid_values):
    # Decisión Q-11
    first = _start(onb_client).json()
    _put(onb_client, first["onboarding_id"], "datos-personales", valid_values["datos-personales"])
    again = _start(onb_client)
    assert again.status_code == 200
    assert again.json()["onboarding_id"] == first["onboarding_id"]
    assert again.json()["current_step_id"] == "contacto"
    assert onb_client.get("/onboarding/current", headers=H()).json() == again.json()


def test_cada_usuario_tiene_su_propia_sesion(onb_client):
    assert _start(onb_client, USER).json()["onboarding_id"] != _start(onb_client, OTHER).json()["onboarding_id"]


def test_el_paso_actual_avanza_al_completar_un_paso(onb_client, valid_values):
    # Req. El paso actual se actualiza al avanzar
    oid = _start(onb_client).json()["onboarding_id"]
    response = _put(onb_client, oid, "datos-personales", valid_values["datos-personales"])
    assert response.status_code == 200
    view = response.json()
    assert _statuses(view) == [("datos-personales", "completed"), ("contacto", "current"), ("aceptacion", "pending")]
    assert (view["completed_steps"], view["current_step_id"]) == (1, "contacto")


# --- Validación bloqueante --------------------------------------------------------------------------------------

def test_dato_obligatorio_faltante_responde_422_con_mensaje_accionable_y_no_avanza(onb_client, events_of):
    # Req. Falta información obligatoria; tarea 3.1
    before = _start(onb_client).json()
    response = _put(onb_client, before["onboarding_id"], "datos-personales", {"document_number": "TEST-12345"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "STEP_VALIDATION_FAILED"
    assert detail["errors"] == [
        {"field": "full_name", "rule": "required", "message": "Escribe tu nombre completo."}]
    assert onb_client.get("/onboarding/current", headers=H()).json() == before  # el paso actual no cambia
    assert [e["event_type"] for e in events_of()] == ["onboarding_started"]


def test_dato_invalido_responde_422_con_el_mensaje_de_la_regla(onb_client):
    # Req. Datos inválidos
    oid = _start(onb_client).json()["onboarding_id"]
    response = _put(onb_client, oid, "datos-personales", {"full_name": "Ana Torres", "document_number": "12345"})
    assert response.status_code == 422
    assert response.json()["detail"]["errors"] == [{
        "field": "document_number", "rule": "pattern",
        "message": "Escribe el documento de prueba con el formato TEST-12345."}]


def test_la_respuesta_de_error_no_refleja_el_valor_enviado(onb_client):
    # Sección 5 / tarea 3.2: mensajes estáticos que nunca reflejan valores enviados
    oid = _start(onb_client).json()["onboarding_id"]
    submitted = "ZZZ-valor-privado-77"
    response = _put(onb_client, oid, "datos-personales", {"full_name": "Ana Torres", "document_number": submitted})
    assert response.status_code == 422
    assert submitted not in response.text


def test_corregir_y_reenviar_permite_avanzar(onb_client, valid_values):
    # Req. Se corrige y se permite avanzar
    oid = _start(onb_client).json()["onboarding_id"]
    assert _put(onb_client, oid, "datos-personales", {"full_name": "", "document_number": "x"}).status_code == 422
    assert _put(onb_client, oid, "datos-personales", valid_values["datos-personales"]).status_code == 200


def test_paso_fuera_de_orden_responde_409(onb_client, valid_values):
    oid = _start(onb_client).json()["onboarding_id"]
    response = _put(onb_client, oid, "contacto", valid_values["contacto"])
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "STEP_NOT_CURRENT"


def test_paso_inexistente_responde_404(onb_client):
    oid = _start(onb_client).json()["onboarding_id"]
    response = _put(onb_client, oid, "no-existe", {"a": "b"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "STEP_NOT_FOUND"


def test_onboarding_ajeno_e_inexistente_responden_igual_404(onb_client, valid_values):
    # Sección 5: propiedad por user_id sin enumeración
    mine = _start(onb_client, USER).json()["onboarding_id"]
    foreign = _put(onb_client, mine, "datos-personales", valid_values["datos-personales"], user=OTHER)
    missing = _put(onb_client, "ob_inexistente", "datos-personales", valid_values["datos-personales"], user=OTHER)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    assert foreign.json()["detail"]["code"] == "ONBOARDING_NOT_FOUND"
    assert _close(onb_client, mine, user=OTHER).status_code == 404
    assert onb_client.get("/onboarding/current", headers=H(USER)).json()["completed_steps"] == 0


def test_reenviar_un_paso_completado_es_200_idempotente(onb_client, valid_values, events_of):
    # Decisión Q-7 / tarea 5.2
    oid = _start(onb_client).json()["onboarding_id"]
    first = _put(onb_client, oid, "datos-personales", valid_values["datos-personales"])
    second = _put(onb_client, oid, "datos-personales", valid_values["datos-personales"])
    assert (first.status_code, second.status_code) == (200, 200)
    assert first.json() == second.json()
    assert len([e for e in events_of() if e["event_type"] == "onboarding_step_completed"]) == 1


# --- Cierre, wallet y acceso a pagos ----------------------------------------------------------------------------

def test_cierre_incompleto_responde_409_con_pasos_pendientes_y_wallet_sigue_pendiente(onb_client, valid_values,
                                                                                    events_of):
    # Req. Onboarding incompleto / La wallet no pasa a activo mientras el onboarding no finalice
    oid = _start(onb_client).json()["onboarding_id"]
    _put(onb_client, oid, "datos-personales", valid_values["datos-personales"])
    response = _close(onb_client, oid)
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "ONBOARDING_INCOMPLETE"
    assert detail["pending_step_ids"] == ["contacto", "aceptacion"]
    assert onb_client.get("/wallet", headers=H()).json()["status"] == "pendiente"
    assert "onboarding_closed" not in {e["event_type"] for e in events_of()}


def test_cierre_correcto_activa_la_wallet_y_repetirlo_es_idempotente(onb_client, valid_values, events_of):
    # Req. Onboarding finalizado correctamente; tarea 4.1
    view = _complete_all(onb_client, valid_values, close=False)
    first = _close(onb_client, view["onboarding_id"])
    assert first.status_code == 200
    assert (first.json()["status"], first.json()["wallet_status"]) == ("COMPLETED", "activo")
    second = _close(onb_client, view["onboarding_id"])
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len([e for e in events_of() if e["event_type"] == "onboarding_closed"]) == 1


def test_wallet_404_sin_onboarding_pendiente_al_iniciar_y_activa_al_cerrar(onb_client, valid_values):
    # Sección 5: GET /wallet
    assert onb_client.get("/wallet", headers=H()).status_code == 404
    _start(onb_client)
    pending = onb_client.get("/wallet", headers=H())
    assert pending.status_code == 200
    assert pending.json() == {"status": "pendiente", "activated_at": None}
    _complete_all(onb_client, valid_values)
    active = onb_client.get("/wallet", headers=H()).json()
    assert active["status"] == "activo"
    assert active["activated_at"] is not None


def test_acceso_a_pagos_denegado_sin_wallet_o_con_wallet_pendiente(onb_client):
    # Req. Onboarding incompleto (sin acceso) / tarea 4.2 denegado
    for stage in ("sin-onboarding", "pendiente"):
        if stage == "pendiente":
            _start(onb_client)
        response = onb_client.get("/wallet/payments-entry", headers=H())
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert detail["code"] == "WALLET_NOT_ACTIVE"
        assert detail["next_action"] == "complete_onboarding"


def test_acceso_a_pagos_permitido_con_wallet_activa(onb_client, valid_values):
    # Req. Acceso al punto de entrada de pagos de bajo monto; tarea 4.2 permitido
    _complete_all(onb_client, valid_values)
    response = onb_client.get("/wallet/payments-entry", headers=H())
    assert response.status_code == 200
    assert response.json() == {"allowed": True}


def test_el_acceso_a_pagos_es_por_identidad(onb_client, valid_values):
    # Principio 17: la wallet activa de un usuario no habilita a otro
    _complete_all(onb_client, valid_values, user=USER)
    assert onb_client.get("/wallet/payments-entry", headers=H(OTHER)).status_code == 403


# --- Recorrido de extremo a extremo (tarea 7.1) -----------------------------------------------------------------

def test_recorrido_completo_inicio_error_correccion_cierre_activo_y_acceso_a_pagos(onb_client, valid_values, clock,
                                                                                   events_of):
    # Tarea 7.1: inicio -> error -> corrección -> pasos -> cierre -> wallet activo -> acceso; eventos coherentes
    view = _start(onb_client).json()
    oid = view["onboarding_id"]
    assert onb_client.get("/wallet/payments-entry", headers=H()).status_code == 403

    clock.advance(minutes=1)
    assert _put(onb_client, oid, "datos-personales", {"full_name": "Ana Torres", "document_number": "mal"}
                ).status_code == 422
    clock.advance(minutes=1)
    assert _put(onb_client, oid, "datos-personales", valid_values["datos-personales"]).status_code == 200
    clock.advance(minutes=1)
    assert _put(onb_client, oid, "contacto", valid_values["contacto"]).status_code == 200
    assert _close(onb_client, oid).status_code == 409  # aún falta 'aceptacion'
    clock.advance(minutes=1)
    last = _put(onb_client, oid, "aceptacion", valid_values["aceptacion"]).json()
    assert last["current_step_id"] is None
    assert last["wallet_status"] == "pendiente"
    clock.advance(minutes=1)
    closed = _close(onb_client, oid).json()
    assert (closed["status"], closed["wallet_status"]) == ("COMPLETED", "activo")

    assert onb_client.get("/wallet", headers=H()).json()["status"] == "activo"
    assert onb_client.get("/wallet/payments-entry", headers=H()).json() == {"allowed": True}

    events = events_of(oid)
    assert [(e["event_type"], e["step_id"]) for e in events] == [
        ("onboarding_started", ""), ("onboarding_step_completed", "datos-personales"),
        ("onboarding_step_completed", "contacto"), ("onboarding_step_completed", "aceptacion"),
        ("onboarding_closed", "")]
    assert {e["cohort"] for e in events} == {"MVP-PE"}
    assert [e["occurred_at"] for e in events] == sorted(e["occurred_at"] for e in events)


def test_recorrido_completo_con_la_configuracion_alterna(make_onb_client, alternate_flow, valid_values):
    # Req. Cambiar la configuración cambia los pasos sin cambiar el comportamiento (mismo recorrido por HTTP)
    client = make_onb_client(flow=alternate_flow)
    assert client.get("/wallet/payments-entry", headers=H()).status_code == 403
    view = _complete_all(client, valid_values)
    assert (view["status"], view["wallet_status"], view["total_steps"]) == ("COMPLETED", "activo", 2)
    assert client.get("/wallet/payments-entry", headers=H()).status_code == 200


# --- Salida analítica (X-Analytics-Token) -----------------------------------------------------------------------

MONTHLY = "/analytics/onboarding/monthly"
DURATION = "/analytics/onboarding/duration"


@pytest.mark.parametrize("path", [MONTHLY, DURATION])
def test_analitica_cerrada_por_defecto_sin_token_configurado_responde_404(make_onb_client, path):
    # Decisión Q-4: sin ONB_ANALYTICS_TOKEN la salida está deshabilitada
    client = make_onb_client(analytics_token="")
    assert client.get(path, params={"month": "2026-11"}, headers={"X-Analytics-Token": TOKEN}).status_code == 404
    assert client.get(path, params={"month": "2026-11"}).status_code == 404


@pytest.mark.parametrize("path", [MONTHLY, DURATION])
@pytest.mark.parametrize("headers", [{"X-Analytics-Token": "TEST-incorrecto"}, {}, {"X-Analytics-Token": ""}])
def test_analitica_con_token_incorrecto_o_ausente_responde_401(onb_client, path, headers):
    assert onb_client.get(path, params={"month": "2026-11"}, headers=headers).status_code == 401


@pytest.mark.parametrize("path", [MONTHLY, DURATION])
@pytest.mark.parametrize("month", ["2026-13", "noviembre", "2026-1"])
def test_analitica_con_mes_invalido_responde_422(onb_client, path, month):
    assert onb_client.get(path, params={"month": month}, headers={"X-Analytics-Token": TOKEN}).status_code == 422


def test_salida_mensual_cuenta_el_usuario_activo_y_declara_el_gasto_no_disponible(onb_client, valid_values):
    # Req. Salida analítica: Campos de la salida mensual / Conteo mensual / Mes sin gasto disponible
    _complete_all(onb_client, valid_values, user=USER)
    _start(onb_client, OTHER)  # inició pero no finalizó: no cuenta
    response = onb_client.get(MONTHLY, params={"month": "2026-11"}, headers={"X-Analytics-Token": TOKEN})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"month", "cohort", "new_active_users", "acquisition_spend", "reference",
                         "pending_definitions"}
    assert (body["month"], body["cohort"], body["new_active_users"]) == ("2026-11", "MVP-PE", 1)
    assert body["acquisition_spend"] == {"status": "unavailable", "amount_pen_cents": None}
    assert body["reference"] == {"mau_min": 1000, "mau_max": 2000, "cac_target_pen_cents": 1000}
    assert body["pending_definitions"] == ["OQ-05", "OQ-22"]
    other_month = onb_client.get(MONTHLY, params={"month": "2026-12"}, headers={"X-Analytics-Token": TOKEN})
    assert other_month.json()["new_active_users"] == 0


def test_la_salida_analitica_no_exige_identidad_de_pagador(onb_client):
    # Los agregados no llevan datos personales; el acceso lo controla solo el token (sección 9.3)
    response = onb_client.get(MONTHLY, params={"month": "2026-11"}, headers={"X-Analytics-Token": TOKEN})
    assert response.status_code == 200


def test_reporte_de_duracion_por_http_calcula_la_mediana_con_la_frontera_por_defecto(onb_client, valid_values, clock):
    # Req. Reporte periódico de duración; frontera provisional (OQ-20): inicio -> cierre = 4 x 2 min
    _complete_all(onb_client, valid_values, user=USER, clock=clock, minutes=2)
    response = onb_client.get(DURATION, params={"month": "2026-11"}, headers={"X-Analytics-Token": TOKEN})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"month", "cohort", "finished_onboardings", "median_minutes", "reference", "boundary"}
    assert body["finished_onboardings"] == 1
    assert body["median_minutes"] == pytest.approx(8.0)
    assert body["reference"] == {"baseline_minutes": 8, "target_minutes": 3}
    assert body["boundary"] == {"start": "onboarding_started", "end": "onboarding_closed",
                                "status": "provisional_oq20"}


def test_reporte_de_duracion_sin_datos_devuelve_mediana_nula(onb_client):
    body = onb_client.get(DURATION, params={"month": "2026-11"}, headers={"X-Analytics-Token": TOKEN}).json()
    assert (body["finished_onboardings"], body["median_minutes"]) == (0, None)
