# Evidencia QE: `payment-idempotency-protection` (HU-IDEM, issue #27)

- Fecha: 2026-11-06 (llamadas al mock entre 11:47 y 11:48, UTC-05:00)
- Rama: `feature/hackaton`
- Commit base: `961d130` (las pruebas y el esqueleto están sin commit)
- Fase: **ROJA** (sin implementación; fallo esperado)
- Fuentes: spec `payment-idempotency`, `tasks.md`, diseño aprobado (secciones 3 a 10 y 14), constitución.

## 1. Archivos creados

`api/pyproject.toml`, `api/.gitignore`, `api/app/**/__init__.py` (6 paquetes vacíos), `api/tests/conftest.py`, `api/tests/unit/test_{idempotency_key,payment_service,sqlite_store_concurrency,retry_service,retention_config,request_audit_service}.py`, `api/tests/acceptance/test_payment_flow_acceptance.py`. No hay código de producción.

## 2. Comando y salida real

Entorno: Python 3.14.7, fastapi 0.162.0, httpx 0.28.1, pytest 9.2.0, pytest-cov 7.1.0 (`api/.venv`).

```
cd api
python -m venv .venv
.\.venv\Scripts\python -m pip install fastapi httpx pytest pytest-cov
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider
```

Resultado: **52 pruebas recolectadas: 0 pasadas, 14 falladas, 38 con error de setup, 0 omitidas** (`14 failed, 38 errors in 0.58s`). Todas por `ModuleNotFoundError` (motivo esperado):

| Causa | Cantidad |
|---|---|
| `No module named 'app.services.idempotency_key'` | 10 (falladas) |
| `No module named 'app.config'` | 4 (falladas) |
| `No module named 'app.repositories.sqlite_store'` (fixture `store`) | 38 (errores) |

Nota: los errores de `sqlite_store` ocultan por ahora los módulos `payment_service`, `retry_service`, `request_audit_service`, `main`, `ports.*`, `errors`; aparecerán al implementar.

## 3. Matriz requisito/escenario -> prueba -> resultado

Archivo abreviado: UK=test_idempotency_key, PS=test_payment_service, CC=test_sqlite_store_concurrency, RS=test_retry_service, RC=test_retention_config, AU=test_request_audit_service, AC=test_payment_flow_acceptance. Resultado de todas: ROJO (ModuleNotFoundError).

