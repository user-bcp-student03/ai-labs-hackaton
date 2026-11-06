# Evidencia QE: `user-onboarding-mvp-completion` (HU-ONB, issue #28)

- Fecha: 2026-11-06 (trabajo entre 12:13 y 12:30, UTC-05:00)
- Rama: `feature/hackaton`
- Commit base: `ab1137b` (las pruebas, el diseño y esta evidencia están sin commit)
- Fase: **ROJA, solo API** (sin código de producción de onboarding; fallo esperado)
- Alcance de esta fase: `api/`. Web: **pendiente (fase web)**, no se tocó `web/`.
- Fuentes: spec `user-onboarding-mvp-completion`, `tasks.md`, [diseño aprobado](../../architecture/user-onboarding-mvp-completion-impact.md) (secciones 3 a 14 y 18; Q-1 a Q-12 aprobadas con la recomendación por defecto), [constitución](../../WALLET-CONSTITUTION.md), convenciones de [HU-IDEM](../payment-idempotency-protection/qe-test-evidence.md).

## 1. Archivos creados y modificados

| Archivo | Cambio | Pruebas nuevas |
|---|---|---|
| `api/tests/conftest.py` | **Modificado, solo añadidos** (fixtures y constantes al final; ningún fixture existente cambió): `tests_data_dir`, `example_flow_raw`, `example_flow`, `alternate_flow`, `any_flow` (parametrizado), `valid_values`, `events_of`, `make_onboarding_world`, `onboarding_world`, `drive`, `make_onb_client`, `onb_client` | - |
| `api/tests/data/onboarding-flow-alternate.json` | Nuevo: configuración «ejemplo no aprobado» con otros pasos y orden (`perfil` order 2 listado antes que `bienvenida` order 1) | - |
| `api/tests/unit/test_onboarding_settings.py` | Nuevo | 6 |
| `api/tests/unit/test_flow_config.py` | Nuevo | 41 |
| `api/tests/unit/test_step_engine.py` | Nuevo | 21 |
| `api/tests/unit/test_sqlite_onboarding_store.py` | Nuevo | 25 |
| `api/tests/unit/test_onboarding_service.py` | Nuevo | 33 |
| `api/tests/unit/test_wallet_access_service.py` | Nuevo | 9 |
| `api/tests/unit/test_onboarding_analytics_service.py` | Nuevo | 27 |
| `api/tests/unit/test_app_wiring_onboarding.py` | Nuevo | 21 |
| `api/tests/acceptance/test_onboarding_flow_acceptance.py` | Nuevo | 50 |
| **Total** | | **233** |

No se tocó código de producción, spec, diseño, openspec ni `api/config/` (el JSON de ejemplo es del desarrollador). Sin commit ni push.

## 2. Mock `wallet-mocks` (solo lectura)

Solo `wallet_scenarios` y `wallet_health`. Sin `kyc_create`, `payment_create`, `payment_reverse` ni `mock_reset`. No se creó ningún dato.

| # | Hora aprox. | Herramienta | Entrada | Respuesta real |
|---|---|---|---|---|
| 1 | 12:13 | `wallet_scenarios` | - | 200 `{"kyc":["APPROVED","REJECTED","MANUAL_REVIEW","UNAVAILABLE"],"payments":["APPROVED","REJECTED","PENDING","DELAYED_APPROVAL","TIMEOUT_AFTER_PROCESSING","PROVIDER_ERROR"],"settlements":["MISSING","AMOUNT","DUPLICATE","ORPHAN","CLEAR"]}` |
| 2 | 12:13 | `wallet_health` | - | 200 `{"status":"ok","environment":"cloud-mock","storage":"sqlite","startedAt":"2026-10-23T21:52:54.503Z"}` |

