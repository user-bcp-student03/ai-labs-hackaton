"""Motor de validación de pasos, función pura (diseño 6.2; req. 'Validación bloqueante con mensaje accionable'; tareas 3.1 y 3.2)."""
import pytest


def _text(name, rules, required=True, **extra):
    field = {"name": name, "type": "text", "label": name, "required": required, "rules": rules}
    if required:
        field["required_message"] = f"Completa {name}."
    field.update(extra)
    return field


def _checkbox(name, required=True):
    field = {"name": name, "type": "checkbox", "label": name, "required": required}
    if required:
        field["required_message"] = f"Marca {name}."
    return field


def _max(value, message="Acorta el texto."):
    return {"kind": "max_length", "value": value, "message": message}


def _pattern(value, message="Usa el formato correcto."):
    return {"kind": "pattern", "value": value, "message": message}


def _step_with(*fields):
    from app.services.flow_config import parse_flow_definition

    raw = {"schema_version": 1, "flow_id": "prueba", "approval_status": "approved",
           "steps": [{"id": "s1", "order": 1, "title": "Paso", "fields": list(fields)}]}
    return parse_flow_definition(raw).steps[0]


def _validate(step, values):
    from app.services.step_engine import validate_step_values

    return validate_step_values(step, values)


def _by_field(errors):
    return {error.field: error for error in errors}


def test_valores_validos_no_producen_errores(example_flow, valid_values):
    # Req. Validación / Se corrige y se permite avanzar
    for step in example_flow.steps:
        assert _validate(step, valid_values[step.id]) == []


def test_dato_obligatorio_faltante_indica_que_dato_y_como_completarlo(example_flow):
    # Req. Validación / Falta información obligatoria
    errors = _validate(example_flow.steps[0], {"document_number": "TEST-12345"})
    assert [(e.field, e.rule, e.message) for e in errors] == [
        ("full_name", "required", "Escribe tu nombre completo.")]


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_texto_vacio_o_solo_espacios_cuenta_como_faltante(example_flow, blank):
    # Req. Validación / Falta información obligatoria (strip antes de validar)
    errors = _validate(example_flow.steps[1], {"phone": blank})
    assert [(e.field, e.rule) for e in errors] == [("phone", "required")]


def test_dato_invalido_por_formato_usa_el_mensaje_configurado(example_flow):
    # Req. Validación / Datos inválidos (pattern)
    errors = _validate(example_flow.steps[0], {"full_name": "Ana Torres", "document_number": "12345"})
    assert [(e.field, e.rule, e.message) for e in errors] == [
        ("document_number", "pattern", "Escribe el documento de prueba con el formato TEST-12345.")]


def test_dato_invalido_por_longitud_usa_el_mensaje_configurado(example_flow):
    # Req. Validación / Datos inválidos (max_length, primera regla del campo)
    errors = _validate(example_flow.steps[0], {"full_name": "Ana Torres", "document_number": "TEST-" + "A" * 30})
    assert [(e.field, e.rule, e.message) for e in errors] == [
        ("document_number", "max_length", "Acorta el documento a 25 caracteres como máximo.")]


def test_patron_se_evalua_con_fullmatch(example_flow):
    # Diseño 6.2 punto 2: pattern con re.fullmatch, no con match ni search
    for value in ("TEST-12345!", "XTEST-12345", "TEST-12345 extra"):
        errors = _validate(example_flow.steps[0], {"full_name": "Ana Torres", "document_number": value})
        assert [e.rule for e in errors] == ["pattern"], value


def test_el_texto_se_recorta_antes_de_validar(example_flow):
    # Diseño 6.2 punto 2: strip(); 9 dígitos con espacios alrededor cumplen max_length 9
    assert _validate(example_flow.steps[1], {"phone": "  912345678  "}) == []


def test_un_solo_error_por_campo_el_de_la_primera_regla_que_falla():
    # Diseño 6.2 punto 2: la primera regla que falla produce un único error por campo
    step = _step_with(_text("alias", [_max(5, "Acorta el alias."), _pattern("[a-z]+", "Solo letras.")]))
    errors = _validate(step, {"alias": "NO-VALIDO-Y-LARGO"})
    assert [(e.field, e.rule, e.message) for e in errors] == [("alias", "max_length", "Acorta el alias.")]


def test_el_orden_de_las_reglas_lo_define_la_configuracion():
    step = _step_with(_text("alias", [_pattern("[a-z]+", "Solo letras."), _max(5, "Acorta el alias.")]))
    errors = _validate(step, {"alias": "NO-VALIDO-Y-LARGO"})
    assert [(e.rule, e.message) for e in errors] == [("pattern", "Solo letras.")]