| Requisito / escenario | Prueba(s) |
|---|---|
| Clave / Identificador de intención generado al abrir la confirmación | AC `test_entrada_invalida_422` (parte servidor: `intent_id` obligatorio). La generación en pantalla pertenece al flujo del pagador: no aplicable en `api/` |
| Clave / Intento nuevo recibe clave | UK `test_intento_nuevo_recibe_clave_sha256_hex`; PS `test_intento_original_llama_una_vez_al_proveedor`, `test_clave_reservada_antes_de_llamar_al_proveedor`, `test_clave_del_proveedor_es_la_clave_de_idempotencia` |
| Clave / Cambio de componente genera otra clave | UK `test_cambio_de_componente_cambia_clave` (x5), `test_forma_canonica_evita_colisiones_por_concatenacion` |
| Clave / Pago legítimo idéntico con otra intención | PS `test_pago_legitimo_identico_con_otra_intencion_no_es_duplicado`; AC `test_pago_con_intencion_distinta_es_transaccion_independiente` |
| Clave / Mismo identificador repetido es duplicado | UK `test_misma_intencion_repetida_misma_clave`; PS `test_mismo_intent_repetido_es_duplicado`; AC `test_post_payments_original_202_y_duplicado_200` |
| Clave / Duración de ventana no definida (config) | UK `test_ventana_de_intento_depende_de_configuracion`, `test_ventana_bucket_fijo_...` (P-2); RC `test_valores_provisionales_por_defecto`, `test_valores_leidos_de_entorno` |
| Repetida / Reintentar tras fallo o expiración | RS `test_reintentar_tras_fallo_...`, `test_reintentar_tras_expiracion_...`, `test_reintento_rechazado_si_original_no_es_fallido_ni_expirado` (x2, P-5) |
| Repetida / Clave original devuelve el original | RS `test_clave_original_devuelve_resultado_original_tras_reintento` |
| Repetida / Vínculo almacenado | RS `test_vinculo_almacenado_y_reintento_no_es_duplicado` (solo sentido reintento->original; ver H-3) |
| Repetida / Resultado terminal | PS `test_repeticion_con_resultado_terminal_...`, `test_repeticion_con_proveedor_rechazado_...`, `test_resultado_terminal_no_se_sobrescribe` |
| Repetida / En proceso | PS `test_repeticion_en_proceso_...`, `test_timeout_del_proveedor_deja_intento_pendiente` |
| Repetida / Mismo comportamiento en cualquier riel | PS `test_mismo_comportamiento_en_cualquier_canal` (x2 canales) |
| Repetida / Una sola transacción por clave | PS `test_una_sola_transaccion_por_clave`; CC `test_reserve_attempt_concurrente_crea_una_sola_fila`, `test_submit_concurrente_llama_una_vez_al_proveedor` |
| Auditoría / Duplicado registrado | PS `test_duplicado_registrado_con_ids_y_clave` |
| Auditoría / Cada duplicado su registro | PS `test_cada_duplicado_genera_su_registro_y_el_original_no_cambia` |
| Auditoría / Trazabilidad original-duplicado | AU `test_auditoria_relaciona_duplicado_con_original_...`; AC `test_feed_filtra_por_clave_correlacion_y_tipo` |
| Conciliación / Original identificado | AU `test_intento_original_identificado` |
| Conciliación / Duplicado identificado | AU `test_reintento_duplicado_identificado_con_vinculo` |
| Conciliación / Datos por solicitud; Día de reporte no asignado | AU `test_datos_expuestos_por_solicitud_con_ambas_fechas`; AC `test_flujo_extremo_a_extremo` |
| Conciliación / Reintento vinculado vs duplicado | AU `test_reintento_vinculado_se_distingue_del_duplicado` |
| Conciliación / Duplicados no cuentan | AU `test_duplicados_no_cuentan_como_transacciones` |
| Retención / por canal; no definida | RC `test_ventana_de_retencion_por_canal_y_fallback_a_default`, `test_politica_de_clave_vencida_...`; PS `test_politica_clave_vencida_return_original` |
| Integración 6.1 | AC `test_flujo_extremo_a_extremo` |

Otros (contrato/seguridad): AC `test_identidad_del_pagador_viene_del_encabezado_no_del_cuerpo` (P-3), `test_retry_sobre_intento_pendiente_409` (P-5), `test_get_payment_devuelve_intento_...`.

## 4. Contratos asumidos por las pruebas (el diseño no fija firmas)

El diseño (sección 4) solo fija los puertos. Las pruebas asumen, y desarrollo debe respetarlos o acordar cambio con QE:

- `app.config`: `Settings(attempt_window_seconds=300, retention_seconds_by_channel={"default": 86400}, expired_key_policy="return_original", audit_retention_seconds=None, wallet_mock_url="", wallet_id="wallet-demo")`, `.retention_for(channel)`, `load_settings(env: Mapping)`.
- `derive_idempotency_key(payer_id, amount_cents, recipient, attempt_window_index, intent_id)` y `attempt_window_index(now, window_seconds)`.
- `PaymentService(store, provider, settings, clock).submit_payment(payer_id, intent_id, amount_cents, recipient, channel, request_id, correlation_id)` -> objeto con `.attempt` (`payment_id`, `idempotency_key`, `status`, `provider_payment_id`, `retry_of_payment_id`) y `.request_type`.
- `RetryService(...).create_linked_retry(payment_id, payer_id, request_id, correlation_id)`; `app.errors.RetryNotAllowed`.
- `RequestAuditService(store).list_requests(idempotency_key, correlation_id, request_type, ...)` y `.totals().transactions`; `RequestRecord` con `request_id, correlation_id, idempotency_key, payment_id, request_type, requested_at, original_requested_at, retry_of_payment_id`.
- `SqliteIdempotencyStore(db_path)`; tablas `payment_attempts` (columna `status`, `payment_id`); `reserve_attempt` devuelve objeto con `.outcome` en `CREATED|EXISTS`; `NewAttempt(payment_id, idempotency_key, payer_id, amount_cents, recipient, channel, intent_id, attempt_window_index, created_at)`; `RequestFilters()` con todos los campos opcionales.
- `ProviderResult(provider_payment_id, status)`; estados `PENDING|SUCCEEDED|REJECTED|UNCERTAIN`; mapeo a intento: `REJECTED`->`FAILED`, `UNCERTAIN`/`PENDING`->`PENDING`.
- `create_app(settings, provider, store, clock)`; respuestas JSON con `payment_id`, `status`, `idempotency_key`, `retry_of`, `request_type`; feed como lista JSON.
- Para clave vencida con `return_original` las pruebas usan ventana de intento grande, porque con ventana de 300 s el mismo `intent_id` tras cruzar el bucket genera otra clave (R-1).

