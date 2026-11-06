# Design

## Context

- El repositorio es **greenfield**: no existe código de aplicación, stack definido ni specs previas en `openspec/specs/`. Este diseño describe componentes lógicos y no referencia archivos existentes.
- Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/payment-idempotency/spec.md`.
- Restricciones de la épica ([peru-wallet-mvp](../../../docs/epic/peru-wallet-mvp.sp.md)): ecosistema multirriel (no asumir un único riel), riesgo de duplicidad financiera y desvíos de conciliación por reintentos sin idempotencia, expectativa de pagos inmediatos 24x7x365.
- Los cambios hermanos `payer-low-value-payment-confirmation`, `payment-failure-reversal-handling` y `ops-transaction-reconciliation` consumen el contrato común definido aquí; `merchant-qr-payment-status-visibility` puede reutilizar el registro de duplicados.
- Terminología (intento de pago, transacción financiera, referencia, reintento duplicado, original): ver [GLOSSARY.md](../../../docs/GLOSSARY.md). Preguntas abiertas: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

## Goals / Non-Goals

**Goals:**

- Un contrato único de clave de idempotencia independiente del riel.
- Registro atómico de la clave y de la transacción, de modo que dos solicitudes simultáneas con la misma clave no creen dos transacciones.
- Auditoría de duplicados con identificadores de solicitud y de correlación.
- Un atributo de origen (original/duplicado) consumible por conciliación.

**Non-Goals:**

- Definir la ventana de retención por canal (pregunta abierta de la HU).
- Diseñar la pantalla del pagador, la ruta de soporte/reversos o el reporte de conciliación (otros cambios).
- Deduplicación de eventos entrantes del proveedor (cambio `merchant-qr-payment-status-visibility`).
- Elegir tecnología, almacenamiento o gateway.

## Decisions

1. **Clave compuesta por pagador, monto, destino, ventana de intento e identificador de intención (OQ-01: Decidida (2026-11-06), opción HÍBRIDA).** El flujo del pagador genera un identificador de intención cuando se abre la pantalla de confirmación; el servidor lo incluye en la derivación de la clave junto con pagador, monto, destino y ventana de intento. Cubre el doble toque y el reintento por red (mismo identificador de intención → duplicado) sin tratar como duplicados a pagos legítimos idénticos (identificador distinto dentro de la ventana → clave distinta). La duración de la ventana es configurable y no se fija aquí (OQ-12, abierta; propuesta provisional de 5 min, no aprobada). *Alternativas descartadas:* clave solo derivada (trata como duplicado a dos pagos idénticos intencionales en la misma ventana) y clave aleatoria generada por el cliente por envío (no cubre reenvíos tras reinicio de la app o desde otro dispositivo).
2. **Registro atómico "clave → transacción/resultado".** La primera solicitud con una clave reserva la clave antes de procesar; las siguientes encuentran la reserva y reciben el estado o resultado original. *Alternativa:* verificar existencia y luego insertar; descartada por condición de carrera entre solicitudes concurrentes.
3. **Resultado original inmutable.** El resultado asociado a la clave es el del intento original; no se recalcula ni se sobrescribe por solicitudes posteriores. Si el original aún está en proceso, se devuelve su estado actual.
4. **Registro de duplicados append-only.** Cada solicitud duplicada genera una entrada nueva con identificador de solicitud, identificador de correlación y clave; no modifica el registro original. Permite auditoría y trazabilidad original ↔ duplicado.
5. **Atributo de origen para conciliación (OQ-14: Decidida (2026-11-06), opción DIFERIR).** Cada solicitud expone el tipo (`original` | `duplicado`), el vínculo al original, la fecha de la solicitud y la fecha del original. La regla que asigna un duplicado a un día de reporte no se define aquí: la decide conciliación en la Fase 2. Conciliación lo consume; este cambio solo expone el dato y no genera reportes.
6. **Contrato independiente del riel.** La capa de idempotencia se ubica antes de la interfaz de proveedor, de modo que el comportamiento sea el mismo para cualquier canal.
7. **Retención configurable por canal.** La vigencia de la clave se lee de configuración por canal. Valor provisional de 24 h por canal (OQ-11, abierta): propuesta, no aprobada.
8. **"Reintentar" crea un nuevo intento vinculado (OQ-02: Decidida (2026-11-06)).** Tras un resultado fallido o expirado, "reintentar" crea un nuevo intento con nueva clave y nueva referencia, vinculado al original con el vínculo "reintento de". La capability almacena el vínculo reintento → original. La clave original sigue devolviendo el resultado original (decisión 3) y el reintento no es un duplicado. *Alternativa descartada:* reutilizar la clave original, que devolvería siempre el resultado original e impediría reintentar.

## Risks / Trade-offs

- [Colisión de claves legítimas: dos pagos idénticos intencionales dentro de la misma ventana] → Mitigado por el identificador de intención (decisión 1): cada pago legítimo tiene su propio identificador y por tanto su propia clave.
- [Un cliente que reutilice el identificador de intención en un pago distinto lo trataría como duplicado] → El flujo del pagador debe generar un identificador nuevo por cada apertura de la confirmación; se verifica en la integración con `payer-low-value-payment-confirmation`.
- [Ventana de retención corta permite que un reintento tardío cree una segunda transacción] → Mantener la retención configurable por canal y ajustarla cuando se apruebe la propuesta de OQ-11.
- [Solicitudes concurrentes con la misma clave] → Reserva atómica de la clave (decisión 2).
- [Solapamiento con los cambios hermanos genera definiciones divergentes de clave] → Los hermanos consumen este contrato, ya con OQ-01 y OQ-02 decididas; deben alinear sus artefactos a las decisiones 1 y 8.
- [Un duplicado cuyo original cae en otro día podría reportarse en un día no deseado] → Esta capability expone ambas fechas sin asignar día; la regla queda diferida a conciliación (Fase 2, OQ-14).
- [Volumen del registro de duplicados] → Propuesta provisional "sin purga" (OQ-13, abierta; propuesta, no aprobada); política definitiva por acordar con operaciones/compliance.
- [Dependencia de partners/gateways aún no habilitados] → Aislar la integración tras una interfaz de proveedor; no asumir un riel único.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

Decididas (2026-11-06; ya no bloquean):

- OQ-01: **Decidida (2026-11-06)**, opción híbrida con identificador de intención (decisión 1).
- OQ-02: **Decidida (2026-11-06)**, "reintentar" crea un nuevo intento vinculado al original (decisión 8).
- OQ-14: **Decidida (2026-11-06)**, DIFERIR: se exponen tipo, vínculo al original y ambas fechas; el día de reporte lo decide conciliación en la Fase 2 (decisión 5).

Abiertas (valores provisionales configurables, propuesta, no aprobada):

- OQ-11: ventana de retención de claves por canal (pregunta abierta de la HU) y comportamiento ante una clave fuera de la ventana. Propuesta: 24 h por canal.
- OQ-12: duración de la ventana de intento. Propuesta: 5 min.
- OQ-13: período de conservación del registro de auditoría de duplicados. Propuesta: sin purga.

Supuestos (sin resolver):

- Los valores provisionales de OQ-11, OQ-12 y OQ-13 son configurables y no se codifican; su aprobación queda pendiente de producto, operaciones/compliance.
