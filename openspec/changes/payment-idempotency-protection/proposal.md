# Proposal

## Fuentes

- Historia de usuario: [Idempotencia en pagos](../../../docs/stories/payment-idempotency-protection.sp.md)
- Épica: [MVP de wallet en Perú](../../../docs/epic/peru-wallet-mvp.sp.md)

## Why

La épica identifica como riesgo que los reintentos sin idempotencia robusta generan duplicidad financiera y desvíos de conciliación. El ecosistema es multirriel, por lo que los controles transaccionales deben ser consistentes sin importar el riel de procesamiento. Hoy varios cambios hermanos mencionan "reintento idempotente" de forma local, pero ninguno define un contrato común; este cambio lo define una sola vez para que los demás lo consuman.

## What Changes

- Cada intento de pago lleva una **clave de idempotencia** única por pagador, monto, destino, ventana de intento e **identificador de intención** (generado por el flujo del pagador al abrir la confirmación; OQ-01 decidida).
- Una solicitud repetida con la misma clave **devuelve el resultado original** y no crea una nueva transacción financiera.
- "Reintentar" tras fallo o expiración crea un **nuevo intento vinculado** al original (nueva clave, nueva referencia, vínculo "reintento de"); la clave original sigue devolviendo el resultado original (OQ-02 decidida).
- Cada solicitud duplicada se registra en un **registro de auditoría de eventos duplicados** con identificador de solicitud e identificador de correlación.
- Las salidas de conciliación **distinguen** los intentos originales de los reintentos duplicados: se expone por solicitud el tipo, el vínculo al original y ambas fechas (de la solicitud y del original); el día de reporte de un duplicado lo decide conciliación después (OQ-14 decidida: diferir).

## Alcance

### Dentro de alcance

- Contrato de la clave de idempotencia (composición, unicidad, ámbito) para intentos de pago, incluido el uso del identificador de intención en la derivación.
- Comportamiento ante solicitud repetida: mismo resultado, sin nueva transacción financiera.
- Vínculo "reintento de" entre un nuevo intento y el original tras fallo o expiración.
- Registro de auditoría de duplicados con identificadores de solicitud y de correlación.
- Marcado de origen (original vs. duplicado) con vínculo al original y ambas fechas, disponible para las salidas de conciliación.
- Comportamiento aplicable a todos los canales/rieles del MVP sin asumir un único riel.

### Fuera de alcance

- Pantallas, textos y flujo del pagador (cambio `payer-low-value-payment-confirmation`); este cambio solo exige que el flujo genere el identificador de intención al abrir la confirmación.
- Rutas de atención, reintentos de soporte, reversos y disputas (cambio `payment-failure-reversal-handling`).
- Generación del reporte de conciliación, descalces, filtros y resumen diario, y la regla que asigna un duplicado a un día de reporte (cambio `ops-transaction-reconciliation`, Fase 2); este cambio solo provee el dato de origen y las fechas.
- Idempotencia/deduplicación de eventos entrantes del proveedor para el estado del comercio (cambio `merchant-qr-payment-status-visibility`).
- Definición de la ventana de retención de claves por canal (pregunta abierta OQ-11; solo hay un valor provisional, propuesta no aprobada).
- Elección de tecnología, almacenamiento o proveedor.
- Todo lo listado como fuera de alcance en la épica (multipaís, lealtad, paridad total de proveedores, APIs abiertas).

## Capabilities

### New Capabilities

- `payment-idempotency`: clave de idempotencia por intento de pago, devolución del resultado original ante solicitudes repetidas, registro de auditoría de duplicados con identificadores de solicitud y correlación, y distinción original/duplicado para conciliación.

### Modified Capabilities

Ninguna. No existen specs previas en `openspec/specs/`.

## Relación con otros cambios

Esta capability es la **dueña** del comportamiento de idempotencia. Los siguientes cambios la **consumen** y no la redefinen:

