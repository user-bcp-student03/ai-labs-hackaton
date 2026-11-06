# Análisis de riesgos de seguridad: `payment-idempotency-protection` (HU-IDEM, issue #27)

Rol: Wallet Security. Revisión 1 (2026-11-06). Solo lectura: no se modificó código, configuración ni specs.

## 1. Alcance de la revisión

- HU / issue: HU-IDEM, `payment-idempotency-protection`, issue #27.
- Rama: `feature/hackaton`.
- Commit base revisado: `961d130` (`.git/refs/heads/feature/hackaton:1`). **Hay cambios sin commit**: todo `api/`, `docs/architecture/`, `docs/evidence/` y las casillas de `openspec/changes/payment-idempotency-protection/tasks.md`. La revisión es sobre el árbol de trabajo, no sobre un commit inmutable; debe repetirse sobre el commit final. (`git rev-parse --short HEAD` no se pudo ejecutar; el hash se lee de `.git/refs/heads/feature/hackaton` y coincide con `implementation-log.md:5`.)
- Archivos revisados: `api/pyproject.toml`; `api/app/{config,errors,main,schemas}.py`; `api/app/ports/*`; `api/app/repositories/sqlite_store.py`; `api/app/routes/{dependencies,payments,idempotency_audit}.py`; `api/app/services/*`; `api/.gitignore`, `.gitignore`. Pruebas solo por búsqueda de datos/identificadores.
- Fuentes: `docs/architecture/payment-idempotency-protection-impact.md` (sección 14: P-1 a P-6), `docs/WALLET-CONSTITUTION.md:91-94` (principios 16 a 19), `spec.md`, `design.md`, `qe-test-evidence.md`, `implementation-log.md`, `AGENTS.md`.
- Fuera de alcance / no ejecutado: no hay herramienta de ejecución. No se corrieron pruebas, `pip-audit`, scanners (CodeQL, Dependency Review), ni peticiones HTTP. Los resultados citados de pruebas (51/52, 95.83 %) provienen de `implementation-log.md:23-45` y no están verificados por esta revisión. No se revisó el mock ni se usó MCP.

## 2. Lista de revisión

