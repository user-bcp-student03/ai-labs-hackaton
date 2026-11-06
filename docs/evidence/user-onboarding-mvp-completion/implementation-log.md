# Registro de implementación: `user-onboarding-mvp-completion` (HU-ONB, issue #28)

Diseño: [user-onboarding-mvp-completion-impact.md](../../architecture/user-onboarding-mvp-completion-impact.md) (aprobado, Q-1 a Q-12). Evidencia de QE: [qe-test-evidence.md](qe-test-evidence.md). Las secciones se agregan al final; este archivo no se reescribe.

## Fase API

- Fecha: 2026-11-06
- Rol: Wallet API Developer
- Rama: `feature/hackaton`
- Commit base: `ab1137b`. **Sin commit ni push** en esta fase (instrucción de la tarea): todo el trabajo está sin commit sobre ese base, junto con las pruebas de QE y el diseño que ya estaban sin commit.
- Alcance: solo `api/`. No se tocó `web/`, ni la spec, ni el diseño, ni `api/tests/conftest.py`, ni ninguna prueba de QE. No se usó el mock `wallet-mocks` (decisión D-1: sin puerto de KYC) ni `mock_reset`.

### 1. Archivos

| Archivo | Cambio |
|---|---|
| `api/app/repositories/sqlite_support.py` | Nuevo: `TIMESTAMP_FORMAT`, `to_text`, `to_datetime`, `connection(db_path)` e `initialize_schema` |
| `api/app/repositories/sqlite_store.py` | Modificado: usa `sqlite_support` (refactor sin cambio de comportamiento, Q-9) |
| `api/app/config.py` | Modificado, aditivo: `OnboardingSettings`, `Settings.onboarding`, variables `ONB_*`; `analytics_token` con `repr=False` |
| `api/app/errors.py` | Modificado, aditivo: `FlowConfigError`, `OnboardingNotFound`, `StepNotFound`, `StepNotCurrent`, `StepValidationFailed`, `OnboardingIncomplete`, `WalletNotActive` |
| `api/app/main.py` | Modificado: `create_app(..., *, onboarding_flow=None, onboarding_store=None)`; servicios de onboarding en `None` sin flujo; `app.state.settings`; manejador del 422 de formato |
| `api/app/schemas_onboarding.py` | Nuevo |
| `api/app/ports/onboarding_store.py` | Nuevo: un solo puerto `OnboardingStorePort` (D-2) |
| `api/app/repositories/sqlite_onboarding_store.py` | Nuevo |
| `api/app/services/flow_config.py`, `step_engine.py`, `onboarding_service.py`, `wallet_access_service.py`, `onboarding_analytics_service.py` | Nuevos |
| `api/app/routes/onboarding.py`, `wallet.py`, `onboarding_analytics.py` | Nuevos |
| `api/config/onboarding-steps.example.json` | Nuevo: etiquetado «ejemplo no aprobado», documentos `TEST-` (sección 6.3 del diseño) |
| `api/tests/unit/test_onboarding_http_hardening.py` | Nuevo, de desarrollo (23 pruebas): tipos y tamaños del cuerpo, eco de valores, regresión del 422 fuera de onboarding y ramas de guarda. No modifica ni sustituye pruebas de QE |
| `openspec/changes/user-onboarding-mvp-completion/tasks.md` | Solo casillas 2.1, 3.2, 4.1, 5.1, 5.2 y 6.1 |

Detalles de diseño aplicados: el almacén de onboarding comparte archivo SQLite con HU-IDEM; inicio, paso y cierre son transacciones únicas (sesión, wallet y evento) con `UNIQUE` + `INSERT OR IGNORE` para deduplicar y `UPDATE ... WHERE status='IN_PROGRESS'` para ganar la carrera del cierre; no se persisten valores de campos (D-5); `X-Analytics-Token` se compara con `hmac.compare_digest` y la salida está cerrada por defecto (404 sin token configurado); `acquisition_spend` es siempre `unavailable`/`null` (OQ-22).