- `payer-low-value-payment-confirmation`: el requisito "Siguiente acción tras fallo o expiración" y las tareas 5.2 y 5.3 se apoyan en el contrato de clave y en la devolución del resultado original definidos aquí. Su flujo genera el identificador de intención al abrir la confirmación (OQ-01) y "reintentar" crea un nuevo intento vinculado (OQ-02).
- `payment-failure-reversal-handling`: el requisito "Reintento sin duplicidad financiera" y la tarea 2.3 se rigen por este contrato. El reintento de soporte crea un nuevo intento vinculado al original, no reutiliza la clave (OQ-02, decidida).
- `ops-transaction-reconciliation`: consume el marcado original/duplicado de esta capability (tipo, vínculo al original y ambas fechas); el reporte, el resumen diario y la regla de día asignado a un duplicado (OQ-14, diferida a la Fase 2) siguen siendo suyos.
- `merchant-qr-payment-status-visibility` (solape menor): su deduplicación de eventos entrantes del proveedor es un mecanismo distinto (eventos, no solicitudes de pago), pero puede reutilizar el registro de duplicados y los identificadores de correlación.

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | ninguno | Es el cambio base: no consume capabilities de otros cambios. |
| Es consumido por | `payer-low-value-payment-confirmation`, `payment-failure-reversal-handling`, `ops-transaction-reconciliation` | Dependencia fuerte: no pueden cerrar sus pruebas de duplicidad sin este contrato. |
| Reutilizable por | `merchant-qr-payment-status-visibility` | Dependencia opcional (registro de duplicados e identificadores de correlación). |

Orden y justificación completos: [TRACEABILITY.md](../../../docs/TRACEABILITY.md).

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Requisito "Retención de claves configurable por canal" (deriva de la pregunta abierta de la HU; OQ-11).
- Escenarios "Repetición mientras el intento sigue en proceso", "Mismo comportamiento en cualquier riel" y "Una sola transacción por clave" (precisan el criterio 2 y el riesgo multirriel de la épica).
- Escenarios derivados de las decisiones del 2026-11-06 (OQ-01, OQ-02, OQ-14): identificador de intención, reintento vinculado, y datos y fechas expuestos a conciliación.
- Decisión de diseño de reserva atómica de la clave (precisa el criterio 2 ante solicitudes concurrentes).

## Supuestos y preguntas abiertas

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). Estado de las preguntas que afectan a este cambio:

Decididas (2026-11-06; ya no bloquean):

- OQ-01: **Decidida (2026-11-06)**, opción HÍBRIDA: el flujo del pagador genera un identificador de intención al abrir la confirmación y el servidor lo incluye en la derivación de la clave junto con pagador, monto, destino y ventana de intento.
- OQ-02: **Decidida (2026-11-06)**: "reintentar" tras fallo/expiración crea un nuevo intento vinculado al original (nueva clave, nueva referencia, vínculo "reintento de"); la clave original sigue devolviendo el resultado original.
- OQ-14: **Decidida (2026-11-06)**, DIFERIR: esta capability expone tipo (original|duplicado), vínculo al original y ambas fechas; la regla de día de reporte del duplicado la decide conciliación en la Fase 2.

Abiertas (valores provisionales configurables; propuesta, no aprobada):

- OQ-11: ventana de retención de claves por canal (pregunta abierta de la HU). Propuesta: 24 h por canal.
- OQ-12: duración de la ventana de intento que forma parte de la clave. Propuesta: 5 min.
- OQ-13: período de conservación del registro de auditoría de duplicados. Propuesta: sin purga.
- OQ-09: canales exactos del MVP a los que aplica el contrato (incluye si el pago QR del cliente está cubierto; ver OQ-08).

Supuestos (a validar):

- La "ventana de intento" que forma parte de la clave es configurable; su duración no se fija aquí (OQ-12).

## Impact

- El repositorio es greenfield: no hay código de aplicación, por lo que no se referencian archivos ni módulos existentes. El impacto se describe en `design.md` a nivel de componentes lógicos.
- Sistemas afectados (lógicos): servicio de pagos, almacén de claves de idempotencia, registro de auditoría y la fuente de datos de conciliación.
- Dependencias: partners de adquirencia/gateway y rieles de pago (dependencia de la épica); coordinación con los tres cambios hermanos listados arriba.
- Riesgo de la épica que mitiga: duplicidad financiera y desvíos de conciliación por reintentos sin idempotencia robusta.