| # | Ítem | Resultado | Evidencia |
|---|---|---|---|
| 1 | Control de acceso / IDOR | **Cumple con salvedad** (identidad suplantable, RS-01, aceptado P-3) | Propiedad verificada en `routes/payments.py:29-33` (GET), `services/retry_service.py:25-27` (retry), 404 uniforme para inexistente y ajeno; `payment_id` es `uuid4().hex` (`services/payment_service.py:30-41`). Feed filtrado por `payer_id` autenticado: `routes/idempotency_audit.py:28-30`, `repositories/sqlite_store.py:68-73, 186-193`. La clave incluye `payer_id` (`services/idempotency_key.py:19-21`), por lo que un POST ajeno no devuelve datos de otro pagador. Falta prueba de 404 por pago ajeno (`implementation-log.md:47`): falta evidencia ejecutable |
| 2 | Validación de entradas | **Cumple con observaciones** (RS-05) | Monto `StrictInt`, `0 < x <= 100_000_000` (`schemas.py:9,19`); destino `Literal` (`schemas.py:13,20`); `intent_id` 1-64 con patrón (`schemas.py:10-11,18`); encabezados `^[A-Za-z0-9._:-]{1,64}$` con `fullmatch` (`routes/dependencies.py:12,25,36`); filtros del feed con largo y patrón (`routes/idempotency_audit.py:14,21-22`). `channel` solo con patrón (`schemas.py:12,21`, sin lista permitida). `payment_id` de ruta sin límite de largo (`routes/payments.py:49,56`); solo se usa parametrizado |
| 3 | Inyección SQL | **Cumple** | Todos los valores van como parámetros `?` (`sqlite_store.py:127-136, 148-152, 162, 167-170, 178-185, 202-205`). Los f-strings (`sqlite_store.py:162, 201, 204`) solo interpolan constantes del código (`REQUEST_FILTER_COLUMNS` `:63-68`, y los literales `"payment_id = ?"`/`"idempotency_key = ?"` en `:154,157`), nunca entrada del usuario. Falta SAST ejecutado |
| 4 | Idempotencia y concurrencia (reserva atómica) | **Cumple con salvedades** (RS-04) | Reserva por `INSERT` con `idempotency_key UNIQUE` (`sqlite_store.py:27,125-141`), commit antes del proveedor (`:117-123` contexto `with con`; `payment_service.py:68-84`); perdedor devuelve `EXISTS` sin llamar al proveedor (`payment_service.py:77-84`); `UPDATE ... AND status = PENDING` impide sobrescribir terminal (`sqlite_store.py:145-152`). Respaldo declarado: 20 hilos, 1 `CREATED` (`implementation-log.md:59`), no verificado aquí. Reserva y `append_request` no son una sola transacción (`payment_service.py:68-76`) |
| 5 | Secretos y configuración | **Cumple** (RS-06 menor) | Sin secretos ni claves en `api/app` (búsqueda de `password/secret/token/debug` sin coincidencias fuera de `.venv`). Configuración por entorno (`config.py:18-24,62-74`). `WALLET_MOCK_URL` vacío (`config.py:37`, P-6) |
| 6 | Registro (logs) | **Cumple** | Solo `payment_id`, estado y política (`payment_service.py:89, 97, 105`); sin `payer_id`, claves, montos ni encabezados. No se registran `request_id`/`correlation_id` |
| 7 | Errores | **Cumple con observación** (RS-08, falta evidencia) | Mensajes genéricos `404`/`409`/`401`/`422` (`payments.py:32,62,65`; `dependencies.py:26,37`); excepciones de dominio sin detalle (`errors.py`). No hay manejador global: el 500 depende del comportamiento por defecto de FastAPI/Starlette (no ejecutado). El cuerpo 422 de Pydantic por defecto refleja el valor enviado: falta evidencia |
| 8 | Datos ficticios (`TEST-`) | **Cumple** | Fixtures y pruebas con `TEST-payer-*` (`tests/conftest.py:8`, `tests/acceptance/test_payment_flow_acceptance.py:2`); destinos `contact-demo`/`merchant-demo`. Sin datos reales encontrados |
| 9 | Dependencias | **Falta evidencia** (RS-08) | `api/pyproject.toml:5` declara `fastapi`, `httpx` sin versión mínima; `:8` `pytest`, `pytest-cov`. No hay lockfile ni `uvicorn` declarado (el diseño sección 3 lo listaba). No se ejecutó auditoría de vulnerabilidades |
| 10 | Límites de tasa y tamaño | **No cumple parcialmente** (RS-02) | Límites por campo presentes (`schemas.py`); sin límite de tamaño de cuerpo, sin límite de tasa, sin cuota por pagador. Principio 17 (`WALLET-CONSTITUTION.md:92`) los nombra; la spec no los exige (`spec.md`, `design.md` sin mención de tasa) |
| 11 | Scanners / `noqa` / quality gates | **Cumple** | Sin `noqa`, `nosec`, `type: ignore` ni `pragma: no cover` en `api/app`; `fail_under = 85` intacto (`pyproject.toml:18`). No se revisaron workflows de CI (no hay en el diff) |
| 12 | Contratos protegidos (principio 18) | **Cumple** | Rutas nuevas únicamente: `/payments`, `/payments/{id}`, `/payments/{id}/retries`, `/idempotency/requests` (`routes/payments.py:37,46,56`; `routes/idempotency_audit.py:16`). No existen `/auth/login`, `/api/*` en este árbol |

## 3. Registro de riesgos

Decisión de todos los riesgos: **pendiente de decisión humana** (nombre y fecha). Estado inicial: abierto, salvo indicación.

### RS-payment-idempotency-protection-01: Identidad por encabezado `X-Payer-Id` suplantable