Dos métodos de servicio que el diseño no listaba y se añadieron por necesidad de las rutas: `OnboardingService.flow` (propiedad de solo lectura, para `GET /onboarding/flow`) y `WalletAccessService.wallet_of` (para `GET /wallet`). El puerto lleva además `count_closed_between` y `list_event_intervals` para la analítica (contrato no fijado por el diseño).

### 2. Comandos y salidas reales

Entorno: `api/.venv` (Python 3.14.7). Desde `api/`.

1. Línea base tras el refactor de `sqlite_support` (solo los 7 archivos de HU-IDEM):
   `.venv\Scripts\python -m pytest -q -p no:cacheprovider tests/unit/test_idempotency_key.py tests/unit/test_payment_service.py tests/unit/test_request_audit_service.py tests/unit/test_retention_config.py tests/unit/test_retry_service.py tests/unit/test_sqlite_store_concurrency.py tests/acceptance/test_payment_flow_acceptance.py`
   Salida: `52 passed, 1 warning in 5.38s` (antes: 52 según `qe-test-evidence.md` sección 3; después del refactor: 52).
2. Settings, flow_config, motor y almacén: `... pytest tests/unit/test_onboarding_settings.py tests/unit/test_flow_config.py tests/unit/test_step_engine.py tests/unit/test_sqlite_onboarding_store.py` -> `93 passed in 2.74s`.
3. Servicios (sin las dos pruebas de rutas): `66 passed, 3 deselected in 10.92s`.
4. Corrida de verificación final (tras la última edición de código):
   - 52 de HU-IDEM: `52 passed, 1 warning in 3.91s`.
   - Todo salvo el archivo de desarrollo (`--ignore=tests/unit/test_onboarding_http_hardening.py`): **`285 passed, 1 warning in 20.58s`** = 52 de HU-IDEM + 233 de onboarding de QE.
   - Suite completa: `.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing` -> **`308 passed, 1 warning in 29.57s`** (285 + 23 de desarrollo). `Required test coverage of 85.0% reached. Total coverage: 98.61%`. 0 falladas, 0 errores.

Cobertura por módulo (suite completa con `--cov-report=term-missing`, corrida de 308 pruebas con el mismo total 98.61%; después solo se envolvió una línea larga en `sqlite_onboarding_store.py` y se repitió la corrida con `--cov-report=term`, con el mismo total):

| Módulo nuevo o modificado | Cobertura | Líneas sin cubrir |
|---|---|---|
| `routes/onboarding.py` | 100% | - |
| `routes/wallet.py` | 100% | - |
| `routes/onboarding_analytics.py` | 100% | - |
| `schemas_onboarding.py` | 100% | - |
| `ports/onboarding_store.py` | 100% | - |
| `repositories/sqlite_onboarding_store.py` | 100% | - |
| `services/flow_config.py` | 100% | - |
| `services/step_engine.py` | 100% | - |
| `services/onboarding_service.py` | 100% | - |
| `services/wallet_access_service.py` | 100% | - |
| `services/onboarding_analytics_service.py` | 100% | - |
| `errors.py` | 100% | - |
| `repositories/sqlite_support.py` | 96% | 15 (rama de fecha sin zona horaria, heredada de `sqlite_store`) |
| `main.py` | 98% | 29 (`_utc_now` por defecto) |
| `config.py` | 97% | 90, 92, 104 (código de HU-IDEM no modificado) |
| `repositories/sqlite_store.py` | 93% | 119, 175-176, 178-179 (código de HU-IDEM no modificado) |
| Total `app` | **98.61%** | meta del código nuevo (85%): cumplida |

### 3. Tareas

