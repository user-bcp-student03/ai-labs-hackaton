# Plan de corrección

## api

### Alcance y decisiones registradas

| Tema | Decisión | Fuente |
|---|---|---|
| Hallazgos incluidos | H-API-01 a H-API-07 (los 7 en estado "Pendiente") | Respuesta del usuario |
| Parámetro `owner` | Opción (a): eliminar `owner` de las consultas y usar siempre `identity["username"]` del token. El campo `owner` del cuerpo de `POST /api/tasks` también deja de decidir el owner. | Respuesta del usuario |
| Token (H-API-01) | Incluido. Se aprueba la dependencia **PyJWT** para verificar firma, emisor, audiencia y expiración. | Respuesta del usuario |
| Límites de carga (H-API-04) | **Pendiente.** El usuario no indicó extensiones permitidas ni tamaño máximo. No se fijan valores en este plan. | Respuesta del usuario (vacío) |
| Consulta de advisories (H-API-05) | Sí, consultada en la web (ver H-API-05). | Respuesta del usuario |
| Aprobación humana para implementar | Aprobados H-API-01 a H-API-07 por Ricardo RG, según confirmación explícita del usuario en esta sesión. | Confirmación del usuario |
| Contrato de endpoints | `docs/ENDPOINTS.md` no existe. Se conserva el comportamiento observado en `api/app/main.py`, salvo los cambios aprobados arriba. | AGENTS.md / instrucciones del paso |
| Código | No se modificó código en esta etapa. | Restricción del paso |

### Contrato observado que se mantiene

Cada punto indica si el cambio propuesto lo modifica. Los cambios marcados
"aprobado" salen de la decisión del usuario.

| Método y ruta | Comportamiento observado (api/app/main.py) | Cambio propuesto |
|---|---|---|
| `GET /api/tasks` | Lista tareas del owner, orden por `id`, campos `id,title,description,status,owner,priority,createdAt` (api/app/main.py:68-75). | Sin `owner` en la query; siempre tareas de `identity["username"]`. Cambio aprobado (H-API-02). |
| `POST /api/tasks` | `201`; defaults `status=TODO`, `priority=MEDIUM`; devuelve la tarea creada (api/app/main.py:78-88). | El `owner` del cuerpo se ignora; siempre `identity["username"]`. Cambio aprobado (H-API-02). |
| `GET /api/summary` | `owner,total,byStatus,highPriorityOpen` (api/app/main.py:91-105). | Sin `owner` en la query. Cambio aprobado (H-API-02). |
| `POST /api/requirements` | `201` con `owner,fileName,storedAt,size` (api/app/main.py:108-112). | `fileName` y `storedAt` pueden cambiar por normalización (H-API-04); límites pendientes. |
| `GET /api/backend-health` | `requestedBy,status,body`; consulta `AUTH_HEALTH_URL` o `http://localhost:8080/q/health` (api/app/main.py:114-121). | Sin cambio de contrato. |
| Errores 401 | `401` con `detail` que incluye `str(error)` (api/app/main.py:25-26). | Sin cambio de código de estado; el texto del detalle se vuelve genérico (ver H-API-07). |

**Riesgo de compatibilidad a confirmar:** el cambio de `owner` puede romper
clientes que hoy envían `owner`. Esto no se verificó porque el alcance excluye
otros componentes. Queda como pendiente de coordinación (ver sección de
pendientes).

---

### Orden de ejecución propuesto

1. Pruebas de caracterización de todo el comportamiento actual (sin cambios de código).
2. H-API-05: actualizar `urllib3` y `python-multipart` (sin cambio de contrato).
3. H-API-06: extraer capas sin cambiar comportamiento.
4. H-API-03 y H-API-02: SQL parametrizado y autorización por identidad sobre la capa de repositorio/servicio.
5. H-API-07: modelos Pydantic y excepciones específicas.
6. H-API-04: carga segura de archivos (cuando existan los límites).
7. H-API-01: verificación JWT (depende de coordinación con `auth/`).

H-API-06 va antes de H-API-03/02 porque esas correcciones necesitan un
repositorio separado de la ruta; sin esa separación, el SQL parametrizado
quedaría dentro de la función de ruta, contra GOOD_PRACTICES.md.

---

### H-API-01: Token Base64 con secreto embebido y sin firma

**Hallazgo (HALLAZGOS.md):** Token Base64 con secreto embebido y sin firma;
severidad alta; estado Pendiente.

