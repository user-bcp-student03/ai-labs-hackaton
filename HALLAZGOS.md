# Discovery de API

## Contrato observado en el código

Actualización 2026-11-02: la implementación vigente está distribuida entre
`api/app/routes/`, `api/app/security.py` y `api/app/schemas.py`; la tabla
siguiente refleja los cambios aprobados de api. Las referencias del párrafo
introductorio corresponden al discovery previo a la separación de módulos.

No existe `docs/ENDPOINTS.md`; lo siguiente describe el comportamiento visible en `api/app/main.py`, no un contrato acordado ni validado externamente. Las cinco rutas dependen de `legacy_identity` y requieren un token en `Authorization` con esquema Bearer (api/app/main.py:17, api/app/main.py:68, api/app/main.py:78, api/app/main.py:91, api/app/main.py:108, api/app/main.py:115).

| Método y ruta | Entrada observada | Respuesta observada |
|---|---|---|
| `GET /api/tasks` | La identidad del token determina el owner; un query `owner` no declarado se ignora (api/app/routes/tasks.py:14). | Lista con `id`, `title`, `description`, `status`, `owner`, `priority` y `createdAt` (api/app/schemas.py:15). |
| `POST /api/tasks` | JSON tipado con `title`, `description`, `status` y `priority`; extras, incluido `owner`, se ignoran (api/app/schemas.py:6, api/app/routes/tasks.py:22). | `201` y respuesta `TaskOut` (api/app/schemas.py:15). |
| `GET /api/summary` | La identidad del token determina el owner; un query `owner` no declarado se ignora (api/app/routes/summary.py:14). | `owner`, `total`, `byStatus` y `highPriorityOpen` (api/app/schemas.py:27). |
| `POST /api/requirements` | Multipart con campo `file` (api/app/routes/uploads.py:11). | `201` con `owner`, `fileName`, `storedAt` y `size` (api/app/schemas.py:36). |
| `GET /api/backend-health` | Sin parámetros de ruta; consulta `AUTH_HEALTH_URL` o `http://localhost:8080/q/health` (api/app/routes/backend_health.py:22). | `requestedBy`, `status` y `body` (api/app/schemas.py:45); ante error, conserva forma y devuelve mensaje genérico. |

## Matriz de hallazgos

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | Base64 solo codifica el contenido; el backend compara un secreto hardcodeado y comprueba la expiración, pero no verifica firma, emisor ni audiencia. El token no ofrece integridad criptográfica ni claims verificables. | api/app/security.py:8, api/app/security.py:17, api/app/security.py:19 | alta | Pendiente |
| H-API-02 | api | El cliente puede elegir el owner de lectura y escritura | Vulnerabilidad | `owner` de la query determinaba las tareas listadas y resumidas; además, el JSON permitía asignar el owner al crear una tarea. Nota de resolución: ahora las rutas usan exclusivamente `identity["username"]` e ignoran `owner` enviado por el cliente. | api/app/routes/tasks.py:18, api/app/routes/tasks.py:27, api/app/routes/summary.py:18 | alta | Resuelto |
| H-API-03 | api | Consultas SQL construidas por concatenación | Vulnerabilidad | Los valores de filtros y campos recibidos en la petición se interpolaban en SQL. Nota de resolución: las consultas del repositorio usan parámetros SQLite para filtros, inserts y recuperación por ID. | api/app/repositories/tasks.py:76, api/app/repositories/tasks.py:87, api/app/repositories/tasks.py:94, api/app/repositories/tasks.py:107 | alta | Resuelto |
| H-API-04 | api | Nombre y contenido del archivo subido sin controles | Vulnerabilidad | Se usa el nombre recibido para construir la ruta y se lee el archivo completo sin límite; no se valida extensión ni tamaño. Un nombre con ruta puede escribir fuera del directorio previsto y una carga grande puede agotar recursos. | api/app/routes/uploads.py:12, api/app/routes/uploads.py:17, api/app/routes/uploads.py:18 | alta | Pendiente |
| H-API-05 | api | Dependencias fijadas a versiones señaladas para análisis SCA | Vulnerabilidad | `urllib3==2.5.0` estaba afectado por PYSEC-2026-1994 y `python-multipart==0.0.21` por CVE-2026-24486; se actualizaron a `urllib3==2.8.0` y `python-multipart==0.0.33`. Nota de resolución: las versiones se verificaron con PyPI y las versiones fijadas superan las corregidas de los avisos consultados. | api/requirements.txt:4, api/requirements.txt:5 | media | Resuelto |
| H-API-06 | api | Rutas, persistencia, reglas y serialización concentradas en un módulo | Refactor | `main.py` concentraba la inicialización de SQLite, rutas, reglas y serialización. Nota de resolución: se separaron rutas, servicios, repositorio, esquemas, dependencias y configuración, conservando `create_app` y `app.main:app`. | api/app/main.py:16, api/app/repositories/tasks.py:46, api/app/services/tasks.py:25, api/app/routes/tasks.py:12, api/app/schemas.py:6 | media | Resuelto |
| H-API-07 | api | Tipado crudo, excepciones amplias y lógica duplicada/anidada | Refactor | Los cuerpos y respuestas usaban `dict` con `Any`; había excepciones amplias, lógica duplicada y anidamiento en el resumen. Nota de resolución: se añadieron modelos Pydantic, excepciones específicas con mensajes genéricos, constantes y resumen sin anidamiento profundo. | api/app/schemas.py:6, api/app/schemas.py:15, api/app/schemas.py:27, api/app/security.py:22, api/app/routes/backend_health.py:30, api/app/services/tasks.py:25 | media | Resuelto |