| Tarea | Estado | Requisito y evidencia |
|---|---|---|
| 2.1 | Marcada | Req. «Secuencia de pasos»: `flow_config`, `onboarding_service`, `GET /onboarding/flow`; pruebas de ejemplo y alterno (SV `test_la_secuencia_...[example\|alternate]`, `test_el_comportamiento_es_el_mismo_...`, AC `test_flow_cambia_con_la_configuracion_...`) |
| 3.2 | Marcada | Req. «Validación»: mensaje obligatorio al cargar (FC 41 casos) y en el ejemplo entregado (`test_ejemplo_entregado_cumple_tarea_3_2_...`); errores sin eco del valor |
| 4.1 | Marcada | Req. «Activación»: cierre atómico, idempotente y concurrente (ST, SV, AC); wallet no activa sin cierre |
| 5.1 | Marcada | Req. «Eventos»: inicio, paso y cierre con marca de tiempo, `onboarding_id` y cohorte (ST, SV, AC) |
| 5.2 | Marcada | Dedup por `UNIQUE` en la misma transacción; reenvíos y 20 hilos dejan un único evento (ST, SV) |
| 6.1 | Marcada | Req. «Salida analítica»: conteo mensual por cohorte, excluye no finalizados, desfase configurable (AN, AC) |
| 2.2 | **Sin marcar** | Cubre API y web (diseño sección 12). La parte API (secuencia, paso actual y progreso en `OnboardingView`) está verificada; falta la interfaz |
| 3.1 | **Sin marcar** | Cubre API y web. La parte API (422 con errores accionables, bloqueo, corrección, cambio de regla) está verificada; faltan `step-form`, `error-summary` y `form-field` |
| 4.2 | **Sin marcar** | Cubre API y web. La parte API (`GET /wallet/payments-entry` 200/403 y `require_active_wallet`) está verificada; falta `active-wallet.guard` y la página de entrada. Se puede marcar si el revisor considera que el alcance de la tarea es solo el backend |
| 5.3 | **Sin marcar** | Datos y reporte de duración implementados y probados con frontera de prueba; cierra solo tras 1.2/OQ-20 (frontera oficial pendiente de Producto/Analítica) |
| 6.2 | **Sin marcar** | Bloqueada por OQ-22: solo contrato `unavailable`/`null` y parámetros de referencia; sin fuente de gasto, sin valor `available`, sin prueba de «Atribución de gasto de adquisición» |
| 6.3 | **Sin marcar** | La salida y sus claves están implementadas y la prueba de claves exactas pasa, pero falta documentarla y aprobar el glosario (1.3) |
| 7.1 | **Sin marcar** | La aceptación de API pasa (`test_recorrido_completo_...`); falta el recorrido web contra la API real (fase web) |
| 1.1 a 1.7 | **Sin marcar** | Acuerdos humanos y personas (Cumplimiento, Producto, Analítica). 1.7 (contrato y ejemplo) está entregado en código y documentado en el diseño, pero su verificación pide que Cumplimiento confirme que puede cargar sus pasos reales: falta evidencia de esa confirmación |

### 4. Discrepancias con las pruebas de QE (no se editó ninguna)

Ninguna prueba queda en rojo. Observaciones:

- **D-1 (artefacto de prueba, no bloqueante):** `tests/unit/test_app_wiring_onboarding.py::test_el_flujo_se_carga_desde_steps_config_path_al_iniciar` usa `make_settings()` con el `db_path` por defecto (relativo, `idempotency.sqlite3`) y flujo configurado; por diseño (3.3) entonces se crea `SqliteOnboardingStore("idempotency.sqlite3")`, así que la suite **crea `api/idempotency.sqlite3`** en el directorio de trabajo. Se comprobó: borrado el archivo, ejecutar solo esa prueba lo recrea. El archivo **no está ignorado** por `.gitignore` (`git check-ignore` sin coincidencia). Es el riesgo R-9 / RS-06 de HU-IDEM. No se editó la prueba. Recomendación: añadir `*.sqlite3*` al `.gitignore` o que la prueba use `db_path` temporal. El archivo generado se borró tras cada corrida.
- **H-1 de QE (`.gitignore`):** ya existe `!api/tests/data/` sin commit en el árbol (no es de esta fase); `api/tests/data/onboarding-flow-alternate.json` aparece como no rastreado y no ignorado. Falta que se incluya en el commit.
- **H-4 de QE (tipo incorrecto y cuerpo sin `values`):** el diseño no lo define. Decisión de desarrollo: el borde exige `values` como objeto con valores `str` (hasta 2000 caracteres) o `bool` estrictos, hasta 50 claves de hasta 64 caracteres; si no, **422 `INVALID_REQUEST`** con mensaje estático y **sin eco del cuerpo** (el 422 por defecto de FastAPI devuelve `input`). Solo aplica a rutas bajo `/onboarding`; el resto conserva el manejador base (regresión probada). Dentro del motor, un valor que no sea texto en un campo `text` cuenta como dato faltante y un checkbox solo está marcado con `true`. Cubierto por `test_onboarding_http_hardening.py`.
- **H-3 de QE:** se respetaron las decisiones asumidas (a a f). Adicional: `GET /onboarding/flow` **no exige identidad** (la definición no es dato personal).
- **H-5 de QE:** `hmac.compare_digest` sobre bytes UTF-8 implementado; sin logs en la capa de onboarding (no hay llamadas a `logging`); el límite de tamaño del cuerpo HTTP a nivel de servidor (p. ej. proxy) no se implementó y queda para la revisión de seguridad.
- **Estados de la wallet del mock:** no aplicable (D-1).

### 5. Supuestos y valores provisionales (ninguno resuelve una OQ)

- OQ-06: cohorte `MVP-PE` (propuesta no aprobada). OQ-23: estado previo `pendiente` (propuesta no aprobada). OQ-20: frontera `onboarding_started` -> `onboarding_closed`, publicada con `status: provisional_oq20` (propuesta no aprobada). OQ-21: sin evento de abandono (provisional). S-2: desfase `-300` minutos (supuesto, no aprobado). Referencias 8/3 minutos, 1000/2000 MAU y PEN 10 (1000 céntimos): parámetros de la épica, no resultados.
- Todos se leen de variables `ONB_*`; el token analítico (`ONB_ANALYTICS_TOKEN`) vacío mantiene la salida cerrada. No hay secretos en el repositorio; las pruebas usan `TEST-analytics-token`.
- Una sesión por usuario (Q-11): `UNIQUE(user_id)`; reanudar devuelve 200 y la sesión `COMPLETED` si ya terminó.
- La verificación «todos los pasos completados» del cierre la hace el servicio antes de `close_onboarding`; es segura porque el progreso es solo de inserción y la configuración no cambia en caliente (diseño sección 7).
- `OnboardingService` acepta `clock` por simetría con los demás servicios, pero no lo usa: el almacén sella las marcas de tiempo.

### 6. Hallazgos fuera de alcance (candidatos, no implementados)

1. `.gitignore` no ignora `*.sqlite3*` (ver D-1). Candidato para Seguridad (RS-06 de HU-IDEM).
2. Sin límite de tasa ni de tamaño de cuerpo a nivel de servidor (RS-02 heredado); `X-Payer-Id` sigue siendo identidad provisional suplantable (R-5).
3. `list_event_intervals` devuelve todas las filas del mes (sin paginación); aceptable en MVP, a revisar con volumen real.
4. `request_context` de HU-IDEM usa `HTTP_422_UNPROCESSABLE_ENTITY`, obsoleta en la versión instalada de Starlette (solo advertencia en tiempo de importación). Esta fase usa un valor numérico con nombre y no toca ese código.
5. La advertencia `StarletteDeprecationWarning` de `httpx` en `TestClient` es heredada del entorno.

### 7. Estado por requisito (fase API)