## 5. Llamadas al mock `wallet-mocks` (respuestas tal cual)

Wallet `wallet-demo`; claves con prefijo `qe-idem-20261106-`. Sin `mock_reset`, `payment_reverse` ni `kyc_create`.

| # | Hora aprox. | Herramienta | Entrada | Respuesta |
|---|---|---|---|---|
| 1 | 11:47 | `wallet_health` | - | 200 `{"status":"ok","environment":"cloud-mock","storage":"sqlite",...}` |
| 2 | 11:47 | `wallet_get` | `wallet-demo` | 200 `balance 76300, reserved 1250, available 75050` (antes) |
| 3 | 11:47 | `payment_list` | `wallet-demo` | 200, lista previa de pagos de otros (sin claves `qe-idem`) |
| 4 | 11:47 | `payment_create` | key `...-ok-merchant-01`, merchant-demo, 101, APPROVED | **202** `pay_eb49b5c485ee4748`, status PENDING |
| 5 | 11:47 | `payment_create` | misma clave y contenido | **200** mismo `pay_eb49b5c485ee4748` |
| 6 | 11:47 | `payment_create` | misma clave, monto 102 | **409** `{"error":"IDEMPOTENCY_CONFLICT"}` |
| 7 | 11:47 | `payment_create` | key `...-ok-contact-01`, contact-demo, 103, APPROVED | **202** `pay_4389deb84b3c4a1f`, PENDING |
| 8 | 11:47 | `payment_create` | misma clave y contenido | **200** mismo `pay_4389deb84b3c4a1f` |
| 9 | 11:47 | `payment_create` | key `...-timeout-contact-01`, contact-demo, 104, TIMEOUT_AFTER_PROCESSING | **504** `{"error":"PROVIDER_TIMEOUT","paymentId":"pay_a017863414754e72","status":"PENDING"}` |
| 10 | 11:47 | `payment_create` | misma clave y contenido | **200** mismo `pay_a017863414754e72` |
| 11 | 11:47 | `payment_create` | key `...-timeout-merchant-01`, merchant-demo, 105, TIMEOUT_AFTER_PROCESSING | **504** `paymentId pay_6362c3dbdd364576`, PENDING |
| 12 | 11:48 | `payment_create` | key `...-pending-merchant-01`, merchant-demo, 106, PENDING | **202** `pay_7d20827e9ab94e98`, PENDING |
| 13 | 11:48 | `payment_create` | misma clave y contenido | **200** mismo `pay_7d20827e9ab94e98` |
| 14 | 11:48 | `payment_get` | `pay_a017863414754e72` | 200 PENDING, idem `...-timeout-contact-01` |
| 15 | 11:48 | `provider_payment_get` | `pay_7d20827e9ab94e98` | 200 `{"amount":106,"status":"PENDING"}` |
| 16 | 11:48 | `payment_list` | `wallet-demo` | 200; filtrado `qe-idem`: exactamente 5 pagos, 5 claves distintas, sin duplicados |

Conclusión sobre el modelo del doble: idempotencia del mock confirmada (misma clave y contenido = 200 con el mismo id; contenido distinto = 409; 504 con pago ya creado y reintento con la misma clave = 200 con el mismo id; sin duplicados en el listado). Se confirma en dos canales (`contact-demo`, `merchant-demo`) y en APPROVED, TIMEOUT_AFTER_PROCESSING y PENDING. `PROVIDER_ERROR`, `REJECTED` y `DELAYED_APPROVAL` no se ejecutaron (fuera del plan acordado): falta evidencia.

## 6. Hallazgos