- Categoría OWASP: A01 Broken Access Control / A07 Identification and Authentication Failures.
- Severidad: alta fuera del MVP; **MVP: riesgo aceptado por decisión P-3** (`docs/architecture/payment-idempotency-protection-impact.md` sección 14). No bloquea.
- Probabilidad: alta si el servicio se expone. Impacto: alto (lectura de pagos del pagador suplantado, creación de pagos y reintentos a su nombre).
- Evidencia: `api/app/routes/dependencies.py:11,31,35-38` (cualquier valor que cumpla el patrón es la identidad; sin credencial ni firma). Toda la autorización del feed y de GET/retry depende de ello: `routes/payments.py:29-33`, `retry_service.py:26`, `idempotency_audit.py:30`.
- Escenario: un cliente envía `X-Payer-Id: TEST-payer-1` y consulta `GET /payments/{id}` / `GET /idempotency/requests` de ese pagador, o reintenta sus pagos. Mitigante: `payment_id` no adivinable, pero el feed devuelve los `payment_id` del pagador suplantado.
- Corrección sugerida: sustituir por identidad de `auth/` (token firmado) antes de datos reales; mientras tanto, no exponer el servicio fuera de entorno local y mantener solo valores `TEST-`.
- Estado: aceptado como MVP por P-3 (documentado); **registrado, sin bloqueo**. Confirmado por lectura de código.

### RS-payment-idempotency-protection-02: Crecimiento ilimitado del registro append-only y sin límites de tasa/cuerpo (DoS)

- Categoría OWASP: A04 Insecure Design / API4 Unrestricted Resource Consumption.
- Severidad: media. Probabilidad: media. Impacto: medio (disco y latencia de SQLite; indisponibilidad de pagos).
- Evidencia: cada solicitud escribe una fila en `payment_requests` (`payment_service.py:75-79`, `sqlite_store.py:177-185`), los triggers prohíben UPDATE y DELETE (`sqlite_store.py:58-61`), no hay purga (`config.py:21`, OQ-13 abierta, `design.md:46`). Sin límite de tasa ni de tamaño de cuerpo en `main.py:25-37`. Cada petición abre varias conexiones SQLite (`sqlite_store.py:115-123`), con `busy_timeout` de 10 s (`:19`).
- Escenario: un cliente repite `POST /payments` con la misma clave a alta frecuencia (todas `duplicate`, 200) o con `X-Payer-Id` variables; el registro crece sin cota y la escritura serializada de SQLite degrada el servicio para todos. Un cuerpo JSON muy grande se lee completo antes de validar (comportamiento del servidor ASGI; falta evidencia ejecutable).
- Corrección sugerida: límite de tasa por pagador y de tamaño de cuerpo en el borde/proxy; decidir OQ-13 (retención y archivado, por ejemplo purga por lote fuera del trigger); cuota por pagador.
- Estado: abierto. Confirmado por lectura que no hay purga ni límites; el efecto real es supuesto (no ejecutado).

### RS-payment-idempotency-protection-03: El feed de auditoría se trunca en silencio en 500 filas y devuelve las más antiguas

- Categoría OWASP: A04 Insecure Design (integridad de auditoría).
- Severidad: media. Probabilidad: alta con volumen. Impacto: medio (conciliación con datos incompletos; las solicitudes recientes no aparecen).
- Evidencia: `sqlite_store.py:21` (`MAX_LISTED_ROWS = 500`), `:204` (`ORDER BY seq LIMIT ?`, ascendente), sin paginación ni indicador de truncamiento (`idempotency_audit.py:16-31`).
- Escenario: un pagador con más de 500 solicitudes no puede ver ni conciliar las últimas; un duplicado reciente queda fuera de la respuesta.
- Corrección sugerida: paginación por cursor (`seq`) o orden descendente con indicador de truncamiento.
- Estado: abierto. Confirmado por lectura.

### RS-payment-idempotency-protection-04: Intentos `PENDING` huérfanos y reserva/auditoría no atómicas