| Requisito | Estado |
|---|---|
| Secuencia de pasos y paso actual visibles | Cumplido en API (probado); interfaz: falta evidencia (fase web) |
| Validación bloqueante con mensaje accionable | Cumplido en API (probado); interfaz: falta evidencia (fase web) |
| Activación del estado de la wallet | Cumplido en API: cierre atómico, idempotente y concurrente; acceso a `/wallet/payments-entry`; guard web: falta evidencia |
| Eventos de analítica del onboarding | Cumplido (inicio, pasos, cierre, dedup, atomicidad) |
| Datos para medir la duración | Implementado y probado con frontera de prueba; la frontera oficial sigue pendiente (OQ-20): falta evidencia oficial |
| Salida analítica: conteo mensual y campos | Cumplido (6.1); documentación y glosario pendientes (6.3, 1.3) |
| Salida analítica: atribución de gasto (6.2) | No cumplido por diseño: bloqueado por OQ-22; contrato `unavailable` verificado |
| Contraste con el mock KYC | No aplicable (D-1) |
| Regresión HU-IDEM | Cumplido: 52 pasan antes y después |
| Cobertura del código nuevo >= 85% | Cumplido: 98.61% total; 100% en los módulos nuevos de onboarding |
| Interfaz web y accesibilidad | Pendiente (fase web) |


## Fase Web

Registrado el 2026-11-06 por la verificacion posterior al agente frontend (el agente termino sin resumen; los resultados siguientes se midieron de nuevo). Rama `feature/hackaton`, commit base `ab1137b`, cambios sin commit.

### Versiones verificadas
- Node v26.9.0, npm 11.19.1, Angular CLI 22.2.6, Angular 22.2.4, TypeScript 6.0.3, rxjs 7.8.2, vitest 5.1.0 (`npx ng version`).
- Dependencias de desarrollo adicionales a las previstas en Q-8: `jsdom`, `vitest`, `prettier`, `typescript-eslint`, `@eslint/js` (las genera `ng new`/`angular-eslint`); ver RS-08 del analisis de seguridad.

### Resultados medidos (web/)
| Comando | Resultado |
|---|---|
| `npm run lint` (`ng lint`) | Exit 0, "All files pass linting", sin errores ni avisos |
| `$env:CI="1"; npm test -- --watch=false --coverage` | Exit 0; 15 archivos de prueba y 96 pruebas pasadas, 0 falladas; cobertura statements 99.24%, branches 98.17%, functions 96.26%, lines 100% |
| `npm run build` (`ng build`) | Exit 0, 7.25 s, sin avisos; inicial 266.57 kB (74.81 kB transferencia); chunk lazy `onboarding-routes` 57.55 kB |
| `npm audit --omit=dev` | 0 vulnerabilidades (dependencias de produccion) |
| `npm audit` | 15 moderadas, en la cadena de herramientas de desarrollo angular-eslint / @typescript-eslint/utils; no se aplico `--force` |

### Resultados medidos (api/, regresion completa)
- `.venv\Scripts\python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing` (13:12): 308 passed, 0 failed, 0 errors; cobertura 98.61% (1224 sentencias, 17 sin cubrir).
- Las 52 pruebas de HU-IDEM no se alteraron: `git diff ab1137b` sobre sus 7 archivos de prueba y sobre las lineas existentes de `api/tests/conftest.py` no muestra diferencias.
- Las pruebas crean `api/idempotency.sqlite3` (prueba de QE con `db_path` relativo); se borro tras la corrida y `.gitignore` ahora cubre `*.sqlite3`.

### Tareas
- Marcadas con evidencia: 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 6.1 (API verificada por pruebas; web verificada por lint, pruebas y build).
- Sin marcar: 1.1 a 1.7 (acuerdos con personas/artefactos), 5.3 (OQ-20), 6.2 (OQ-22), 6.3 (glosario y documentacion de la salida), 7.1 (falta el recorrido manual extremo a extremo en navegador contra la API real, ver Q-12).

### Falta evidencia
- Recorrido manual en navegador (teclado, foco, `aria-live`, 320 px, zoom 200%, contraste, lector de pantalla) y recorrido extremo a extremo contra la API real.
- Revision de las dependencias de desarrollo con `npm audit fix` (cambios incompatibles): requiere decision humana.
