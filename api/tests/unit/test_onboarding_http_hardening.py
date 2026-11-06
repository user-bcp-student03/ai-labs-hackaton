"""Endurecimiento del borde HTTP y ramas de guarda de HU-ONB escritas por desarrollo (no sustituyen las de QE).
Cubren lo que el diseño deja abierto (hallazgo H-4 de QE): tipos incorrectos, tamaños y eco de valores."""
import pytest

USER = "TEST-user-1"
HEADERS = {"X-Payer-Id": USER}
SECRET = "ZZZ-valor-privado-77"


def _put(client, onboarding_id, step_id, body):
    return client.put(f"/onboarding/{onboarding_id}/steps/{step_id}", json=body, headers=HEADERS)


@pytest.mark.parametrize("body", [
    {"values": {"full_name": 12345}},
    {"values": {"full_name": None}},
    {"values": {"full_name": ["a"]}},
    {"values": SECRET},
    {"otro": SECRET},
    {"values": {"full_name": SECRET * 200}},
    {"values": {f"campo_{i}": "x" for i in range(51)}},
    {"values": {"x" * 65: SECRET}},
])
def test_cuerpo_con_formato_incorrecto_responde_422_sin_reflejar_lo_enviado(onb_client, body):
    onboarding_id = onb_client.post("/onboarding", headers=HEADERS).json()["onboarding_id"]
    response = _put(onb_client, onboarding_id, "datos-personales", body)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_REQUEST"
    assert SECRET not in response.text


def test_identificador_de_ruta_demasiado_largo_responde_422(onb_client):
    response = _put(onb_client, "ob_" + "x" * 200, "datos-personales", {"values": {}})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_REQUEST"


def test_fuera_de_onboarding_el_422_conserva_el_comportamiento_base(onb_client):
    # Regresión HU-IDEM: el manejador de errores solo se desvía en /onboarding/*
    response = onb_client.post("/payments", json={}, headers=HEADERS)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_un_tipo_inesperado_cuenta_como_dato_faltante(example_flow):
    # Supuesto documentado (H-4): el motor trata un valor que no es texto como vacío
    from app.services.step_engine import validate_step_values

    errors = validate_step_values(example_flow.steps[1], {"phone": True})
    assert [(e.field, e.rule) for e in errors] == [("phone", "required")]


def test_valor_de_tipo_incorrecto_en_checkbox_no_cuenta_como_marcado(example_flow):
    from app.services.step_engine import validate_step_values

    assert [e.rule for e in validate_step_values(example_flow.steps[2], {"accept_terms": "true"})] == ["required"]


@pytest.mark.parametrize("mutate", [
    lambda raw: raw.update(steps={"id": "no-es-lista"}),
    lambda raw: raw["steps"][0]["fields"][0].update(autocomplete="NAME;<x>"),
    lambda raw: raw["steps"][0]["fields"][0].update(input_mode=7),
    lambda raw: raw["steps"][0]["fields"][0].update(required="si"),
    lambda raw: raw["steps"][0].update(fields="no-es-lista"),
    lambda raw: raw["steps"].append("no-es-objeto"),
    lambda raw: raw.update(schema_version=True),
])
def test_configuracion_con_estructura_o_tokens_invalidos_se_rechaza(example_flow_raw, mutate):
    from app.errors import FlowConfigError
    from app.services.flow_config import parse_flow_definition

    mutate(example_flow_raw)
    with pytest.raises(FlowConfigError):
        parse_flow_definition(example_flow_raw)


def test_archivo_de_configuracion_inexistente_se_rechaza(tmp_path):
    from app.errors import FlowConfigError
    from app.services.flow_config import load_flow_definition

    with pytest.raises(FlowConfigError):
        load_flow_definition(str(tmp_path / "no-existe.json"))


def test_el_almacen_no_acepta_dos_sesiones_con_el_mismo_onboarding_id(db_path, clock):
    import sqlite3

    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    store = SqliteOnboardingStore(db_path, clock=clock)
    store.start_onboarding("ob_1", "TEST-user-1", "MVP-PE", "pendiente")
    with pytest.raises(sqlite3.IntegrityError):
        store.start_onboarding("ob_1", "TEST-user-2", "MVP-PE", "pendiente")


def test_cerrar_un_onboarding_inexistente_en_el_almacen_lanza_not_found(db_path, clock):
    from app.errors import OnboardingNotFound
    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    with pytest.raises(OnboardingNotFound):
        SqliteOnboardingStore(db_path, clock=clock).close_onboarding("ob_no")


def test_el_almacen_usa_el_reloj_utc_por_defecto(db_path):
    from datetime import timezone

    from app.repositories.sqlite_onboarding_store import SqliteOnboardingStore

    session = SqliteOnboardingStore(db_path).start_onboarding("ob_1", "TEST-user-1", "MVP-PE", "pendiente").session
    assert session.started_at.tzinfo is not None
    assert session.started_at.utcoffset() == timezone.utc.utcoffset(None)