- Categoría OWASP: A04 Insecure Design.
- Severidad: media. Probabilidad: media. Impacto: medio (pago posiblemente cobrado en el proveedor sin resultado local; el pagador no puede reintentar ni reconciliar).
- Evidencia:
  - Solo `ProviderError` se captura (`payment_service.py:92-98`); cualquier otra excepción del proveedor propaga 500 dejando el intento `PENDING` sin log ni actualización (`:85-90`).
  - Una caída entre la reserva (`:68-74`) y `update_attempt` (`:87`) deja `PENDING` para siempre: toda repetición es `duplicate` sin llamar al proveedor (`:77-84`); reintento sobre `PENDING` es 409 (`retry_service.py:28-29`, P-5). `resolve` existe en el puerto (`ports/payment_provider.py:23`) pero nada lo invoca (`implementation-log.md:F-3`, riesgo R-2/H-6 del diseño).
  - `reserve_attempt` (`:68`) y `append_request` (`:75`) son transacciones distintas: una caída intermedia deja un intento sin fila de auditoría `original`.
- Escenario: timeout del proveedor tras procesar (`UNCERTAIN`, `payment_service.py:97-98`): el dinero puede haberse movido y el sistema responde `PENDING` indefinidamente.
- Corrección sugerida: tarea de resolución (`resolve`) para `PENDING` antiguos; capturar excepciones genéricas del proveedor como `UNCERTAIN` con log; escribir reserva y auditoría en una transacción.
- Estado: abierto. Es de alcance parcial de la HU (R-2 del diseño); lo ya reconocido como diferido en `implementation-log.md` F-3 puede registrarse como candidato aparte si el responsable lo decide.

### RS-payment-idempotency-protection-05: `channel` sin lista permitida y fuera de la clave de idempotencia

- Categoría OWASP: A04 Insecure Design / A03 (validación incompleta).
- Severidad: baja. Probabilidad: media. Impacto: bajo.
- Evidencia: `schemas.py:12,21` (cualquier `[a-z0-9-]{1,32}`; OQ-09 abierta); `idempotency_key.py:19` (componentes sin `channel`); `payment_service.py:68-84` (EXISTS ignora el canal solicitado); `config.py:47-49` (retención por canal con valor `default`).
- Escenario: misma intención con otro canal devuelve el pago original sin avisar (el canal enviado se descarta); un canal arbitrario pasa al proveedor (`payment_service.py:94-95`) y evade políticas por canal.
- Corrección sugerida: lista permitida de canales (tras OQ-09) y decidir si el canal es parte de la clave o se rechaza el desajuste con 409.
- Estado: abierto.

### RS-payment-idempotency-protection-06: Base de datos con ruta relativa por defecto, no ignorada por Git

- Categoría OWASP: A05 Security Misconfiguration.
- Severidad: baja. Probabilidad: baja. Impacto: bajo (datos ficticios en MVP).
- Evidencia: `config.py:16` (`idempotency.sqlite3` relativo al directorio de trabajo); `.gitignore:12-14` ignora `*.db*` pero no `*.sqlite3`; `api/.gitignore:1` solo `.venv/`.
- Escenario: un `git add` accidental versiona la base con `payer_id` y claves; ruta dependiente del directorio de ejecución; sin control de permisos del archivo.
- Corrección sugerida: ignorar `*.sqlite3*` (y WAL/SHM), exigir `IDEM_DB_PATH` absoluta fuera del repositorio.
- Estado: abierto.

### RS-payment-idempotency-protection-07: `X-Request-Id` / `X-Correlation-Id` controlados por el cliente y no únicos

- Categoría OWASP: A09 Security Logging and Monitoring Failures (integridad de trazas).
- Severidad: baja. Probabilidad: media. Impacto: bajo.
- Evidencia: `dependencies.py:21-28,38-39` (valor del cliente válido por patrón); `sqlite_store.py:44` (`request_id` sin PK/UNIQUE, decisión D-2 en `implementation-log.md`).
- Escenario: un cliente reutiliza un `correlation_id` de otro para contaminar búsquedas por correlación o repudia una solicitud; el aislamiento por `payer_id` en el feed evita fuga cruzada.
- Corrección sugerida: tratar los IDs del cliente como no confiables, registrar además un identificador interno generado por solicitud.
- Estado: abierto.

### RS-payment-idempotency-protection-08: Dependencias sin versionar y auditoría no ejecutada; manejo global de errores sin verificar

