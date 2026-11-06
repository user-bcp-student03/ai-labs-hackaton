# Diseño

Ver [proposal.md](proposal.md) para la motivación y [specs/merchant-qr-payment-status/spec.md](specs/merchant-qr-payment-status/spec.md) para los requisitos.

## Contexto

- El repositorio es greenfield: no existe código de aplicación, stack, modelo de datos ni integración con proveedores. Este diseño es de nivel de enfoque y no referencia archivos ni módulos existentes; las elecciones concretas de tecnología se difieren a la implementación.
- La épica indica que el ecosistema es multirriel, que las integraciones con adquirencia/gateway son contractuales (no autoservicio) y que las transiciones asíncronas de estado pueden deteriorar la confianza si la confirmación no es clara.
- Los formatos y garantías de entrega de los callbacks/eventos del proveedor aún son desconocidos (OQ-26).
- Terminología (intento de pago, transacción, referencia, estado, evento duplicado): ver [GLOSSARY.md](../../../docs/GLOSSARY.md). Los estados visibles al comercio son consumidos por `ops-transaction-reconciliation` y deben poder correlacionarse con los estados terminales de `payer-low-value-payment-confirmation` (OQ-24).

## Goals / Non-Goals

**Goals:**
- Una fuente única de verdad del estado por transacción, consultable por el comercio.
- Aplicación de eventos del proveedor de forma deduplicada y tolerante a desorden.
- Consulta del historial con filtros por fecha y referencia, limitada al comercio autenticado.

**Non-Goals:**
- Definir el conjunto final de estados ni el canal (app/web) de consulta.
- Conciliación, reversos, disputas y vista para el pagador.
- Elegir proveedor o tecnología concreta.

## Decisiones

1. **Modelo separado de estado proveedor vs. estado MVP.** Se mantiene un mapeo configurable entre los estados/eventos del proveedor y el conjunto de estados MVP. Razón: el MVP no debe asumir un único riel y el conjunto mínimo aún no está definido. Alternativa: codificar los estados directamente (rechazada: acopla el modelo a la decisión pendiente y a un proveedor).
2. **Historial de eventos append-only + estado actual derivado.** Cada evento se guarda con su identificador de proveedor y marca de tiempo; el estado actual se deriva o proyecta del historial. Razón: soporta el historial filtrable y auditoría. Alternativa: solo sobrescribir el estado (rechazada: pierde trazabilidad).
3. **Deduplicación de eventos del proveedor por identificador de evento y referencia de transacción** (no es la idempotencia de solicitudes de pago). Los eventos repetidos no alteran estado ni historial; los eventos fuera de orden no regresan el estado. Razón: riesgo de la épica sobre confiabilidad de confirmación y duplicidad. Alternativa: confiar en el orden de entrega del proveedor (rechazada: no está garantizado).
   *Nota:* este mecanismo de eventos entrantes es distinto de la idempotencia de solicitudes de pago, cuyo contrato (clave, resultado original, registro de auditoría de duplicados) pertenece a la capability `payment-idempotency` del cambio `payment-idempotency-protection`. Puede reutilizar el registro de duplicados (append-only) y los identificadores de correlación de ese cambio, sin adoptar su clave de idempotencia; la reutilización se valida durante la implementación y no modifica los requisitos de este cambio. Términos «evento duplicado» frente a «reintento duplicado»: ver [GLOSSARY.md](../../../docs/GLOSSARY.md).
4. **Actualización de la vista tras aplicar el evento.** El mecanismo de refresco (consulta periódica, push u otro) se decide en implementación, y depende del canal aún no definido (OQ-25). El requisito es que el estado mostrado refleje el último evento aplicado dentro del plazo máximo configurable (OQ-28).
5. **Filtros del lado del servidor, con alcance por comercio.** Toda consulta se restringe al comercio autenticado. Alternativa: filtrar en el cliente (rechazada: riesgo de exposición y mal rendimiento con volumen).

## Risks / Trade-offs

- [Dependencia de terceros: callbacks tardíos o perdidos] → Mostrar la fecha/hora de la última actualización; evaluar mecanismo de consulta de respaldo al proveedor cuando se conozcan las capacidades.
- [Estados del proveedor sin equivalente MVP] → Mapeo configurable y registro de casos no mapeados para revisión.
- [Estado ambiguo que lleve al comercio a entregar sin pago confirmado] → Depende de la definición del conjunto de estados (OQ-24); no se resuelve aquí.
- [Autenticidad de callbacks] → Validar origen de los eventos del proveedor; el método depende del proveedor y se define al integrar.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). No se responden aquí.

- OQ-24: ¿cuál es el conjunto mínimo de estados requerido para la operación de comercios en el lanzamiento MVP? (Pregunta abierta de la HU. Afecta el mapeo y los textos mostrados, pero la estructura de requisitos no depende del valor concreto.) Incluye si coincide con los estados terminales del pagador y qué se muestra ante un estado sin equivalente.
- OQ-25: ¿cuál es el canal de consulta del comercio: app, web o ambos? (Supuesto abierto de la HU.)
- OQ-26: ¿qué proveedores de adquirencia/gateway se usarán y qué garantías ofrecen sus callbacks (orden, reintentos, firma)?
- OQ-27: ¿cuál es la retención y el rango máximo de fechas del historial consultable, y qué fecha se filtra (creación del intento o cambio de estado) y en qué zona horaria?
- OQ-28: ¿cuál es el plazo máximo entre aplicar un evento y reflejarlo en la vista del comercio? (agregado por análisis).
- OQ-08: ¿qué flujo/capability crea el intento de pago QR iniciado por el cliente? (ningún cambio lo define.)
