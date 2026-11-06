# Proposal

## Why

La caída en checkout de los pagos de bajo monto es de 30% y el objetivo de la épica es llevarla a 8% dentro del trimestre posterior al lanzamiento. Una causa clave de pérdida de confianza es que el pagador no recibe un resultado claro y definitivo (más aún con transiciones asíncronas de estado y riesgo de cobros duplicados por reintentos). Además, las transacciones exitosas deben alimentar el cálculo de MAU (1,000–2,000 en los meses 1-3).

## Fuentes

- Historia de usuario: [Confirmación de pagos de bajo monto](../../../docs/stories/payer-low-value-payment-confirmation.sp.md)
- Épica: [MVP de wallet en Perú](../../../docs/epic/peru-wallet-mvp.sp.md)

## What Changes

- Pantalla de pago que muestra, antes de la confirmación final, la identidad del destino y el monto de la transferencia.
- Validación visible al usuario del monto de bajo valor **antes del envío**, respetando límites por proveedor (que pueden ser menores al máximo regulatorio).
- Resultado terminal **único** por intento de pago: exitoso, fallido o expirado, contemplando transiciones asíncronas de estado.
- En caso de éxito: referencia de transacción mostrada al pagador y persistida en el historial.
- En caso de fallo o expiración: siguiente acción clara (reintentar o volver) sin crear cobros duplicados. La protección contra duplicados la aporta la capability `payment-idempotency` (cambio `payment-idempotency-protection`), que este cambio consume y no redefine.
- Generación y envío del **identificador de intención** al abrir la pantalla de confirmación (decisión OQ-01, híbrida): este flujo solo genera y envía ese identificador; `payment-idempotency` deriva la clave a partir de él más pagador, monto, destino y ventana de intento.
- "Reintentar" tras fallo o expiración crea un **nuevo intento vinculado** al original (nueva clave, nueva referencia, vínculo «reintento de»); la clave original sigue devolviendo el resultado original (decisión OQ-02).
- **Verificación del intento previo** (decisión OQ-03): no se permite un nuevo intento mientras el previo esté en proceso o incierto; sí se permite cuando el previo es terminal (fallido o expirado). Durante el bloqueo se muestra un mensaje accionable y no se crea ningún cobro nuevo.
- Emisión del evento de activación del pagador por cada transacción exitosa, para el reporte de MAU de los meses 1-3. No debe confundirse con el estado de wallet `activo` del onboarding (ver [GLOSSARY.md](../../../docs/GLOSSARY.md)).
- Instrumentación del funnel de checkout y reporte de caída en checkout de la cohorte MVP Perú, para verificar la reducción de 30% a 8% (medible según la definición de OQ-18).

## Alcance

### Dentro de alcance

- Flujo del pagador para transferencias de bajo monto, de la pantalla de confirmación al resultado terminal.
- Estados terminales, referencia de transacción, historial del pagador y siguiente acción (reintentar como nuevo intento vinculado, o volver) tras fallo o expiración, sin cobros duplicados visibles para el pagador (apoyada en `payment-idempotency`); generación y envío del identificador de intención; verificación del intento previo con bloqueo de nuevos intentos mientras el previo esté en proceso o incierto.
- Evento de activación del pagador y eventos de funnel de checkout de este flujo, y el reporte de caída en checkout.
- Cohorte MVP Perú.

### Fuera de alcance

- Onboarding de wallet (otra historia de la épica).
- Cobro a comercios con QR y visibilidad de estado para el comercio (cambio `merchant-qr-payment-status-visibility`).
- Monitoreo y conciliación para operaciones/compliance (cambio `ops-transaction-reconciliation`).
- Políticas operativas/legales de reversos y disputas (cambio `payment-failure-reversal-handling`).
- Derivación de la clave de idempotencia, devolución del resultado original ante solicitudes repetidas y registro de auditoría de duplicados (capability `payment-idempotency`, cambio `payment-idempotency-protection`). Este cambio solo genera y envía el identificador de intención (OQ-01).
- Despliegue multipaís, programas de lealtad, paridad completa entre proveedores/bancos y APIs abiertas de pago (fuera de alcance de la épica).
- Cálculo/reporte consolidado de MAU y CAC; este cambio solo emite el evento de activación con los atributos necesarios para el conteo mensual (responsable del reporte consolidado: OQ-07).
- Definición de la regla inicial de monto bajo y de las etiquetas de estados terminales (ver OQ-15 y OQ-16).
- Tratamiento operativo de la confirmación tardía tras expiración (OQ-10): este cambio solo conserva el resultado terminal y deja disponible la inconsistencia.

