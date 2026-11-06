# Registro de implementación: `payment-idempotency-protection` (HU-IDEM, issue #27)

- Fecha: 2026-11-06
- Rol: Wallet API Developer
- Rama: `feature/hackaton`
- Commit base: `961d130` (sin commits nuevos: el código, las pruebas de QE y este log están sin commitear por instrucción)
- Entorno: Python 3.14.7, `api/.venv` (fastapi, httpx, pytest, pytest-cov ya instalados; sin dependencias nuevas)
- Fuentes: diseño aprobado (`docs/architecture/payment-idempotency-protection-impact.md` secciones 2 a 14), spec `payment-idempotency`, `tasks.md`, `qe-test-evidence.md`, constitución.

## 1. Archivos de producción creados (`api/app/`)

`config.py`, `errors.py`, `schemas.py`, `main.py`, `ports/payment_provider.py`, `ports/idempotency_store.py`, `repositories/sqlite_store.py`, `services/idempotency_key.py`, `services/payment_service.py`, `services/retry_service.py`, `services/request_audit_service.py`, `routes/dependencies.py`, `routes/payments.py`, `routes/idempotency_audit.py`.
No se modificaron pruebas, spec, diseño ni `proposal`. Solo se marcaron casillas en `openspec/changes/payment-idempotency-protection/tasks.md`.

## 2. Comando y salida real

```
cd api
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing
```

Resultado: **52 recolectadas: 51 pasadas, 1 fallada, 0 omitidas** (`1 failed, 51 passed, 1 warning in 4.20s`).

Fallo: `tests/unit/test_request_audit_service.py::test_datos_expuestos_por_solicitud_con_ambas_fechas` (`IndexError`: no hay solicitud `duplicate`). Ver discrepancia D-1.

Cobertura (umbral `fail_under = 85` alcanzado: **95.83 %**):

| Módulo | Stmts | Miss | Cobertura | Líneas sin cubrir |
|---|---|---|---|---|
| `config.py` | 49 | 3 | 94% | 43, 45, 57 |
| `errors.py` | 3 | 0 | 100% | - |
| `main.py` | 24 | 1 | 96% | 22 |
| `ports/idempotency_store.py` | 64 | 0 | 100% | - |
| `ports/payment_provider.py` | 13 | 0 | 100% | - |
| `repositories/sqlite_store.py` | 89 | 6 | 93% | 78, 140, 196-197, 199-200 |
| `routes/dependencies.py` | 25 | 3 | 88% | 24, 26, 37 |
| `routes/idempotency_audit.py` | 13 | 0 | 100% | - |
| `routes/payments.py` | 40 | 2 | 95% | 32, 62 |
| `schemas.py` | 33 | 0 | 100% | - |
| `services/idempotency_key.py` | 10 | 0 | 100% | - |
| `services/payment_service.py` | 58 | 3 | 95% | 96-98 |
| `services/request_audit_service.py` | 14 | 0 | 100% | - |
| `services/retry_service.py` | 21 | 1 | 95% | 27 |
| **TOTAL** | 456 | 19 | **95.83%** | |

Líneas sin pruebas (riesgo bajo, registrado): validación de configuración inválida (`config.py` 43, 45, 57), reserva con `IntegrityError` ajeno a la clave (`sqlite_store.py` 78, 140), filtros de fecha del feed (`sqlite_store.py` 196-200), rama 401/422 de encabezados (`dependencies.py`), 404 de pago ajeno (`payments.py` 32, 62), `ProviderError` del proveedor (`payment_service.py` 96-98), reintento de pago inexistente o ajeno (`retry_service.py` 27), y el valor por defecto de `create_app` (`main.py` 22).

## 3. Diagnóstico del fallo (sin modificar la prueba)

Verificación puntual con un script ad hoc (no es parte de la suite), mismo escenario de la prueba, avance de 1 día y 1 hora entre solicitudes:

```
ventana 300 s        -> original original False   (otra clave: bucket distinto)
ventana 10_000_000 s -> original duplicate True
```

## 4. Tareas (orden del diseño sección 11)

