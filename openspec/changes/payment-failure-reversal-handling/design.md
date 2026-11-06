# Design

## Context

El repositorio es greenfield: no existe código de aplicación, por lo que este diseño no referencia archivos, módulos ni APIs existentes. Describe un enfoque conceptual a validar al elegir el stack. Motivación en `proposal.md` (ver "Why"); requisitos en `specs/payment-failure-support-routing/spec.md`.

Restricciones relevantes de la épica ([peru-wallet-mvp](../../../docs/epic/peru-wallet-mvp.sp.md)) y la HU ([payment-failure-reversal-handling](../../../docs/stories/payment-failure-reversal-handling.sp.md)):

- Ecosistema multirriel: no se asume un único riel de procesamiento.
- No hay regla pública uniforme para cancelar unilateralmente transferencias P2P ya ejecutadas.
- Reintentos sin idempotencia robusta pueden causar duplicidad financiera y desvíos de conciliación; el contrato de idempotencia lo define el cambio `payment-idempotency-protection` (capability `payment-idempotency`).
- Niveles de escalamiento y SLA por definir (OQ-30); categorías de disputa en MVP sin decidir (OQ-29).
- Terminología (intento de pago, transacción, referencia, estado incierto, transferencia ejecutada, estado de resolución vs estado de investigación): ver [GLOSSARY.md](../../../docs/GLOSSARY.md).
- Este cambio consume estados terminales y referencia de `payer-low-value-payment-confirmation` y el contrato de `payment-idempotency`.

## Goals / Non-Goals

**Goals:**

- Un modelo de motivos de falla propio del producto, independiente de los códigos de cada riel/proveedor.
- Una regla de elegibilidad determinista (reintento / investigación / disputa) derivada del motivo y del estado de ejecución de la transferencia.
- Un registro auditable de acciones de soporte ligado a la referencia de transacción.

**Non-Goals:**

- Definir SLA, niveles de escalamiento o categorías de disputa (preguntas abiertas de la HU).
- Diseñar reversos/devoluciones automáticos con proveedores.
- Definir la clave de idempotencia, el resultado original o la auditoría de duplicados (propiedad de `payment-idempotency`).
- Elegir tecnología, base de datos o proveedor de herramienta de soporte.

## Decisions

1. **Taxonomía interna de códigos de motivo, con mapeo por riel/proveedor.** Se almacena el código interno y el motivo original del proveedor. Alternativa: guardar solo el código del proveedor; descartada por el acoplamiento a cada riel y la dificultad de dar guía uniforme. Un código "no clasificado" evita perder casos.
2. **Elegibilidad calculada a partir de (código de motivo, certeza de ejecución de la transferencia).** Si hay ejecución confirmada o estado incierto, nunca se ofrece reintento. Alternativa: dejar la elección al agente de soporte; descartada por riesgo de duplicidad.
3. **Reintentos de soporte consumen el contrato de `payment-idempotency` (dueña: cambio `payment-idempotency-protection`).** Este cambio no define clave, resultado original ni auditoría de duplicados: el reintento se rige por ese contrato para que no se genere un segundo movimiento de fondos. Lo propio de este cambio es la regla de cuándo soporte puede reintentar (decisión 2) y el enrutamiento a investigación o disputa cuando no corresponde. **Pregunta abierta (OQ-02):** si el reintento reutiliza la clave del intento original o crea un nuevo intento vinculado; reutilizar la clave devolvería el resultado original (fallido) en vez de reintentar el pago, por lo que no se fija aquí. Alternativa: definir una idempotencia local de soporte; descartada por divergencia del contrato común.
4. **Registro de acciones append-only.** Cada acción y cada cambio de estado de resolución es una entrada nueva ligada a la referencia de transacción, para auditoría. Alternativa: sobrescribir el estado; descartada por pérdida de trazabilidad.
5. **Mensajería al usuario con dos rutas (falla técnica vs. transferencia ejecutada)** que nunca promete cancelación unilateral en el segundo caso.
6. **Categorías de disputa tratadas como dato configurable no resuelto.** La capability no restringe categorías hasta que se responda la pregunta abierta.

## Risks / Trade-offs

- [Mapeo incompleto de motivos de proveedores] → Código "no clasificado" + conservar motivo original + revisión periódica de la taxonomía.
- [Estados asíncronos inciertos clasificados como falla técnica] → Tratar el estado incierto como investigación, nunca como reintento.
- [Dependencia del contrato de `payment-idempotency`, aún no consolidado en specs, y de su ventana de retención de claves (OQ-11)] → Consumir el contrato tal como lo defina `payment-idempotency-protection`; un reintento tardío fuera de la retención queda sujeto a lo que ese cambio decida, y la elegibilidad de reintento de este cambio no la reemplaza.
- [Obligaciones regulatorias de 2027 aún no precisas] → Mantener el registro auditable y la taxonomía extensible; validar con compliance.
- [SLA/escalamiento indefinidos] → El diseño no los codifica; se añadirán como cambio posterior.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). No se responden aquí.

- OQ-29: ¿qué categorías de disputa se habilitan en MVP y cuáles se difieren? (de la HU; sin responder.)
- OQ-30: ¿cuáles son los niveles de escalamiento y SLA de soporte? (de la HU; por definir.)
- OQ-31: ¿qué proveedores/rieles exponen motivos de falla utilizables para el mapeo? (depende de integraciones contractuales.)
- OQ-32: ¿qué fuente determina que una transferencia ya fue ejecutada o que su estado es incierto?
- OQ-33: ¿cuáles son los estados de resolución de las acciones de soporte y cómo se relacionan con los estados de investigación de conciliación (mismo caso o entidades distintas)?
- OQ-02: semántica del reintento de soporte (misma clave vs nuevo intento vinculado).
- OQ-10: tratamiento de la confirmación tardía de un intento expirado.