Escenarios KYC existentes: `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `UNAVAILABLE`. **Quedan fuera de esta fase por la decisión D-1** (sin `KycProviderPort`; la spec no define rechazo, revisión manual ni indisponibilidad de KYC; OQ-19). Por eso ninguna prueba usa el mock: no hay contrato de proveedor que contrastar en ONB. Estado de contraste con el mock: **no aplicable en esta fase** (decisión D-1). El estado `activo`/`pendiente` es local (D-3), no el de la wallet del proveedor.

## 3. Comando y salida real

Entorno: `api/.venv` existente (Python 3.14.7, fastapi 0.162.0, httpx 0.28.1, pytest 9.2.0).

```
cd api
.venv\Scripts\python -m pytest -q -p no:cacheprovider
```

Salida real final (suite completa, 12:25): `66 failed, 53 passed, 1 warning, 166 errors in 10.44s`. Total recolectado: 285 = 52 (HU-IDEM) + 233 (nuevas).

| Conjunto | Total | Pasadas | Falladas | Errores de setup |
|---|---|---|---|---|
| HU-IDEM (7 archivos existentes) | 52 | **52** | 0 | 0 |
| Onboarding (9 archivos nuevos) | 233 | 1 | 66 | 166 |

Comando solo de HU-IDEM (12:25): `.venv\Scripts\python -m pytest -q -p no:cacheprovider tests/unit/test_idempotency_key.py tests/unit/test_payment_service.py tests/unit/test_request_audit_service.py tests/unit/test_retention_config.py tests/unit/test_retry_service.py tests/unit/test_sqlite_store_concurrency.py tests/acceptance/test_payment_flow_acceptance.py` -> `52 passed, 1 warning in 6.64s`.

Por archivo nuevo (pasadas / falladas / errores): settings 0/6/0; flow_config 0/37/4; step_engine 0/6/15; sqlite_onboarding_store 0/0/25; onboarding_service 0/1/32; wallet_access_service 0/0/9; onboarding_analytics_service 0/0/27; app_wiring_onboarding **1**/16/4; onboarding_flow_acceptance 0/0/50.

Causas reales (todas esperadas en fase roja):

- `ModuleNotFoundError: No module named 'app.services.flow_config'` (causa dominante; arrastra a los fixtures `example_flow` y `alternate_flow`).
- `ImportError: cannot import name 'FlowConfigError' from 'app.errors'`.
- `ModuleNotFoundError: No module named 'app.repositories.sqlite_onboarding_store'` (los 25 de almacén; también el fixture `make_onboarding_world`).
- `ModuleNotFoundError: No module named 'app.services.onboarding_service'`.
- `AttributeError: 'Settings' object has no attribute 'onboarding'` e `ImportError: cannot import name 'OnboardingSettings' from 'app.config'`.
- `KeyError: 'onboarding_flow'` (firma de `create_app` sin parámetros nuevos).
- `Failed: DID NOT RAISE ValueError` (`load_settings` ignora `ONB_*`).

La **única prueba nueva en verde** es `test_app_wiring_onboarding.py::test_sin_flujo_las_rutas_de_pagos_siguen_igual`: es de regresión (principio 18) y debe seguir verde. No se ocultó ni omitió ninguna prueba.

## 4. Matriz requisito/escenario -> prueba -> resultado

Abreviaturas (`api/tests/...`): SET=`unit/test_onboarding_settings`, FC=`unit/test_flow_config`, SE=`unit/test_step_engine`, ST=`unit/test_sqlite_onboarding_store`, SV=`unit/test_onboarding_service`, WA=`unit/test_wallet_access_service`, AN=`unit/test_onboarding_analytics_service`, WI=`unit/test_app_wiring_onboarding`, AC=`acceptance/test_onboarding_flow_acceptance`. Resultado de todas: **ROJO** (módulo ausente o contrato incumplido), salvo la marcada VERDE.

### Requisito: Secuencia de pasos y paso actual visibles (tareas 2.1, 2.2)

| Escenario | Prueba(s) |
|---|---|
| Los pasos provienen de configuración | SV `test_inicio_muestra_todos_los_pasos_y_resalta_el_primero`, `test_la_secuencia_el_orden_y_el_paso_actual_son_los_de_la_configuracion[example\|alternate]`, `test_el_orden_lo_da_order_y_no_la_posicion_en_el_archivo`; FC `test_los_pasos_se_ordenan_por_order_no_por_posicion`; AC `test_flow_publica_la_configuracion_y_la_etiqueta_de_ejemplo`; WI `test_el_flujo_se_carga_desde_steps_config_path_al_iniciar` |
| Cambiar la configuración cambia los pasos sin cambiar el comportamiento | SV `test_el_comportamiento_es_el_mismo_con_cualquier_configuracion[example\|alternate]`; AC `test_flow_cambia_con_la_configuracion_sin_cambiar_el_contrato`, `test_recorrido_completo_con_la_configuracion_alterna` |
| Los pasos de ejemplo no son requisitos regulatorios | FC `test_configuracion_de_ejemplo_se_carga`, `test_ejemplo_entregado_en_api_config_es_valido_y_esta_etiquetado`, caso inválido «ejemplo sin label»; AC `test_flow_publica_la_configuracion_y_la_etiqueta_de_ejemplo` |
| Se muestra la secuencia al iniciar | SV `test_inicio_muestra_todos_los_pasos_y_resalta_el_primero`; AC `test_inicio_responde_201_con_la_secuencia_y_el_primer_paso_actual` |
| El paso actual se actualiza al avanzar | SV `test_el_paso_actual_avanza_y_la_secuencia_sigue_visible`; AC `test_el_paso_actual_avanza_al_completar_un_paso` |
| El paso actual sigue visible tras un error | SV `test_tras_un_error_de_validacion_el_paso_actual_no_cambia`; AC `test_dato_obligatorio_faltante_responde_422_...` (el estado no cambia) |

### Requisito: Validación bloqueante con mensaje accionable (tareas 3.1, 3.2)

| Escenario | Prueba(s) |
|---|---|
| Las validaciones provienen de configuración | SE `test_las_reglas_provienen_de_la_configuracion_no_del_motor`; FC `test_toda_regla_y_campo_requerido_tienen_mensaje`, `test_ejemplo_entregado_cumple_tarea_3_2_mensajes_en_cada_regla` |
| Cambiar las reglas configuradas cambia la validación sin cambiar el comportamiento | SE `test_cambiar_la_regla_configurada_cambia_la_validacion_sin_cambiar_el_motor`; SV `test_cambiar_una_regla_configurada_cambia_la_validacion_no_el_bloqueo` |
| Falta información obligatoria | SE `test_dato_obligatorio_faltante_indica_que_dato_y_como_completarlo`, `test_texto_vacio_o_solo_espacios_cuenta_como_faltante` (x3), `test_checkbox_requerido_exige_estar_marcado`; SV `test_dato_faltante_bloquea_el_avance_sin_evento_ni_progreso`; AC `test_dato_obligatorio_faltante_responde_422_con_mensaje_accionable_y_no_avanza` |
| Datos inválidos | SE `..._por_formato_...`, `..._por_longitud_...`, `test_patron_se_evalua_con_fullmatch`, `test_un_solo_error_por_campo_...`, `test_el_orden_de_las_reglas_...`, `test_regla_min_length`; SV `test_dato_invalido_bloquea_y_devuelve_el_mensaje_configurado`; AC `test_dato_invalido_responde_422_con_el_mensaje_de_la_regla` |
| Se corrige y se permite avanzar | SE `test_valores_validos_no_producen_errores`; SV `test_se_corrige_y_se_permite_avanzar`; AC `test_corregir_y_reenviar_permite_avanzar` |

Contrato de seguridad y orden (diseño 5 y 6.2): SE `test_campo_desconocido_...`, `test_los_mensajes_no_reflejan_el_valor_enviado`, `test_el_motor_es_puro_...`; SV `test_los_valores_enviados_no_se_reflejan_ni_se_persisten_ni_se_registran` (D-5), `test_paso_posterior_al_actual_...` (409), `test_paso_inexistente_se_rechaza`, `test_reenviar_un_paso_completado_es_idempotente_...` (Q-7), `test_onboarding_ajeno_o_inexistente_...`; AC `test_la_respuesta_de_error_no_refleja_el_valor_enviado`, `test_paso_fuera_de_orden_responde_409`, `test_paso_inexistente_responde_404`, `test_onboarding_ajeno_e_inexistente_responden_igual_404`, `test_reenviar_un_paso_completado_es_200_idempotente`, `test_sin_identidad_se_responde_401` (x6).

### Requisito: Activación del estado de la wallet al finalizar el onboarding (tareas 4.1, 4.2)

| Escenario | Prueba(s) |
|---|---|
| Onboarding finalizado correctamente | ST `test_close_activa_la_wallet_y_registra_el_cierre_en_una_transaccion`; SV `test_cierre_correcto_activa_la_wallet`; AC `test_cierre_correcto_activa_la_wallet_y_repetirlo_es_idempotente`, `test_wallet_404_sin_onboarding_pendiente_al_iniciar_y_activa_al_cerrar` |
| Onboarding incompleto | SV `test_cierre_incompleto_lanza_incomplete_con_los_pasos_pendientes`, `test_completar_todos_los_pasos_sin_cerrar_no_activa_la_wallet`; AC `test_cierre_incompleto_responde_409_...`, `test_acceso_a_pagos_denegado_sin_wallet_o_con_wallet_pendiente` |
| La wallet no pasa a activo mientras el onboarding no finalice | ST `test_wallet_no_pasa_a_activo_mientras_no_se_cierre`, `test_cierre_es_atomico_si_falla_el_evento_no_se_activa_la_wallet`; WA `test_pasos_completados_sin_cierre_no_dan_acceso` |
| Acceso al punto de entrada de pagos de bajo monto | WA `test_wallet_activa_da_acceso`, `test_dependencia_require_active_wallet_permite_con_wallet_activa`, `..._responde_403_sin_wallet_activa`, `..._exige_identidad`; AC `test_acceso_a_pagos_permitido_con_wallet_activa`, `test_el_acceso_a_pagos_es_por_identidad` |
| Alcance del término «activación» | SV `test_los_eventos_son_solo_los_tres_tipos_sin_activacion_del_pagador`; ST `test_solo_existen_los_tres_tipos_de_evento_de_onboarding` (no hay evento de activación del pagador) |
| Nombres de los demás estados de la wallet (OQ-23) | SET `test_valores_provisionales_por_defecto`; SV `test_cohorte_y_estado_previo_de_la_wallet_vienen_de_la_configuracion`, `test_por_defecto_cohorte_mvp_pe_y_wallet_pendiente`; ST `test_estado_previo_de_la_wallet_viene_del_argumento_no_del_almacen`; WA `test_estado_previo_configurable_tampoco_da_acceso` |
| Idempotencia y concurrencia del cierre (tarea 4.1, diseño D-8) | ST `test_close_repetido_es_idempotente_sin_efectos_nuevos`, `test_close_concurrente_gana_un_solo_hilo` (20 hilos); SV `test_cierre_repetido_es_idempotente`, `test_cierre_concurrente_activa_una_sola_vez` |
| Decisión Q-1 (no se condiciona `POST /payments`) | WI `test_con_flujo_las_rutas_de_pagos_siguen_igual_y_no_exigen_wallet_activa` |

### Requisito: Eventos de analítica del onboarding (tareas 5.1, 5.2)

| Escenario | Prueba(s) |
|---|---|
| Registro del inicio | ST `test_start_crea_sesion_wallet_pendiente_y_evento_de_inicio`, `test_marcas_de_tiempo_en_formato_utc_de_ancho_fijo`; SV `test_recorrido_completo_registra_inicio_pasos_y_cierre_coherentes` |
| Registro de cada paso finalizado | ST `test_record_step_completed_registra_progreso_y_evento_una_sola_vez`; SV `test_recorrido_completo_...`, `test_dato_faltante_bloquea_...` (el paso rechazado no genera evento) |
| Registro del cierre del flujo | ST `test_close_activa_la_wallet_...`; SV `test_recorrido_completo_...`, `test_abandonar_no_genera_evento_de_cierre_ni_activa` (OQ-21 provisional); AC `test_recorrido_completo_inicio_error_correccion_cierre_activo_y_acceso_a_pagos` (tarea 7.1) |
| Eventos sin duplicados | ST `test_start_repetido_...`, `test_start_concurrente_...`, `test_record_step_concurrente_...`, `test_unicidad_de_evento_por_onboarding_tipo_y_paso`, `test_eventos_son_append_only`; SV `test_enviar_el_mismo_paso_en_paralelo_deja_un_unico_evento`, `test_inicio_concurrente_crea_una_sola_sesion`, `test_iniciar_de_nuevo_reanuda_la_misma_sesion`; AC `test_el_cliente_no_puede_enviar_eventos` (D-7) |

Atomicidad (diseño 7): ST `test_cierre_es_atomico_...`, `test_inicio_es_atomico_...`, `test_paso_es_atomico_...`. Sin valores de campos en el almacén (D-5): ST `test_el_progreso_no_guarda_valores_de_campos`. Una sesión por usuario (Q-11): ST `test_unicidad_de_sesion_por_usuario`, `test_usuarios_distintos_...`; SV `test_usuario_con_onboarding_completado_recibe_su_sesion_completed`; AC `test_iniciar_otra_vez_reanuda_con_200_y_el_mismo_id`. Consultas parametrizadas: ST `test_user_id_se_trata_como_dato_no_como_sql`.

### Requisito: Datos para medir la duración de onboarding (tarea 5.3; cierra solo tras 1.2/OQ-20)

| Escenario | Prueba(s) |
|---|---|
| Reporte periódico para verificar la reducción / Reporte periódico de duración | AN `test_reporte_de_duracion_sin_datos_tiene_claves_y_mediana_nula`; AC `test_reporte_de_duracion_por_http_calcula_la_mediana_con_la_frontera_por_defecto`, `test_reporte_de_duracion_sin_datos_devuelve_mediana_nula` |
| Valores de referencia no garantizados | AN `test_valores_8_y_3_son_parametros_configurables_no_resultados`; SET `test_valores_leidos_de_entorno` |
| Cálculo de la mediana de la cohorte | AN `test_mediana_con_cantidad_impar_...`, `..._par_...`, `test_la_mediana_resiste_un_valor_extremo`, `test_excluye_onboardings_sin_evento_de_fin_otra_cohorte_y_otro_mes`, `test_el_onboarding_pertenece_al_mes_de_su_evento_de_fin_con_desfase`, `test_frontera_de_prueba_distinta_de_la_provisional`, `test_frontera_con_evento_de_paso_tambien_como_inicio` |
| Frontera de eventos no definida / pendiente de definición oficial (OQ-20) | AN `test_frontera_por_defecto_se_publica_como_provisional`; SET `test_valores_provisionales_por_defecto` |

### Requisito: Salida analítica de nuevos usuarios activos y gasto de adquisición (tareas 6.1, 6.2 parcial, 6.3)

| Escenario | Prueba(s) |
|---|---|
| Finalidad de verificación de MAU y CAC | AN `test_salida_mensual_sin_datos_tiene_las_claves_documentadas`, `test_parametros_de_referencia_son_configurables`; AC `test_salida_mensual_cuenta_el_usuario_activo_y_declara_el_gasto_no_disponible` |
| Definición de «nuevo usuario activo» | AN `test_conteo_mensual_solo_cuenta_wallets_activas_del_mes` |
| Fuente del gasto y definición de usuario nuevo para CAC (OQ-22) | Solo contrato: AN `test_gasto_de_adquisicion_siempre_no_disponible_y_nunca_cero` y `pending_definitions == ["OQ-05","OQ-22"]` |
| Reporte consolidado fuera de alcance (OQ-07) | AN `test_la_salida_mensual_no_calcula_mau_ni_cac`, `test_parametros_de_referencia_son_configurables` |
| Conteo mensual de nuevos usuarios activos | AN `test_conteo_mensual_solo_cuenta_...`, `test_conteo_mensual_excluye_otras_cohortes`, `test_limites_mensuales_usan_el_desfase_configurado_por_defecto` (x4 bordes), `test_el_desfase_horario_es_configurable`; AC `test_salida_mensual_cuenta_...` |
| **Atribución de gasto de adquisición** | **Sin prueba: bloqueado por OQ-22** (tarea 6.2 abierta). No se inventa fuente ni valor `available` |
| Campos de la salida mensual (tarea 6.3) | AN `test_salida_mensual_sin_datos_tiene_las_claves_documentadas` (claves exactas); AC `..._declara_el_gasto_no_disponible` |
| Mes sin gasto de adquisición disponible | AN `test_gasto_de_adquisicion_siempre_no_disponible_y_nunca_cero` |
| Usuario sin onboarding finalizado | AN `test_conteo_mensual_solo_cuenta_...` (incompleto, pasos sin cierre y solo inicio); AC `test_salida_mensual_cuenta_...` |

Acceso a la salida (Q-4, diseño 9.3): AC `test_analitica_cerrada_por_defecto_sin_token_configurado_responde_404` (x2), `test_analitica_con_token_incorrecto_o_ausente_responde_401` (x6), `test_analitica_con_mes_invalido_responde_422` (x6), `test_la_salida_analitica_no_exige_identidad_de_pagador`; SET `test_token_analitico_no_aparece_en_repr`; WI `test_sin_flujo_la_salida_analitica_tambien_responde_503` (x2).

### Tareas

| Tarea | Pruebas | Estado de la prueba |
|---|---|---|
| 1.7 | FC (41), SET (6) | Roja |
| 2.1, 2.2 | SV, AC, FC | Roja |
| 3.1, 3.2 | SE (21), SV, AC | Roja |
| 4.1, 4.2 | ST, SV, WA, AC | Roja |
| 5.1, 5.2 | ST, SV, AC | Roja |
| 5.3 | AN, AC | Roja; **no se cierra hasta 1.2/OQ-20** |
| 6.1 | AN, AC | Roja |
| 6.2 | solo contrato `unavailable` | **Bloqueada por OQ-22** |
| 6.3 | AN (claves exactas) | Roja; falta aprobar glosario (1.3) y documentar la salida |
| 7.1 | AC `test_recorrido_completo_...` (API) | Roja; recorrido web manual pendiente (fase web) |
| Integración de `create_app` (D-9) | WI (21) | 1 VERDE (regresión), 20 rojas |
| Regresión HU-IDEM | 52 existentes | **52 VERDES (sin cambios)** |

## 5. Contratos asumidos por las pruebas (el diseño no fija estas firmas; el desarrollador debe respetarlas o acordar el cambio con QE)

El diseño fija módulos, endpoints, tablas, eventos y variables de entorno; **no** fija las firmas Python de servicios ni los campos exactos de `OnboardingView`. QE los asumió así.

**Configuración (`app.config`)**
- `OnboardingSettings` (dataclass congelado) con: `steps_config_path=""`, `cohort="MVP-PE"`, `wallet_pending_status="pendiente"`, `duration_start_event="onboarding_started"`, `duration_end_event="onboarding_closed"`, `report_utc_offset_minutes=-300`, `ref_duration_baseline_minutes=8`, `ref_duration_target_minutes=3`, `ref_mau_min=1000`, `ref_mau_max=2000`, `ref_cac_target_cents=1000`, `analytics_token=""` (con `repr=False`: el token no aparece en `repr(Settings)`).
- `Settings.onboarding: OnboardingSettings` con valor por defecto (los `Settings(**overrides)` actuales no cambian); `load_settings` lee las variables `ONB_*` (sección 10) y un valor numérico inválido lanza `ValueError`.

**Configuración de pasos (`app.services.flow_config`, `app.errors`)**
- `parse_flow_definition(raw: Mapping) -> FlowDefinition` y `load_flow_definition(path: str) -> FlowDefinition`; ambos lanzan `app.errors.FlowConfigError` ante cualquier incumplimiento de la sección 6.1 (JSON no válido y raíz que no es objeto incluidos).
- `FlowDefinition(schema_version, flow_id, approval_status, label, steps: tuple[StepDefinition])` inmutable; `steps` **ordenados por `order`**. `StepDefinition(id, order, title, description, fields)`; `FieldDefinition(name, type, label, hint, required, required_message, autocomplete, input_mode, rules)`; `RuleDefinition(kind, value, message)`.
- Restricciones extra verificadas: mensajes y `required_message` sin HTML; título 1-80, descripción hasta 300; patrón hasta 200; `max_length` obligatorio en `text` y hasta 500.

**Motor (`app.services.step_engine`)**
- `validate_step_values(step: StepDefinition, values: Mapping[str, str | bool]) -> list[FieldError]`; lista vacía = válido. `FieldError(field, rule, message)` con `rule` en `required | min_length | max_length | pattern | unknown_field`. Un error por campo (primera regla que falla, en el orden configurado), `strip()` previo, `re.fullmatch`, sin eco del valor, puro.

**Puerto y almacén (`app.ports.onboarding_store`, `app.repositories.sqlite_onboarding_store`)**
- `SqliteOnboardingStore(db_path, clock=...)`; el almacén sella el tiempo con su reloj. Crea las 4 tablas de la sección 7 (nombres y columnas del diseño) con `IF NOT EXISTS`, comparte archivo con `SqliteIdempotencyStore`.
- `start_onboarding(onboarding_id, user_id, cohort, wallet_pending_status) -> StartOutcome(session, created)`; `get_session(onboarding_id)`, `get_session_by_user(user_id)`, `get_wallet(user_id)` (devuelven `None` si no existe); `list_completed_step_ids(onboarding_id) -> list[str]` (orden de finalización; `[]` si no existe); `record_step_completed(onboarding_id, step_id) -> bool`; `close_onboarding(onboarding_id) -> CloseOutcome(session, closed_now)`.
- `OnboardingSession(onboarding_id, user_id, cohort, status, started_at, updated_at, closed_at)` con `status` en `IN_PROGRESS | COMPLETED` y fechas `datetime` con zona horaria UTC; `Wallet(user_id, status, created_at, activated_at)` con `status` `activo` tras el cierre.
- Las tres operaciones son transaccionales (si falla la inserción del evento no queda sesión, progreso, wallet activa ni cierre) y propagan `sqlite3.DatabaseError`. Los eventos se leen en pruebas por SQL directo desde `onboarding_events` (sin método de puerto).

**Servicios**
- `OnboardingService(store, flow, settings, clock)`; `new_onboarding_id()` -> `ob_` + 32 hex. Métodos: `start_or_resume(user_id) -> StartedOnboarding(created, onboarding)`; `get_current(user_id)`; `submit_step(user_id, onboarding_id, step_id, values)`; `close(user_id, onboarding_id)`. Los tres últimos y `start_or_resume().onboarding` devuelven `OnboardingState(onboarding_id, status, cohort, wallet_status, current_step_id | None, steps: [StepState(id, order, title, status in completed|current|pending)], completed_steps, total_steps)`, con igualdad por valor.
- Excepciones en `app.errors`: `FlowConfigError`, `OnboardingNotFound` (también onboarding ajeno), `StepNotFound`, `StepNotCurrent`, `StepValidationFailed(.errors)`, `OnboardingIncomplete(.pending_step_ids)`, `WalletNotActive`.
- Semántica: reenviar un paso completado devuelve el estado sin validar ni crear eventos (aun con otros valores); completar todos los pasos no activa la wallet (solo `close`); cierre repetido devuelve el mismo estado sin cambios.
- `WalletAccessService(store)`: `is_active(user_id) -> bool` y `require_active(user_id) -> None` (lanza `WalletNotActive`).
- `OnboardingAnalyticsService(store, settings)`: `monthly_output(month) -> dict` y `duration_report(month) -> dict` con **exactamente** las claves de 9.1 y 9.2 (`month` mal formado -> `ValueError`). Mes del onboarding = mes de `closed_at` (mensual) o del evento de fin (duración) con `report_utc_offset_minutes`; filtra por `settings.onboarding.cohort`; mediana con `statistics.median` (par = promedio de los dos centrales; `null` sin datos); frontera `event_type[:step_id]`; `boundary.status = "provisional_oq20"`.

**HTTP (rutas de la sección 5)**
- Errores `{"detail": {"code", "message", ...}}`; extras dentro de `detail`: `errors[{field, rule, message}]` (422), `pending_step_ids` (409 `ONBOARDING_INCOMPLETE`), `next_action: "complete_onboarding"` (403 `WALLET_NOT_ACTIVE`).
- `OnboardingView` (POST `/onboarding`: 201 nueva y 200 reanudada; GET `/onboarding/current`; PUT paso; POST cierre) con las claves de `OnboardingState`. `FlowView` con `flow_id, approval_status, label, steps[{id, order, title, description, fields[{name, type, label, required, ...}]}]`; `max_length` se deriva de la regla `max_length`; no publica reglas ni patrones ni mensajes.
- `GET /wallet` -> `{"status", "activated_at"}` (404 sin wallet); `GET /wallet/payments-entry` -> `{"allowed": true}` o 403.
- Analítica: encabezado `X-Analytics-Token`; **sin** `X-Payer-Id`; sin token configurado 404; token incorrecto o ausente 401; `month` mal formado 422.
- Identidad: `X-Payer-Id` con `request_context` existente (401 sin él) en todas las rutas, excepto `GET /onboarding/flow` (no verificado) y analítica.
- `app.routes.wallet.require_active_wallet`: dependencia FastAPI que usa `request_context` y `app.state.services.wallet_access`.
- `create_app(provider, settings=None, store=None, clock=..., *, onboarding_flow=None, onboarding_store=None)`; `app.state.services.onboarding`, `.wallet_access`, `.onboarding_analytics` (`None` sin flujo -> rutas nuevas, incluida analítica, 503 `ONBOARDING_NOT_CONFIGURED`); con flujo, el almacén por defecto es `SqliteOnboardingStore(settings.db_path, clock)`; `steps_config_path` se carga al iniciar y un archivo inválido lanza `FlowConfigError`.

## 6. Hallazgos

- **H-1 (bloqueante para el repositorio limpio)**: `.gitignore` línea 11 (`**/data/`) **ignora** `api/tests/data/onboarding-flow-alternate.json` (comprobado con `git check-ignore -v`). Sin una excepción (por ejemplo `!api/tests/data/`) el archivo no se versiona y las pruebas que lo usan (fixtures `alternate_flow` y `any_flow[alternate]`, y el cableado por `steps_config_path`) fallarían en un clon limpio. QE no modificó `.gitignore`; decisión del desarrollador o del revisor.
- **H-2**: el diseño no fija las firmas Python de servicios ni los campos exactos de `OnboardingView`/`MonthlyOutputView`; QE los asumió (sección 5). Si desarrollo elige otros, debe acordarlo con QE antes de adaptar pruebas.
- **H-3 (decisiones no definidas por la spec ni por el diseño, asumidas para cerrar la prueba)**: (a) ubicación de `FlowConfigError` en `app.errors`; (b) analítica sin flujo configurado -> 503 (y no 404 por token); (c) token ausente -> 401; (d) `month` inválido -> 422 en HTTP y `ValueError` en servicio; (e) `GET /onboarding/flow` exige o no identidad (no se prueba); (f) `pending_step_ids`, `errors` y `next_action` dentro de `detail`.
- **H-4**: el tipo incorrecto de un valor (número en un `text`, texto en un `checkbox`) y un cuerpo sin `values` no están definidos por el diseño (6.2 solo describe `str | bool`). Sin prueba: **falta evidencia** (FastAPI/Pydantic respondería 422 con su propia forma, distinta de `STEP_VALIDATION_FAILED`).
- **H-5**: comparación del token en tiempo constante (`hmac.compare_digest`), no logueo de valores a nivel de aplicación completa y límite de tamaño del cuerpo HTTP no se pueden demostrar con una prueba funcional barata: se verificarán en la revisión de seguridad. Límite de tasa (RS-02 heredado de HU-IDEM): fuera de esta fase.
- **H-6**: las pruebas de límites mensuales usan el desfase `-300` (supuesto S-2, no aprobado como OQ). Si Analítica define otro, cambia la configuración, no las pruebas (el desfase es parámetro de prueba).
- **H-7**: la prueba de concurrencia (20 hilos) de inicio, paso y cierre depende de `busy_timeout` y de la atomicidad real de SQLite; puede exponer interbloqueos que las pruebas con mocks no verían (es el objetivo).
- **H-8**: la única verde nueva (`test_sin_flujo_las_rutas_de_pagos_siguen_igual`) es una regresión intencional y no debe volverse roja.
- **H-9**: los textos de ejemplo y de las pruebas usan documentos ficticios `TEST-` y el token `TEST-analytics-token` (principio 16). No hay secretos reales.
- **H-10**: la prueba `test_ejemplo_entregado_en_api_config_...` lee `api/config/onboarding-steps.example.json`, que el desarrollador debe crear con la estructura de la sección 6.3 (ids `datos-personales`, `contacto`, `aceptacion` y etiqueta con «ejemplo no aprobado»).

## 7. Cobertura

Meta 85% del código modificado. **Falta evidencia**: no existe código de onboarding. Comando a usar con la implementación: `.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing` desde `api/` (`fail_under = 85` en `api/pyproject.toml`). Se medirá por módulo nuevo y se registrará aquí al cerrar el ciclo.

## 8. Defectos

Ninguno de producción (no existe el código). Los fallos actuales son la fase roja esperada. Sin defectos de HU-IDEM: sus 52 pruebas siguen en verde.

## 9. Web

**Actualizacion 2026-11-06 (fase web).** `ng lint` sin errores; 96 pruebas web pasadas (15 archivos) con cobertura lines 100% y statements 99.24%; `ng build` correcto; regresion API 308 pasadas con 98.61% de cobertura; 52 pruebas de HU-IDEM sin cambios respecto de `ab1137b`. Detalle y comandos en `implementation-log.md` (seccion "Fase Web"). **Falta evidencia:** lista manual WCAG 2.2 AA (teclado, foco, `aria-live`, 320 px, zoom 200%, contraste, lector de pantalla) y recorrido 7.1 en navegador contra la API real; no se ejecutaron.
**Texto original de la fase roja:** no se tocó `web/`. Quedan para esa fase: `ng test` por componente, servicio y guard; lista manual WCAG 2.2 AA (teclado, foco, `aria-live`, 320 px, zoom 200%, contraste, lector de pantalla); recorrido manual 7.1 contra la API real (Q-12); `ng lint` con `angular-eslint`.

## 10. Estado por requisito

> Tabla de la fase roja (antes de implementar). Estado actual medido: ver la actualización de la sección 9 y `implementation-log.md` (API: 308 pruebas pasadas; web: 96 pasadas). Siguen en «falta evidencia»: 6.2 (OQ-22), 5.3 (OQ-20), accesibilidad manual y recorrido 7.1 en navegador.

| Requisito | Estado |
|---|---|
| Secuencia de pasos y paso actual visibles (API) | Pendiente (pruebas rojas, listas para implementar); parte de interfaz: falta evidencia (fase web) |
| Validación bloqueante con mensaje accionable (API) | Pendiente; interfaz: falta evidencia (fase web) |
| Activación del estado de la wallet | Pendiente (acceso a pagos en la interfaz: falta evidencia, fase web) |
| Eventos de analítica del onboarding | Pendiente |
| Datos para medir la duración de onboarding | Pendiente; tarea 5.3 no cierra hasta definir la frontera (1.2, OQ-20): falta evidencia oficial |
| Salida analítica: conteo mensual y campos | Pendiente |
| Salida analítica: atribución de gasto de adquisición (6.2) | **Falta evidencia: bloqueada por OQ-22**; solo contrato `unavailable` con prueba |
| Contraste con el KYC del mock | No aplicable en esta fase (decisión D-1); escenarios KYC `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `UNAVAILABLE` fuera de alcance |
| Regresión HU-IDEM (52 pruebas) | **Cumplido** (52 pasan, medido 12:25) |
| Cobertura >= 85% del código nuevo | Falta evidencia |
| Interfaz web y accesibilidad | Pendiente (fase web) |