| Tarea | Requisito | Estado | Evidencia |
|---|---|---|---|
| 2.1 | Clave de idempotencia por intento | Hecha | `test_idempotency_key` (10 pasadas) |
| 2.2 | Registro atómico clave a transacción | Hecha | `test_sqlite_store_concurrency` (20 hilos: 1 `CREATED`, 19 `EXISTS`; 1 llamada al proveedor) |
| 2.3 | Resultado original ante repetición | Hecha | `test_payment_service` (repetición terminal, en proceso, rechazado, 0 llamadas adicionales) |
| 3.1 | Registro de duplicados append-only | Hecha | `test_duplicado_registrado_...`, `test_cada_duplicado_...`; triggers SQL impiden UPDATE/DELETE |
| 3.2 | Relacionar duplicado con original | Hecha | `test_auditoria_relaciona_...`; `test_feed_filtra_...` |
| 2.5 | Reintento vinculado | Hecha | `test_retry_service` (6 pasadas) |
| 4.1 | Retención por canal desde configuración | Hecha | `test_retention_config` (4 pasadas) |
| 4.2 | Documentar comportamiento por defecto (OQ-11) | **Sin marcar** | Hay comportamiento y prueba (`return_original`), pero no hay documento propio en `api/`; falta el documento que referencie OQ-11 |
| 5.1 | Tipo, vínculo y ambas fechas | **Sin marcar** | 3 de 4 escenarios en verde; `test_datos_expuestos_por_solicitud_con_ambas_fechas` en rojo (D-1) |
| 5.2 | Duplicados no cuentan como transacciones | Hecha | `test_duplicados_no_cuentan_como_transacciones` |
| 2.4 | Mismo comportamiento en dos canales con proveedor simulado | Hecha, con salvedad | Prueba con doble en `contact-demo` y `merchant-demo`; contrato real del mock solo por MCP (QE, `qe-test-evidence.md` sección 5). No existe adaptador `wallet_mock_provider.py` (ver S-6) |
| 6.1 | Flujo extremo a extremo | Hecha | `test_flujo_extremo_a_extremo` (original, duplicado, reintento tras `REJECTED`, feed, sin día de reporte) |
| 1.1, 1.2, 1.3, 1.4, 5.3 | Acuerdos y aprobaciones humanas | Sin marcar | Dependen de personas |

## 5. Discrepancias con las pruebas de QE (no se modificaron)

- **D-1 (pide revisión de QE)**: `test_datos_expuestos_por_solicitud_con_ambas_fechas` avanza el reloj 25 h con la ventana de intento por defecto (300 s). Con buckets fijos (decisión P-2, spec y diseño) el `intent_id` repetido produce otra clave y la solicitud es `original`; la prueba espera `duplicate`. La propia sección 4 de `qe-test-evidence.md` indica usar una ventana grande en estos casos (como hace `test_politica_clave_vencida_return_original`) y R-1 está aceptado. Propuesta para QE: construir el mundo con `make_world(attempt_window_seconds=10_000_000)`. No se implementó una búsqueda sin ventana para forzar el verde, porque cambiaría la clave definida por la spec.
- **D-2 (informativa)**: `request_id` no es clave primaria en `payment_requests` (el diseño sección 6 lo proponía). Se usa `seq` autoincremental, porque un `X-Request-Id` repetido por el cliente provocaría un error 500 y la tabla debe registrar cada solicitud.

## 6. Supuestos y desviaciones del diseño

- S-1 `X-Payer-Id` obligatorio (patrón `[A-Za-z0-9._:-]{1,64}`); ausente o inválido: 401. Solo MVP (P-3).
- S-2 `X-Request-Id` y `X-Correlation-Id` se generan si faltan; si son inválidos: 422.
- S-3 Entrada validada en el borde: `amount_cents` entero estricto, `0 < monto <= 100000000`; `recipient` en `{contact-demo, merchant-demo}`; `intent_id` de 1 a 64 caracteres con patrón; `channel` con patrón `[a-z0-9-]{1,32}` (OQ-09 abierta, no se fija lista de canales).
- S-4 Política de clave vencida: solo se admite `return_original` (otro valor rechaza la carga de configuración). La retención no se hace cumplir (S-4 del diseño); si se supera, solo se escribe un log con `payment_id` y política. Valores OQ-11 (24 h), OQ-12 (5 min), OQ-13 (sin purga) son configuración por variables de entorno marcadas como "propuesta no aprobada" en `config.py`.
- S-5 El `ProviderError` (proveedor no utilizable) se trata como `UNCERTAIN`: el intento queda `PENDING`; una repetición es `duplicate` y no vuelve a llamar al proveedor. No hay tarea automática de `resolve` (H-6 de QE sigue abierta; no está en esta spec).
- S-6 No se creó `providers/wallet_mock_provider.py`: la API no llama al mock en esta fase (P-6) y el contrato HTTP del mock no está documentado en el repositorio (solo se conoce por MCP); escribirlo sería inventar rutas. `create_app` exige un proveedor inyectado; no hay proveedor real cableado. Pendiente de una fase posterior.
- S-7 El reintento usa un `intent_id` derivado del original (`retry-of:<payment_id>`) y la ventana del original. Así, repetir la llamada de reintento (doble clic) devuelve el mismo reintento como `duplicate` (200) y no cobra dos veces; además la clave no depende del paso del tiempo. Consecuencia: un segundo reintento sobre el mismo original devuelve el primero (aunque haya fallado); para reintentar de nuevo se reintenta sobre el último intento. Pendiente de confirmar con PAYER (OQ-03).
- S-8 Desviación del diseño: `link_retry` del puerto se sustituye por el campo `retry_of_payment_id` en `NewAttempt` (vínculo atómico al reservar). Se añaden al puerto `list_retries_of` y `count_attempts`.
- S-9 `GET /payments/{id}` incluye `retried_by` (lista de reintentos), lo que cubre el sentido original a reintento (H-3 de QE). Sin prueba de QE para ese sentido; hay cobertura parcial indirecta (línea de ruta ejecutada), falta prueba específica: **falta evidencia**.
- S-10 Autorización: `GET /payments/{id}` y `POST .../retries` devuelven 404 si el intento no pertenece al pagador. El feed `GET /idempotency/requests` solo devuelve solicitudes del pagador autenticado, porque no hay rol de operador definido. Esto limita el consumo del feed por conciliación (RECON) hasta definir el rol: ver hallazgo F-1.
- S-11 Logs: solo `payment_id`, estado y política; sin `payer_id`, claves ni montos.
- S-12 Los errores 500 usan la respuesta genérica de FastAPI; las excepciones de dominio se mapean a 404/409 sin detalle interno.