**Problema:** `legacy_identity` decodifica Base64, separa por `|` y compara
`parts[3]` contra `LEGACY_SECRET = "WORKSHOP_SECRET_2026"` (api/app/main.py:14,
api/app/main.py:17-26). Quien conozca el código puede fabricar tokens válidos.
Base64 no garantiza integridad ni claims verificables. GOOD_PRACTICES.md pide
"verificar firma, emisor, audiencia y expiración".

**Cambio propuesto:**
- Reemplazar la verificación por JWT con **PyJWT** (dependencia aprobada):
  `jwt.decode(token, secret, algorithms=["HS256"], audience=..., issuer=...)`.
  El algoritmo se fija en la lista para evitar `none` y cambios de algoritmo.
- El secreto sale del código: variable de entorno (por ejemplo
  `WORKSHOP_JWT_SECRET`), sin valor por defecto en el código. Si falta, la app
  debe fallar al arrancar, no usar un valor de prueba.
- Emisor, audiencia y tiempo de vida como constantes con nombre en
  `app/config.py` (no números mágicos como `3600`).
- Claims explícitos: `sub` (username), `role`, `exp`, `iss`, `aud`.
- Las rutas usan solo el dict/modelo que devuelve la verificación; no decodifican nada.
- El texto de error del 401 es genérico (ver H-API-07).

**Archivos a tocar:** `api/app/security.py` (nuevo: verificación y dependencia
`get_identity`), `api/app/config.py` (nuevo: variables de entorno y constantes),
`api/app/main.py` (quitar `legacy_identity` y `LEGACY_SECRET`),
`api/requirements.txt` (agregar `PyJWT` con versión fijada, por confirmar en
PyPI al resolver la coordinación), `api/tests/`.

**Pruebas de caracterización (antes de tocar):**
- `test_accepts_current_token_format_and_identity`: documenta que hoy un token
  `user|ROLE|exp|SECRET` en Base64 devuelve `username` y `role`. Se marcará como
  cambio esperado, porque ese formato dejará de aceptarse.
- `test_rejects_expired_token` y `test_rejects_wrong_secret` con respuesta `401`.
- `test_rejects_missing_authorization_header` (hoy: `401` porque `""` no tiene 4 partes).
- `test_rejects_malformed_base64` con `401`.

**Dependencia externa (coordinar, fuera del alcance de api):** el token lo emite
el componente `auth/`. Hasta que `auth/` emita JWT con las mismas claims, `api/`
no podrá validar tokens reales del flujo completo. No se modifica `auth/` aquí;
queda como pendiente de coordinación con H-AUTH.

---

### H-API-02: El cliente puede elegir el owner de lectura y escritura

**Hallazgo (HALLAZGOS.md):** El cliente puede elegir el owner de lectura y
escritura; severidad alta; estado Pendiente.

**Problema:** `list_tasks` y `summary` usan `owner or identity["username"]`
(api/app/main.py:69, api/app/main.py:92). `create_task` acepta `owner` del JSON
(api/app/main.py:83). Un usuario puede leer o crear tareas de otro owner. GOOD_PRACTICES.md
pide consultas siempre con `identity["username"]`.

**Cambio propuesto (opción a, aprobada):**
- Eliminar el parámetro `owner` de `GET /api/tasks` y `GET /api/summary`.
- En `POST /api/tasks` ignorar `owner` del cuerpo; el owner es siempre
  `identity["username"]`.
- Los filtros se delegan a un repositorio que recibe el owner ya verificado.

**Archivos a tocar:** `api/app/routes/tasks.py` y `api/app/routes/summary.py`
(nuevos, o funciones dentro de `api/app/routes/`), `api/app/services/tasks.py`
(nuevo), `api/app/repositories/tasks.py` (nuevo), `api/app/main.py`, `api/tests/`.

**Pruebas de caracterización (antes de tocar):**
- `test_lists_seeded_tasks` (ya existe): owner `student`, 2 tareas.
- `test_list_accepts_owner_query_today`: documenta que hoy `?owner=trainer`
  devuelve 1 tarea. Se marcará como cambio esperado: tras el cambio,
  `?owner=trainer` devuelve las tareas del token (`student`).
- `test_creates_task_and_summary` (ya existe): `created.owner == "student"`.
- Nueva: `test_create_ignores_owner_in_body`: hoy el owner del cuerpo se
  guarda; tras el cambio, siempre es el del token.