- **H-1 (R-4 resuelto en lo observado)**: el 504 del mock devuelve `paymentId` en el cuerpo (`{"error":"PROVIDER_TIMEOUT","paymentId":...,"status":"PENDING"}`), y repetir `submit` con la misma clave devuelve 200 con el mismo id. El adaptador debe leer ese `paymentId` del 504 y mapearlo a `ProviderResult(status=UNCERTAIN, provider_payment_id=<id>)`. Mi doble usa `provider_payment_id=None` para UNCERTAIN en `test_timeout_del_proveedor_deja_intento_pendiente`; es un caso conservador, desarrollo puede ajustar con QE.
- **H-2**: el estado local del mock sigue `PENDING` incluso en escenario `APPROVED` tras `payment_create` (202/200); no se vio transición a `SUCCEEDED` sin evento/callback. El diseño debe tratar `PENDING` como estado válido tras `submit` y completar con `resolve` o callback; no asumir `SUCCEEDED` inmediato. No se entregaron eventos (`event_deliver`), por no estar en el plan.
- **H-3 (gap de contrato)**: el diseño no define cómo consultar el vínculo desde el original hacia sus reintentos (spec: "consultable desde cualquiera de los dos"); el puerto solo tiene `get_attempt` con `retry_of`. Sin prueba del sentido original->reintento: falta evidencia hasta que el diseño fije un método o campo.
- **H-4**: el diseño 3 prevé `acceptance/test_provider_contract.py` contra `WALLET_MOCK_URL`; la decisión P-6 lo invalida. La aceptación HTTP usa `TestClient` con doble y el contrato real se verifica solo por MCP (sección 5).
- **H-5 (R-1 confirmado por diseño de prueba)**: con buckets fijos, el mismo `intent_id` repetido tras cruzar el límite produce otra clave y un segundo cobro; no hay escenario de spec que lo cubra. Prueba omitida a propósito: riesgo aceptado (P-2).
- **H-6**: ante timeout (UNCERTAIN) el diseño 7.5 permite `resolve` o reenviar `submit`; las pruebas solo exigen que el intento quede `PENDING` y que la repetición sea `duplicate`. Falta decidir cuál de las dos acciones usará una repetición.
- **H-7**: el estado `EXPIRED` lo asigna PAYER (OQ-17); la prueba de reintento tras expiración lo fija por SQL directo sobre `payment_attempts`.

## 7. Cobertura

Meta 85% del código modificado. **No aplica aún: falta evidencia** (no hay código en `app/`). `fail_under = 85` está configurado en `api/pyproject.toml`.

## 8. Defectos

Ninguno de producción (no existe). Fallos actuales = fase roja esperada.

## 9. Estado por requisito

| Requisito | Estado |
|---|---|
| Clave de idempotencia por intento de pago | Pendiente (pruebas rojas); escenario "Identificador generado al abrir la confirmación": no aplicable en `api/` (lado cliente) |
| Solicitud repetida devuelve el resultado original | Pendiente; escenario "Vínculo... consultable desde cualquiera de los dos": falta evidencia (H-3) |
| Registro de auditoría de duplicados | Pendiente |
| Distinción originales/duplicados para conciliación | Pendiente |
| Retención de claves configurable por canal | Pendiente |
| Contrato del proveedor (idempotencia del mock, 2 canales) | Cumplido en el mock real para APPROVED, TIMEOUT_AFTER_PROCESSING y PENDING; falta evidencia para REJECTED, PROVIDER_ERROR, DELAYED_APPROVAL |
| Cobertura >= 85% | Falta evidencia |


## Actualizacion 2026-11-06 11:59 - correccion de prueba de QE y suite en verde

- Prueba corregida: `test_datos_expuestos_por_solicitud_con_ambas_fechas` (api/tests/unit/test_request_audit_service.py) ahora usa `make_world(attempt_window_seconds=10_000_000)`. Motivo: con buckets fijos (P-2) 25 h con la ventana de 300 s genera otra clave; era un error de la prueba, no del codigo.
- Comando: `.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing` en api/.
- Resultado real: 52 passed, 1 warning; cobertura total 95.83% (minimo por modulo 88%, routes/dependencies.py).
- Tarea 5.1 marcada como cumplida con esta evidencia.

