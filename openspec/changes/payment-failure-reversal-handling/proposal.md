# Proposal

## Why

Los pagos fallidos, expirados y disputados hoy no tienen una ruta de atención explícita: soporte no puede distinguir si corresponde reintentar, investigar o abrir una disputa, y el usuario no recibe guía consistente. Además, no existe una regla pública uniforme para cancelar unilateralmente transferencias P2P ya ejecutadas, y la dirección regulatoria aumenta desde 2027 las obligaciones sobre fraude, disputas y devoluciones/reversos. Conviene definir el comportamiento desde el MVP para sostener la confianza del usuario y evitar duplicidad financiera y desvíos de conciliación.

## Fuentes

- Historia de usuario: [Manejo de fallas de pago y reversos](../../../docs/stories/payment-failure-reversal-handling.sp.md)
- Épica: [MVP de wallet en Perú](../../../docs/epic/peru-wallet-mvp.sp.md)

## What Changes

- Clasificar los resultados de pago fallido y expirado y almacenarlos con un código de motivo legible por máquina.
- Exponer en la vista de soporte la ruta aplicable a cada pago: elegible para reintento, investigación o flujo de disputa.
- Diferenciar en la ruta de ayuda al usuario una falla técnica de un escenario de transferencia ya ejecutada (sin prometer cancelación unilateral).
- Registrar las acciones de soporte con referencia de transacción y estado de resolución.

## Alcance

### En alcance

- Taxonomía de códigos de motivo para pagos fallidos y expirados (almacenamiento y consulta).
- Determinación y visualización de la ruta de atención (reintento, investigación, disputa) en la vista de soporte.
- Mensajería/ruta de ayuda al usuario que distingue falla técnica de transferencia ya ejecutada.
- Registro (trazabilidad) de acciones de soporte con referencia de transacción y estado de resolución.

### Fuera de alcance

- Definición de niveles de escalamiento de soporte y SLA (quedan por definir).
- Decidir qué categorías de disputa se habilitan en MVP y cuáles se difieren (pregunta abierta; no se responde aquí).
- Definición de la clave de idempotencia, de la devolución del resultado original y de la auditoría de duplicados (propiedad de `payment-idempotency`, cambio `payment-idempotency-protection`).
- Cancelación o reverso unilateral de transferencias P2P ya ejecutadas.
- Ejecución automática de devoluciones/reversos con proveedores o bancos externos.
- Cumplimiento regulatorio detallado de 2027 sobre fraude/disputas/devoluciones.
- Confirmación de pago al pagador, visibilidad de estado para comercios y conciliación operativa (cubiertos por otras historias de la épica).
- Todo lo listado como fuera de alcance en la épica (multipaís, lealtad, paridad total de proveedores, APIs abiertas).

## Supuestos

- Los niveles de escalamiento de soporte y los SLA quedan por definir (según la HU).
- El MVP no asume un único riel de procesamiento; los motivos de falla deben poder mapearse desde varios rieles/proveedores.
- Las acciones de soporte y los reintentos deben respetar idempotencia para no generar duplicidad financiera (riesgo de la épica). La idempotencia la define y es propiedad de la capability `payment-idempotency` (cambio `payment-idempotency-protection`); este cambio consume su contrato y no lo redefine. Si el reintento de soporte reutiliza la clave del intento original o crea un nuevo intento vinculado **no se decide aquí** (OQ-02): reutilizar la clave devolvería el resultado original (fallido) y no reintentaría el pago.

## Preguntas abiertas

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). No se responden en este cambio.

- OQ-29: ¿qué categorías de disputa deben habilitarse en MVP y cuáles se difieren a post-MVP? (de la HU, sin respuesta). **Bloquea** habilitar la ruta de disputa; el modelo base puede avanzar.
- OQ-30: ¿cuáles son los niveles de escalamiento de soporte y los SLA por ruta? (de la HU, por definir).
- OQ-31: ¿qué proveedores/rieles exponen motivos de falla utilizables para el mapeo?
- OQ-32: ¿qué fuente determina que una transferencia ya fue ejecutada (resultado del proveedor, asiento de ledger)? **Bloquea** la regla de elegibilidad definitiva (tarea 2.1).
- OQ-33: ¿cuáles son los estados de resolución de las acciones de soporte y cómo se relacionan con los estados de investigación de conciliación?
- OQ-02: semántica del reintento de soporte (ver supuestos). **Bloquea** la tarea 2.3.
- OQ-10: tratamiento de la confirmación tardía de un intento expirado (genera casos de investigación/disputa).

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | `payment-idempotency-protection` | Contrato de reintento sin duplicidad financiera. |
| Depende de | `payer-low-value-payment-confirmation` | Estados terminales (fallido, expirado), referencia de transacción y confirmación tardía que se clasifican y enrutan. |
| Se relaciona con | `ops-transaction-reconciliation` | La ruta "investigación" de soporte y el estado de investigación de un descalce pueden referirse al mismo caso (OQ-33); no se redefine ninguno. |

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Requisito "Reintento sin duplicidad financiera" (proviene del riesgo de idempotencia de la épica; es solo consumo del contrato de `payment-idempotency`).
- Escenarios «Motivo de origen no reconocido» (código "no clasificado") y «Pago elegible para investigación» por estado incierto (decisiones de diseño para no perder casos ni ofrecer reintento ante incertidumbre).

## Capabilities

### New Capabilities

- `payment-failure-support-routing`: clasificación de pagos fallidos/expirados con código de motivo, determinación de la ruta de atención (reintento, investigación, disputa), diferenciación entre falla técnica y transferencia ya ejecutada, y registro de acciones de soporte.

### Modified Capabilities

<!-- Ninguna: `openspec/specs/` aún no contiene capabilities existentes. -->

## Impact

- Repositorio greenfield: no existe código de aplicación; este cambio solo produce artefactos de especificación y no implica archivos de código existentes.
- Sistemas futuros afectados (a nivel conceptual): servicio/estado de pagos, vista de soporte, ruta de ayuda al usuario y registro de acciones de soporte.
- Dependencias: capability `payment-idempotency` (cambio `payment-idempotency-protection`) para la clave y el comportamiento de reintento sin duplicidad; partners de adquirencia/gateway y rieles para mapear motivos de falla; coordinación con las historias hermanas de confirmación al pagador, estado para comercios y conciliación.