---

### H-API-03: Consultas SQL construidas por concatenación

**Hallazgo (HALLAZGOS.md):** Consultas SQL construidas por concatenación;
severidad alta; estado Pendiente.

**Problema:** Se concatenan valores en `list_tasks` (api/app/main.py:70),
`create_task` (api/app/main.py:84, 87), y `summary` (api/app/main.py:93).
Una comilla en `title` rompe el `INSERT` (hoy da error 500, comportamiento a
caracterizar). La concatenación permite modificar la consulta.

**Cambio propuesto:**
- Repositorio con consultas parametrizadas: `connection.execute("... WHERE owner = ?", (owner,))`
  y `INSERT ... VALUES (?, ?, ?, ?, ?, datetime('now'))`.
- Obtener la fila insertada con `cursor.lastrowid` y parámetro, no con concatenación.
- Ninguna función de ruta contiene SQL (GOOD_PRACTICES.md).

**Archivos a tocar:** `api/app/repositories/tasks.py` (nuevo),
`api/app/main.py`, `api/tests/`.

**Pruebas de caracterización (antes de tocar):**
- Listado y creación de casos normales: `status` 201, forma de la respuesta,
  `createdAt` como texto.
- `test_title_with_quote_round_trips`: marcado `xfail` hoy (por el error 500);
  tras el cambio debe pasar. Se usa un título con apóstrofe normal, sin cadenas
  de inyección.
- `test_summary_counts` (ver H-API-07) para no cambiar los conteos al pasar a parámetros.

---

### H-API-04: Nombre y contenido del archivo subido sin controles

**Hallazgo (HALLAZGOS.md):** Nombre y contenido del archivo subido sin
controles; severidad alta; estado Pendiente.

**Problema:** `target = Path(selected_uploads) / str(file.filename)` usa el
nombre recibido tal cual (api/app/main.py:109). El contenido se lee completo
en memoria sin límite (api/app/main.py:110) y sin validar extensión ni tamaño.
GOOD_PRACTICES.md pide normalizar el nombre, limitar extensión y tamaño antes de guardar.

**Cambio propuesto:**
- Normalizar el nombre: usar solo el nombre base, rechazar separadores y nombres
  vacíos, y, si hace falta, generar un nombre propio (por ejemplo UUID) y guardar
  el original solo como metadato.
- Validar extensión contra una lista permitida (constante con nombre).
- Validar tamaño máximo antes de escribir: leer en bloques hasta un límite y
  responder error de cliente si se excede.
- Verificar que la ruta final quede dentro de `upload_dir` antes de escribir.

**Límites: PENDIENTE.** Las extensiones permitidas y el tamaño máximo no
fueron indicados por el usuario. No se fijan valores; hasta confirmarlos, el
paso no se implementa.

**Archivos a tocar:** `api/app/services/uploads.py` (nuevo),
`api/app/config.py` (constantes de límites, una vez confirmadas),
`api/app/main.py`, `api/tests/`.

**Pruebas de caracterización (antes de tocar):**
- `test_uploads_requirement` (ya existe): archivo `requirements.txt`, `201`,
  archivo guardado con ese nombre. Tras el cambio, el nombre `requirements.txt`
  debe conservarse si cumple las reglas, o documentarse el cambio.
- `test_upload_response_shape`: claves `owner,fileName,storedAt,size`.
- Nueva, sin payloads de explotación: nombre con separador de directorio
  (caso neutral `carpeta/archivo.txt`) para verificar que hoy se guarda fuera de
  la base y que tras el cambio se rechaza o normaliza.

---

### H-API-05: Dependencias fijadas a versiones señaladas para análisis SCA

**Hallazgo (HALLAZGOS.md):** Dependencias fijadas a versiones señaladas para
análisis SCA; severidad media; estado Pendiente.

**Problema:** `api/requirements.txt` fija `urllib3==2.5.0` (línea 4) y
`python-multipart==0.0.21` (línea 5).

**Evidencia consultada (web, sin payloads):**
- `urllib3` 2.5.0 y anteriores: PYSEC-2026-1994 (consumo excesivo de CPU y
  memoria al descomprimir respuestas streaming, CWE-409). Corrección: **>= 2.6.0**.
  Relevante para `backend_health` (api/app/main.py:118), que usa `urllib3`.
