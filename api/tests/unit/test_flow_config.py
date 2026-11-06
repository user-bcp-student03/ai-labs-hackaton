"""Contrato de configuración de pasos (diseño sección 6; tareas 1.7 y 3.2; req. 'Secuencia de pasos' y 'Validación')."""
import dataclasses
import json
from pathlib import Path

import pytest

EXAMPLE_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "onboarding-steps.example.json"


def _text_field(raw):
    return raw["steps"][0]["fields"][0]


def _drop(mapping, key):
    del mapping[key]


INVALID_CONFIGS = {
    "schema_version desconocido": lambda raw: raw.update(schema_version=2),
    "sin schema_version": lambda raw: _drop(raw, "schema_version"),
    "flow_id con formato inválido": lambda raw: raw.update(flow_id="Flujo Inválido!"),
    "sin flow_id": lambda raw: _drop(raw, "flow_id"),
    "approval_status inválido": lambda raw: raw.update(approval_status="aprobado-quizas"),
    "ejemplo sin label": lambda raw: _drop(raw, "label"),
    "sin pasos": lambda raw: raw.update(steps=[]),
    "id de paso repetido": lambda raw: raw["steps"][1].update(id=raw["steps"][0]["id"]),
    "order repetido": lambda raw: raw["steps"][1].update(order=raw["steps"][0]["order"]),
    "order menor que 1": lambda raw: raw["steps"][0].update(order=0),
    "id de paso con formato inválido": lambda raw: raw["steps"][0].update(id="Paso 1"),
    "título vacío": lambda raw: raw["steps"][0].update(title=""),
    "título de más de 80 caracteres": lambda raw: raw["steps"][0].update(title="t" * 81),
    "descripción de más de 300 caracteres": lambda raw: raw["steps"][0].update(description="d" * 301),
    "paso sin campos": lambda raw: raw["steps"][0].update(fields=[]),
    "nombre de campo repetido": lambda raw: raw["steps"][0]["fields"][1].update(
        name=raw["steps"][0]["fields"][0]["name"]),
    "nombre de campo con formato inválido": lambda raw: _text_field(raw).update(name="Nombre-Completo"),
    "tipo de campo fuera del vocabulario": lambda raw: _text_field(raw).update(type="number"),
    "regla fuera del vocabulario": lambda raw: _text_field(raw)["rules"].append(
        {"kind": "range", "value": 1, "message": "Fuera de rango."}),
    "patrón que no compila": lambda raw: _text_field(raw)["rules"][1].update(value="[sin-cerrar"),
    "patrón de más de 200 caracteres": lambda raw: _text_field(raw)["rules"][1].update(value="a" * 201),
    "regla sin mensaje": lambda raw: _drop(_text_field(raw)["rules"][0], "message"),
    "regla con mensaje vacío": lambda raw: _text_field(raw)["rules"][0].update(message=""),
    "campo requerido sin required_message": lambda raw: _drop(_text_field(raw), "required_message"),
    "texto sin max_length": lambda raw: _text_field(raw).update(rules=[_text_field(raw)["rules"][1]]),
    "max_length mayor que 500": lambda raw: _text_field(raw)["rules"][0].update(value=501),
    "valor de longitud no entero": lambda raw: _text_field(raw)["rules"][0].update(value="cien"),
    "reglas en un checkbox": lambda raw: raw["steps"][2]["fields"][0].update(
        rules=[{"kind": "max_length", "value": 1, "message": "No aplica."}]),
    "mensaje con HTML": lambda raw: _text_field(raw)["rules"][0].update(message="<b>Acorta</b> el nombre."),
    "required_message con HTML": lambda raw: _text_field(raw).update(required_message="<script>x</script>"),
}


def test_configuracion_de_ejemplo_se_carga(example_flow):
    # Tarea 1.7: el contrato acepta la configuración de la sección 6.3
    assert example_flow.flow_id == "onboarding-ejemplo"
    assert example_flow.approval_status == "example_not_approved"
    assert [s.id for s in example_flow.steps] == ["datos-personales", "contacto", "aceptacion"]
    assert [s.order for s in example_flow.steps] == [1, 2, 3]
    fields = {f.name: f for s in example_flow.steps for f in s.fields}
    assert fields["full_name"].type == "text" and fields["full_name"].required is True
    assert fields["accept_terms"].type == "checkbox"
    assert [r.kind for r in fields["document_number"].rules] == ["max_length", "pattern"]