## 7. Hallazgos fuera de alcance (candidatos, no implementados)

- F-1 Falta un rol u operador para el feed de conciliación y auditoría (hoy acotado al pagador). Decisión de producto o seguridad.
- F-2 R-1 sigue vigente (cobro doble potencial al cruzar la frontera de ventana). Riesgo aceptado (P-2).
- F-3 Falta un proceso de resolución para intentos `PENDING` huérfanos (R-2, H-6): el puerto tiene `resolve`, pero nada lo invoca.
- F-4 Faltan pruebas para las ramas listadas en la sección 2 (encabezados inválidos, 404 por pago ajeno, filtros de fecha, `ProviderError`, configuración inválida). Se propone que QE las añada.
- F-5 Advertencia de deprecación de Starlette (`httpx` con `TestClient`, sugiere `httpx2`): de la librería de pruebas, no del código.
- F-6 No existe README de `api/` con variables de entorno; sería el lugar para cerrar la tarea 4.2.

## 8. Llamadas al mock `wallet-mocks`

Ninguna (decisión P-6; no se usó `mock_reset`, `payment_create` ni `kyc_create`).

## 9. Estado por requisito

| Requisito | Estado |
|---|---|
| Clave de idempotencia por intento de pago | Cumplido (escenario "identificador generado al abrir la confirmación": no aplicable en `api/`, lado cliente) |
| Solicitud repetida devuelve el resultado original | Cumplido; "vínculo consultable desde cualquiera de los dos": implementado, falta evidencia (S-9) |
| Registro de auditoría de duplicados | Cumplido |
| Distinción originales/duplicados para conciliación | Parcial: 3 de 4 escenarios verdes; "Datos expuestos por solicitud" en rojo por D-1 (pendiente de QE); "Día de reporte no asignado" verificado en `test_flujo_extremo_a_extremo` |
| Retención de claves configurable por canal | Cumplido en configuración y prueba; tarea 4.2 (documento) pendiente |
| Contrato del proveedor en dos canales | Cumplido con doble; mock real verificado por QE vía MCP (APPROVED, TIMEOUT, PENDING); falta evidencia para REJECTED, PROVIDER_ERROR, DELAYED_APPROVAL; adaptador real no implementado (S-6) |
| Cobertura >= 85% del código en `api/app` | Cumplido: 95.83% |
| Acuerdos 1.1, 1.2, 1.3, 1.4, 5.3 | Pendiente (personas) |


## Actualizacion 2026-11-06 11:59 - correccion de prueba de QE y suite en verde

- Prueba corregida: `test_datos_expuestos_por_solicitud_con_ambas_fechas` (api/tests/unit/test_request_audit_service.py) ahora usa `make_world(attempt_window_seconds=10_000_000)`. Motivo: con buckets fijos (P-2) 25 h con la ventana de 300 s genera otra clave; era un error de la prueba, no del codigo.
- Comando: `.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing` en api/.
- Resultado real: 52 passed, 1 warning; cobertura total 95.83% (minimo por modulo 88%, routes/dependencies.py).
- Tarea 5.1 marcada como cumplida con esta evidencia.