- `python-multipart` < 0.0.22: CVE-2026-24486 / PYSEC-2026-1852 (escritura de
  archivos fuera del directorio con `UPLOAD_DIR` y `UPLOAD_KEEP_FILENAME=True`).
  Corrección: **>= 0.0.22**. La app usa la configuración por defecto, que según
  el aviso no es vulnerable; aun así se actualiza, porque la configuración
  depende de cómo se use y es parte de la práctica del proyecto.

**Cambio aplicado:** se fijaron `urllib3==2.8.0` y
`python-multipart==0.0.33`, las versiones más recientes publicadas en PyPI al
verificarlas el 2026-11-02. Son posteriores a las versiones corregidas para
los avisos identificados. La instalación con FastAPI 0.128.2 y pydantic
2.13.4 terminó correctamente.

**Archivos a tocar:** `api/requirements.txt`.

**Pruebas de caracterización (antes de tocar):** suite completa existente en
`api/tests/test_api.py` debe seguir pasando. Verificación de versión: consulta
de `importlib.metadata` en una prueba que confirme las versiones mínimas.

**Evidencia consultada:** los avisos oficiales de urllib3 indican que
2.8.0 corrige [GHSA-gh4c-6fx4-qh6g](https://github.com/urllib3/urllib3/security/advisories/GHSA-gh4c-6fx4-qh6g)
y que versiones anteriores a 2.8.0 tienen
[GHSA-vxq7-64xx-v4gw](https://github.com/urllib3/urllib3/security/advisories/GHSA-vxq7-64xx-v4gw)
y [GHSA-8988-9cw3-xx77](https://github.com/urllib3/urllib3/security/advisories/GHSA-8988-9cw3-xx77).
PYSEC-2026-1994 se corrige desde 2.6.0. Para python-multipart,
[CVE-2026-24486](https://nvd.nist.gov/vuln/detail/CVE-2026-24486) se corrige
desde 0.0.22; también se consultó
[CVE-2026-53539](https://nvd.nist.gov/vuln/detail/CVE-2026-53539), afectado
antes de 0.0.30. Los pins elegidos quedan por encima de esos límites. No se
instaló ni ejecutó `pip-audit`; no se afirma que se haya escaneado el árbol
transitivo completo.

---

### H-API-06: Rutas, persistencia, reglas y serialización concentradas en un módulo

**Hallazgo (HALLAZGOS.md):** Rutas, persistencia, reglas y serialización en un
módulo; severidad media; estado Pendiente.

**Problema:** `create_app` mezcla creación de tablas y datos semilla
(api/app/main.py:29-42), el middleware CORS (api/app/main.py:48-54), `as_task`
(api/app/main.py:56-64), las rutas (api/app/main.py:67-121), la lógica de
`summary` y el cierre de conexión (api/app/main.py:123-124).

**Cambio propuesto (estructura):**
- `app/config.py`: variables de entorno y constantes.
- `app/security.py`: verificación de identidad (H-API-01).
- `app/schemas.py`: modelos Pydantic de request y response (H-API-07).
- `app/repositories/tasks.py`: SQL parametrizado; creación de tabla y semilla.
- `app/services/tasks.py`: reglas (resumen, prioridad abierta, defaults).
- `app/routes/*.py`: rutas FastAPI que solo llaman al servicio.
- `app/main.py`: `create_app(db_path=None, upload_dir=None)` y `app = create_app()`.

Se conservan `create_app` y `app.main:app`, porque el `Dockerfile` usa
`uvicorn app.main:app` (api/Dockerfile) y las pruebas importan `create_app`
desde `app.main`.

**Archivos a tocar:** `api/app/main.py` y los nuevos módulos listados.

**Pruebas de caracterización (antes de tocar):** las cuatro pruebas existentes
en `api/tests/test_api.py` más las de H-API-01 a H-API-04. Un test debe confirmar
que `from app.main import create_app` y `app.main:app` siguen funcionando.

---

### H-API-07: Tipado crudo, excepciones amplias y lógica duplicada/anidada

**Hallazgo (HALLAZGOS.md):** Tipado crudo, excepciones amplias y lógica
duplicada/anidada; severidad media; estado Pendiente.

**Problema:**
- `dict[str, Any]` en el cuerpo de `create_task` (api/app/main.py:78) y en las
  respuestas (api/app/main.py:56, 91).
- `except Exception` en `legacy_identity` (api/app/main.py:25) y en
  `backend_health` (api/app/main.py:120).
- La selección `owner or identity["username"]` se repite (api/app/main.py:69, 92).
- `summary` tiene cuatro niveles de `if`/`else` anidados (api/app/main.py:95-104)
  y repite `response["total"] = response["total"] + 1`.
- Los datos por defecto son números y cadenas sueltas: `"TODO"`, `"MEDIUM"`,
  `"HIGH"`, `"DONE"`, `"ARCHIVED"`, `3.0` de timeout (api/app/main.py:81-82, 101-103, 118).
- Mensajes de error con `str(error)` en 401 (api/app/main.py:26) y en
  `backend_health` (api/app/main.py:121); GOOD_PRACTICES.md pide mensajes genéricos.

**Cambio propuesto:**
- Modelos Pydantic de entrada (`TaskCreate`, con defaults `TODO` y `MEDIUM`) y
  salida (`TaskOut`, `SummaryOut`, `UploadOut`).
- Constantes con nombre para estados, prioridades y timeout.
- Excepciones específicas: capturar solo `jwt` errors y errores de `urllib3`;
  `HTTPException` con mensaje genérico; detalle al log del servidor.
- Función `summary` dividida: contar por estado, contar prioridad abierta, con
  guard clauses o una condición combinada en lugar de anidamiento.
- Un único helper para obtener el owner (ya no necesario tras H-API-02).

**Archivos a tocar:** `api/app/schemas.py` (nuevo), `api/app/services/tasks.py`,
`api/app/config.py`, `api/app/routes/*.py`, `api/app/security.py`.

**Pruebas de caracterización (antes de tocar):**
- `test_create_defaults_status_and_priority` (hoy: sin `status` → `TODO`, sin
  `priority` → `MEDIUM`).
- `test_summary_high_priority_open`: HIGH abierto cuenta; HIGH con `DONE` o
  `ARCHIVED` no cuenta; MEDIUM no cuenta.
- `test_summary_by_status_counts`.
- `test_invalid_json_body_today`: documenta el código actual ante un cuerpo
  inválido (hoy `422` de FastAPI) para comparar tras el modelo Pydantic.
- Verificar que el 401 mantiene el código de estado y que el `detail` ya no
  contiene texto interno.

---

### Pendientes y observaciones

| Pendiente | Motivo | Quién lo resuelve |
|---|---|---|
| Límites de carga (extensiones y tamaño) para H-API-04 | El usuario dejó el campo vacío | Usuario |
| Emisión de JWT en `auth/` para H-API-01 | El token lo emite otro componente; fuera del alcance de api | Coordinar con H-AUTH |
| Compatibilidad del cambio de `owner` con clientes | Verificarlo requiere mirar otro componente, fuera del alcance | Coordinar con el responsable de web |
| Observación sin ID: `backend_health` devuelve `str(error)` en el cuerpo (api/app/main.py:121) | No tiene ID en HALLAZGOS.md; no se renumera ni se crea ID aquí | Decidir si se registra como H-API-08 |
| Observación sin ID: CORS con `allow_origins=["*"]` y `allow_credentials=True` (api/app/main.py:48-54) | No tiene ID en HALLAZGOS.md | Decidir si se registra |
| Evidencia de pruebas: no hay `docs/TESTING.md` | El documento no existe; cada ejecución se registrará al ejecutarla | Pendiente de la fase de implementación |

### Comandos de verificación (a ejecutar en la fase de implementación)

- Desde `api/`: `python -m pytest --cov=app` (`pytest` y `pytest-cov` están en `requirements-dev.txt`).
- Meta de cobertura del código modificado: 85% o superior (AGENTS.md, api).
- Desde la raíz: `python tools/lab.py test api` (alternativa, según corresponda).

## Registro de implementación — 2026-11-02

### Estado por hallazgo

| ID | Estado | Implementación / bloqueo |
|---|---|---|
| H-API-01 | Pendiente | No se cambió el formato Base64. Falta coordinar con `auth/` la emisión del JWT y sus claims; fuera del alcance de api. |
| H-API-02 | Resuelto | `GET /api/tasks` y `GET /api/summary` usan la identidad del token; `POST /api/tasks` ignora `owner` del cuerpo. |
| H-API-03 | Resuelto | Las operaciones del repositorio usan parámetros SQLite para filtros, inserts y recuperación de filas. |
| H-API-04 | Pendiente | No se implementó validación de extensión, normalización segura ni límite de lectura. El usuario no definió extensiones permitidas ni tamaño máximo. |
| H-API-05 | Resuelto | Pins actualizados a `urllib3==2.8.0` y `python-multipart==0.0.33`; solo se afirma la corrección de los avisos citados, no un análisis transitivo completo. |
| H-API-06 | Resuelto | Se separaron rutas, servicios, repositorio, esquemas, dependencias, seguridad y configuración; se mantienen `create_app` y `app.main:app`. |
| H-API-07 | Resuelto | Request/response Pydantic, excepciones específicas, errores genéricos, constantes y resumen sin anidamiento profundo. |

### Caracterización y corrección por hallazgo

| ID | Antes del cambio | Después del cambio |
|---|---|---|
| H-API-01 | Los tests existentes enviaban el formato Base64 actual. | No se cambió el formato ni se completó el test de JWT porque sigue pendiente coordinar el emisor de `auth/`; sin resultado correctivo para este ID. |
| H-API-02 | `test_owner_query_can_select_another_owner_today` y `test_create_task_accepts_owner_from_request_today` pasaron con `owner=trainer`, demostrando la selección/asignación del owner del cliente. | Sus versiones actualizadas verifican que query/body no alteran la identidad `student`; ambas pasan. |
| H-API-03 | `test_task_title_with_apostrophe_round_trips` quedó como `xfail` porque SQLite rechazó el título. | Se retiró `xfail`; el título con apóstrofe se crea y recupera correctamente. |
| H-API-04 | `test_uploads_requirement` caracterizó una carga permitida; no se ejecutó una caracterización de límites porque no fueron definidos. | La ruta y el comportamiento vulnerable de nombre/lectura permanecen; no se declara corrección ni resultado posterior para el control de archivo. |
| H-API-05 | `test_dependency_versions_before_update` pasó con los pins `urllib3==2.5.0` y `python-multipart==0.0.21`. | `test_dependency_versions_after_update` pasa con pins exactos `urllib3==2.8.0` y `python-multipart==0.0.33`; instalación de requirements correcta. |
| H-API-06 | `test_app_factory_and_import_entrypoint_are_available` y la suite existente pasaron antes del refactor. | La misma prueba y la suite siguen pasando; se conserva `app.main:app` y `create_app`. |
| H-API-07 | Las pruebas previas confirmaron defaults, resumen, 422 sin body y que los mensajes de token/backend exponían detalles internos. | Las pruebas actualizadas verifican defaults y resumen equivalentes, 422, `401` genérico y body backend genérico con el mismo formato; pasan. |

### Ejecuciones registradas

Todas las ejecuciones de pytest se hicieron con cwd `api/`. Las pruebas de
caracterización de H-API-02, -03, -05, -06 y -07 precedieron a los cambios de
implementación.

| Fecha | Comando | Componente / IDs | Resultado |
|---|---|---|---|
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing` | api; H-API-02, -03, -06, -07 | No inició: el intérprete no tenía pytest instalado. Se instalaron las dependencias ya declaradas en `requirements.txt` y `requirements-dev.txt`. |
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing` | api; H-API-02, -03, -06, -07 | Falló la caracterización: 9 passed, 1 failed, 1 xfailed. La aserción esperaba 3 tareas `TODO`, pero la fixture observada contenía 2; se corrigió el conteo del test antes de modificar la implementación. |
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing` | api; H-API-02, -03, -06, -07 | Caracterización corregida: 10 passed, 1 xfailed; cobertura 93%. |
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing` | api; H-API-02, -03, -05, -06, -07 | Caracterización ampliada antes del cambio: 13 passed, 1 xfailed; cobertura 97%. |
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing` | api; H-API-02, -03, -05, -06, -07 | Después de implementar: 14 passed; cobertura 97%. |
| 2026-11-02 | `python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=85` | api; H-API-02, -03, -05, -06, -07 | 15 passed; cobertura total 97.96%, supera el umbral 85%. Se observaron dos warnings (deprecación de Starlette/AnyIO y conexión SQLite global no cerrada por la prueba). |

**Desviaciones y límites:** se implementaron H-API-02, -03, -05, -06 y -07.
H-API-01 y H-API-04 siguen pendientes por dependencias de coordinación/datos
que no están disponibles en el alcance aprobado. No se creó
`docs/ENDPOINTS.md` ni `docs/TESTING.md`. Las pruebas se ejecutaron con Python
3.14.7, aunque README.md recomienda Python 3.13 para api.