## Capabilities

### New Capabilities

- `payer-low-value-payment-confirmation`: confirmación del pago de bajo monto por parte del pagador, con resultado terminal único, referencia persistida en historial, siguiente acción tras fallo o expiración sin cobros duplicados y evento de activación.

### Modified Capabilities

Ninguna. No existen specs previas en `openspec/specs/`.

### Capabilities consumidas

- `payment-idempotency` (dueño: cambio `payment-idempotency-protection`): clave de idempotencia derivada del identificador de intención más pagador, monto, destino y ventana de intento, resultado original ante solicitudes repetidas y auditoría de duplicados. Este cambio no la modifica ni la redefine; solo la usa (enviándole el identificador de intención) para garantizar que reintentos y expiraciones no creen cobros duplicados.

## Preguntas abiertas y decisiones

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

Decididas (2026-11-06):

- OQ-01: **Decidida (2026-11-06)**, opción híbrida. Este flujo genera un identificador de intención al abrir la confirmación y lo envía a `payment-idempotency`, que deriva la clave de ese identificador más pagador, monto, destino y ventana de intento. Este cambio no deriva ni calcula la clave.
- OQ-02: **Decidida (2026-11-06)**, nuevo intento vinculado. "Reintentar" crea un intento nuevo con nueva clave, nueva referencia y vínculo «reintento de» al original; la clave original sigue devolviendo el resultado original.
- OQ-03: **Decidida (2026-11-06)**, conservar y bloquear. Se conserva la verificación del intento previo: no se permite un nuevo intento mientras el previo esté en proceso o incierto; se permite cuando es terminal (fallido o expirado).

Abiertas (no se responden en este cambio):

- OQ-04: momento de asignación de la referencia de transacción (se asume desde la creación del intento; ver `design.md`).
- OQ-05: definición del evento de activación del pagador y su relación con MAU.
- OQ-06: criterio de pertenencia a la cohorte MVP Perú.
- OQ-10: tratamiento de la confirmación tardía de un intento ya expirado.
- OQ-15: regla inicial de monto bajo por proveedor/canal (pregunta abierta de la HU).
- OQ-16: etiquetas de los estados terminales.
- OQ-17: tiempo máximo de un intento antes de expirar.
- OQ-18: definición de "caída en checkout" y de "abandono".

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | `payment-idempotency-protection` | Consume la clave, el resultado original y la auditoría de duplicados. |
| Depende de | `user-onboarding-mvp-completion` | Precondición de acceso: solo una wallet `activo` accede al punto de entrada de pagos de bajo monto (lo garantiza el onboarding, no este cambio). |
| Es consumido por | `payment-failure-reversal-handling` | Estados terminales, referencia de transacción y resultados fallido/expirado que se clasifican. |
| Es consumido por | `ops-transaction-reconciliation` | Estados terminales del intento como estados comparables contra el resultado del proveedor. |

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Requisito "Validación de monto antes del envío" (proviene del contexto de la HU y de la restricción de límites por proveedor de la épica, no de un criterio).
- Requisito "Etiquetas de estados terminales pendientes de definición" (proviene de un supuesto de la HU).
- Escenarios "No se permite confirmar sin datos del destino" y "Estado pendiente antes del resultado" (precisan los criterios 1 y 2).
- Máquina de estados `creado → en_proceso → {exitoso | fallido | expirado}` y tiempo máximo configurable del intento (diseño; OQ-17).
- Requisito «Verificación del intento previo antes de un nuevo intento» (materializa la decisión OQ-03; el alcance «misma intención de pago» y el tratamiento de la consulta fallida como «incierto» son supuestos de análisis).

## Impact

- El repositorio es greenfield: no hay código de aplicación, por lo que no se referencian archivos ni módulos existentes. El impacto se describirá en `design.md` a nivel de componentes lógicos.
- Dependencias externas: partners de adquirencia/gateway y proveedores de pago con límites propios (dependencia de la épica).
- Sistemas afectados (lógicos): pantalla de pago, servicio de pagos/estado, historial, instrumentación de eventos de analítica.
- Dependencia entre cambios: `payment-idempotency-protection` (capability `payment-idempotency`) y `user-onboarding-mvp-completion` (wallet `activo` como precondición). Consumidores de este cambio: `payment-failure-reversal-handling` y `ops-transaction-reconciliation`.
- Riesgos de la épica relevantes: duplicidad financiera por reintentos (mitigada por `payment-idempotency`) y pérdida de confianza por estados asíncronos poco claros.