def test_los_pasos_se_ordenan_por_order_no_por_posicion(alternate_flow):
    # Req. 'Secuencia de pasos' / Los pasos provienen de configuración: el JSON alterno lista 'perfil' antes
    assert [s.id for s in alternate_flow.steps] == ["bienvenida", "perfil"]
    assert alternate_flow.flow_id == "onboarding-alterno"


def test_definicion_inmutable(example_flow):
    with pytest.raises(dataclasses.FrozenInstanceError):
        example_flow.flow_id = "otro"
    assert isinstance(example_flow.steps, tuple)


def test_load_flow_definition_lee_archivo_json(tests_data_dir):
    from app.services.flow_config import load_flow_definition

    flow = load_flow_definition(str(tests_data_dir / "onboarding-flow-alternate.json"))
    assert flow.approval_status == "example_not_approved"


@pytest.mark.parametrize("name", list(INVALID_CONFIGS))
def test_configuracion_invalida_se_rechaza_al_cargar(example_flow_raw, name):
    # Tarea 1.7: validación explícita al cargar; cualquier incumplimiento detiene el arranque
    from app.errors import FlowConfigError
    from app.services.flow_config import parse_flow_definition

    INVALID_CONFIGS[name](example_flow_raw)
    with pytest.raises(FlowConfigError):
        parse_flow_definition(example_flow_raw)


def test_configuracion_aprobada_no_exige_label(example_flow_raw):
    # Sección 6.1: label obligatorio solo si approval_status != approved
    from app.services.flow_config import parse_flow_definition

    example_flow_raw["approval_status"] = "approved"
    del example_flow_raw["label"]
    assert parse_flow_definition(example_flow_raw).approval_status == "approved"


def test_checkbox_no_requerido_no_exige_required_message(example_flow_raw):
    from app.services.flow_config import parse_flow_definition

    checkbox = example_flow_raw["steps"][2]["fields"][0]
    checkbox["required"] = False
    del checkbox["required_message"]
    assert parse_flow_definition(example_flow_raw).steps[2].fields[0].required is False


def test_archivo_que_no_es_json_se_rechaza(tmp_path):
    from app.errors import FlowConfigError
    from app.services.flow_config import load_flow_definition

    broken = tmp_path / "roto.json"
    broken.write_text("{no es json", encoding="utf-8")
    with pytest.raises(FlowConfigError):
        load_flow_definition(str(broken))


def test_raiz_que_no_es_objeto_se_rechaza(tmp_path):
    from app.errors import FlowConfigError
    from app.services.flow_config import load_flow_definition

    as_list = tmp_path / "lista.json"
    as_list.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(FlowConfigError):
        load_flow_definition(str(as_list))


def test_toda_regla_y_campo_requerido_tienen_mensaje(example_flow, alternate_flow):
    # Tarea 3.2: cada regla y cada 'required' de la configuración lleva un mensaje accionable no vacío
    for flow in (example_flow, alternate_flow):
        for step in flow.steps:
            for field in step.fields:
                if field.required:
                    assert field.required_message and field.required_message.strip()
                for rule in field.rules:
                    assert rule.message and rule.message.strip()


def test_ejemplo_entregado_en_api_config_es_valido_y_esta_etiquetado():
    # Tarea 1.7 / req. 'Los pasos de ejemplo no son requisitos regulatorios' (archivo del desarrollador)
    from app.services.flow_config import load_flow_definition

    flow = load_flow_definition(str(EXAMPLE_CONFIG_PATH))
    assert flow.approval_status == "example_not_approved"
    assert "ejemplo no aprobado" in flow.label.lower()
    assert [s.id for s in flow.steps] == ["datos-personales", "contacto", "aceptacion"]


def test_ejemplo_entregado_cumple_tarea_3_2_mensajes_en_cada_regla():
    # Tarea 3.2 sobre api/config/onboarding-steps.example.json
    from app.services.flow_config import load_flow_definition

    flow = load_flow_definition(str(EXAMPLE_CONFIG_PATH))
    for step in flow.steps:
        for field in step.fields:
            assert (not field.required) or field.required_message
            assert all(rule.message for rule in field.rules)