def test_regla_min_length():
    step = _step_with(_text("clave", [{"kind": "min_length", "value": 4, "message": "Usa al menos 4 caracteres."},
                                      _max(10)]))
    assert [e.rule for e in _validate(step, {"clave": "abc"})] == ["min_length"]
    assert _validate(step, {"clave": "abcd"}) == []


def test_todos_los_errores_del_paso_se_devuelven_juntos(example_flow):
    # Diseño 6.2 punto 3: se responden todos los errores del paso
    errors = _validate(example_flow.steps[0], {"full_name": "", "document_number": "malo"})
    assert set(_by_field(errors)) == {"full_name", "document_number"}
    assert len(errors) == 2


def test_cambiar_la_regla_configurada_cambia_la_validacion_sin_cambiar_el_motor():
    # Req. Validación / Cambiar las reglas configuradas cambia la validación sin cambiar el comportamiento
    permissive = _step_with(_text("alias", [_max(10, "Acorta a 10.")]))
    strict = _step_with(_text("alias", [_max(3, "Acorta a 3 como máximo.")]))
    assert _validate(permissive, {"alias": "abcdef"}) == []
    errors = _validate(strict, {"alias": "abcdef"})
    assert [(e.field, e.rule, e.message) for e in errors] == [("alias", "max_length", "Acorta a 3 como máximo.")]


def test_las_reglas_provienen_de_la_configuracion_no_del_motor(alternate_flow):
    # Req. Validación / Las validaciones provienen de configuración: otro flujo, otras reglas, mismo motor
    profile = alternate_flow.steps[1]
    assert _validate(profile, {"nickname": "ana2026"}) == []
    errors = _validate(profile, {"nickname": "ANA!"})
    assert [(e.field, e.rule) for e in errors] == [("nickname", "pattern")]
    assert errors[0].message == "Usa de 3 a 12 letras minúsculas o números; por ejemplo: ana2026."


def test_checkbox_requerido_exige_estar_marcado(example_flow):
    # Diseño 6.2 punto 2: checkbox requerido y no marcado -> required con required_message
    step = example_flow.steps[2]
    for values in ({}, {"accept_terms": False}):
        errors = _validate(step, values)
        assert [(e.field, e.rule, e.message) for e in errors] == [
            ("accept_terms", "required", "Marca la casilla para aceptar los términos y continuar.")]
    assert _validate(step, {"accept_terms": True}) == []


def test_checkbox_no_requerido_puede_quedar_sin_marcar():
    step = _step_with(_checkbox("newsletter", required=False))
    assert _validate(step, {"newsletter": False}) == []
    assert _validate(step, {}) == []


def test_texto_opcional_vacio_no_evalua_mas_reglas():
    # Diseño 6.2 punto 2: vacío y no requerido -> sin más reglas
    step = _step_with(_text("apodo", [_max(5), {"kind": "min_length", "value": 3, "message": "Mínimo 3."}],
                            required=False))
    assert _validate(step, {}) == []
    assert _validate(step, {"apodo": "  "}) == []
    assert [e.rule for e in _validate(step, {"apodo": "ab"})] == ["min_length"]


def test_campo_desconocido_se_reporta_sin_reflejar_su_valor(example_flow, valid_values):
    # Diseño 6.2 punto 2: unknown_field; los mensajes nunca reflejan valores enviados
    values = {**valid_values["contacto"], "campo_extra": "VALOR-SENSIBLE-999"}
    errors = _validate(example_flow.steps[1], values)
    assert [(e.field, e.rule) for e in errors] == [("campo_extra", "unknown_field")]
    assert "VALOR-SENSIBLE-999" not in errors[0].message


def test_los_mensajes_no_reflejan_el_valor_enviado(example_flow):
    # Tarea 3.2: un valor enviado no aparece en los errores
    submitted = "ZZZ-valor-privado-77"
    errors = _validate(example_flow.steps[0], {"full_name": "Ana Torres", "document_number": submitted})
    assert errors
    assert all(submitted not in f"{e.field}{e.rule}{e.message}" for e in errors)


def test_el_motor_es_puro_no_muta_la_entrada_y_es_determinista(example_flow):
    values = {"full_name": "  Ana Torres ", "document_number": "malo"}
    snapshot = dict(values)
    first = _validate(example_flow.steps[0], values)
    second = _validate(example_flow.steps[0], values)
    assert values == snapshot
    assert first == second