- Categoría OWASP: A06 Vulnerable and Outdated Components / A05.
- Severidad: baja. Probabilidad: baja. Impacto: medio. **Falta evidencia** (no se ejecutó auditoría ni se probó el 500).
- Evidencia: `api/pyproject.toml:5,8` (sin versiones mínimas, sin lockfile, `uvicorn` no declarado); `main.py:25-37` sin manejador global de excepciones.
- Escenario: instalación con versiones vulnerables; un fallo no previsto (por ejemplo `IntegrityError` re-lanzado en `sqlite_store.py:139-140`) depende del manejo por defecto para no filtrar detalles.
- Corrección sugerida: fijar versiones mínimas/lockfile, ejecutar `pip-audit` (o Dependency Review) y añadir un manejador global que devuelva un cuerpo genérico con prueba.
- Estado: abierto (verificación pendiente).

## 4. Decisión por riesgo

| Riesgo | Propuesta del analista | Decisión |
|---|---|---|
| RS-01 | aceptar solo MVP (ya decidido en P-3) | pendiente de decisión humana (confirmar nombre y fecha en el registro) |
| RS-02 | mitigar ahora o diferir con OQ-13 | pendiente de decisión humana |
| RS-03 | mitigar ahora | pendiente de decisión humana |
| RS-04 | mitigar (captura genérica, atomicidad) y diferir `resolve` como candidato | pendiente de decisión humana |
| RS-05 | diferir hasta OQ-09 | pendiente de decisión humana |
| RS-06 | mitigar ahora (cambio trivial) | pendiente de decisión humana |
| RS-07 | aceptar o diferir | pendiente de decisión humana |
| RS-08 | mitigar y reevaluar | pendiente de decisión humana |

El analista no acepta ni difiere riesgos.

## 5. Verificación de corrección

Sin correcciones aún. Se reevaluará cada riesgo contra el commit que las incorpore y se registrará aquí (resultado y commit).

## 6. Confirmado vs supuesto vs falta evidencia

- **Confirmado por lectura de código**: SQL parametrizado; reserva atómica con `UNIQUE`; propiedad verificada en GET/retry y feed filtrado por pagador; validaciones de monto, destino, `intent_id` y encabezados; logs sin datos sensibles; ausencia de `noqa`/exclusiones; contratos protegidos intactos; ausencia de purga, límites de tasa/cuerpo y paginación; RS-01, RS-03, RS-04 (rutas de código), RS-05, RS-06, RS-07.
- **Supuesto**: efecto de DoS real (RS-02); comportamiento del cuerpo grande y del 500 por defecto; resultados de pruebas y cobertura citados del log de desarrollo.
- **Falta evidencia**: auditoría de dependencias; escaneo SAST/CodeQL; pruebas de 404 por pago ajeno, 401/422 de encabezados y filtros de fecha (`implementation-log.md:47`); concurrencia real contra el archivo SQLite en ejecución; revisión de CI (no incluida en el diff).
- **Fuera de alcance, candidatos aparte**: R-1 (cobro doble al cruzar el bucket, aceptado en P-2, no se bloquea); rol de operador para el feed de conciliación (F-1 del log); adaptador real del proveedor (S-6).

## 7. Resumen ejecutivo

| Severidad | Cantidad | Riesgos |
|---|---|---|
| Alta | 1 (aceptada como MVP, P-3) | RS-01 |
| Media | 3 | RS-02, RS-03, RS-04 |
| Baja | 4 | RS-05, RS-06, RS-07, RS-08 |

No se encontraron inyecciones SQL, fugas entre pagadores (condicionado a RS-01), secretos ni supresión de scanners. **Recomendación para la compuerta humana: avanzar condicionado**, sin bloqueo por RS-01 (aceptado en P-3, solo valores `TEST-`). Antes de cerrar la HU se recomienda decidir explícitamente RS-02 a RS-04 (mitigar ahora, diferir o aceptar con nombre y fecha), mitigar RS-06 (trivial) y obtener la evidencia faltante de RS-08 (auditoría de dependencias, prueba del 500). Repetir la revisión sobre el commit final, ya que el árbol revisado tiene cambios sin commit.
