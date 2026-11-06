# Proposal

- **Historia de usuario**: [Conciliación operativa de transacciones](../../../docs/stories/ops-transaction-reconciliation.sp.md)
- **Historia relacionada (consumo del marcado original/duplicado, criterio 4)**: [Idempotencia en pagos](../../../docs/stories/payment-idempotency-protection.sp.md)
- **Épica**: [MVP de wallet en Perú para pagos cotidianos](../../../docs/epic/peru-wallet-mvp.sp.md)

## Why

El MVP de wallet opera sobre un ecosistema multirriel con estados de pago asíncronos y dependencia de terceros (proveedores de adquirencia/gateway). Sin una conciliación diaria entre las intenciones de pago, los resultados del proveedor y los asientos del ledger, los descalces (por ejemplo, duplicidad por reintentos sin idempotencia robusta) no se detectan a tiempo y se pierde integridad financiera y confianza del usuario. Esta capacidad es un control operativo previo a considerar una transacción como definitiva y cubre la historia candidata de la épica para operaciones/compliance.

## What Changes

- Se introduce una conciliación diaria que compara los registros de transacción de la wallet (intención de pago y asiento de ledger) contra los registros de resultado del proveedor en los canales del MVP.
- Cada descalce se marca con referencia de transacción, tipo de descalce y estado actual de investigación.
- Los reportes de conciliación se pueden filtrar por fecha y por canal de proveedor.
- Se genera un resumen diario con totales de registros conciliados, no conciliados y resueltos.
- El reporte y el resumen diario **consumen** el marcado de origen (original o reintento duplicado) que provee la capability `payment-idempotency` del cambio `payment-idempotency-protection`, de modo que distinguen los intentos originales de los reintentos duplicados y no cuentan los duplicados como transacciones adicionales. Este cambio no define ni genera ese marcado.
- Nota: el repositorio es greenfield y no contiene código de aplicación; este cambio solo define comportamiento (specs), diseño y tareas. No se referencian archivos de código existentes.

### Dentro de alcance

- Comparación diaria wallet vs. resultado del proveedor en los canales MVP (transferencias de bajo monto y cobro a comercios con QR).
- Clasificación y marcado de descalces con referencia, tipo y estado de investigación.
- Filtrado de reportes por fecha y canal de proveedor.
- Resumen diario de totales: conciliados, no conciliados y resueltos.
- Presentación en el reporte y en el resumen diario de la distinción original/reintento duplicado, a partir del marcado provisto por `payment-idempotency` (solo consumo).

### Fuera de alcance

- Clave de idempotencia, devolución del resultado original, registro de auditoría de duplicados (con identificadores de solicitud y de correlación) y generación del marcado original/duplicado: son propiedad del cambio `payment-idempotency-protection` (capability `payment-idempotency`).
- Implementación de código, herramientas o infraestructura de conciliación (según la HU, las herramientas se definirán durante la implementación).
- Corrección automática de descalces, reversos, contracargos o disputas (el manejo operativo/legal de reversos y disputas es un riesgo de la épica que se trata aparte).
- Definición del umbral máximo diario de descalce aceptable para el lanzamiento (pregunta abierta de la HU).
- Despliegue multipaís, paridad completa con todos los proveedores/bancos desde el día uno y APIs abiertas para terceros (fuera de alcance de la épica).
- Instrumentación del funnel de checkout/onboarding y notificaciones al usuario final.

## Capabilities

### New Capabilities

- `transaction-reconciliation`: conciliación diaria entre intenciones de pago, resultados del proveedor y asientos del ledger de wallet; marcado de descalces con estado de investigación; reportes filtrables por fecha y canal; resumen diario de totales; distinción de originales y reintentos duplicados en el reporte y el resumen (consumiendo el marcado de `payment-idempotency`, que no es propiedad de esta capability).

### Modified Capabilities

(ninguna; `openspec/specs/` está vacío y no existen capacidades previas)

## Supuestos y preguntas abiertas

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

Supuestos (tomados de la HU):

- Las herramientas de conciliación se definirán durante la implementación.

Supuestos adicionales (a validar con `payment-idempotency-protection`):

- El marcado original/duplicado (con vínculo al intento original) estará disponible desde `payment-idempotency`; su forma exacta se acuerda con ese cambio y no se redefine aquí (OQ-14).

Preguntas abiertas (no se responden en este cambio):

- OQ-34: ¿cuál es la tasa máxima diaria de descalce aceptable para la preparación del lanzamiento del MVP? (La HU no la define; el resumen diario no evaluará ningún umbral hasta que se responda.)
- OQ-35: hora de corte y zona horaria del día conciliado, y tratamiento de estados asíncronos pendientes (evita descalces falsos).
- OQ-36: catálogo definitivo de tipos de descalce y de estados de investigación.
- OQ-37: regla de conteo del total de "resueltos" frente al de "no conciliados" en el resumen diario.
- OQ-09: canales exactos del MVP y referencia de transacción común para el cruce.
- OQ-14: forma de exponer el marcado original/duplicado y día asignado a un duplicado cuyo original cae en otro día.
- OQ-24: conjunto de estados del comercio que la conciliación debe poder comparar.
- OQ-33: relación entre el estado de investigación de un descalce y el estado de resolución de soporte.

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | `payment-idempotency-protection` | Marcado original/duplicado con vínculo al original (dependencia fuerte, criterio 4). |
| Depende de | `payer-low-value-payment-confirmation` | Estados terminales (exitoso, fallido, expirado), referencia de transacción y discrepancias por confirmación tardía (OQ-10). |
| Depende de | `merchant-qr-payment-status-visibility` | Conjunto de estados MVP del comercio (OQ-24) y estados aplicados por eventos del proveedor. |
| Se relaciona con | `payment-failure-reversal-handling` | La ruta de investigación de soporte y el estado de investigación del descalce pueden referirse al mismo caso (OQ-33); no se redefine ninguno. |

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Escenario «Registros con datos diferentes» (tipo de descalce por diferencia de datos; deriva del criterio 1 «compara» y de la decisión 3 del diseño).
- Escenario «Intención de pago sin asiento de ledger» (deriva del enunciado de la HU, que menciona los asientos del ledger, pero ningún criterio los cubre explícitamente).
- Escenario «Salida disponible por cada día conciliado» (hace verificable «diaria»; OQ-35).
- Escenario «Registro sin marcado de origen» (robustez ante dato faltante del consumo de `payment-idempotency`).
- Escenario «Varias transacciones financieras para un mismo intento original» (decisión 8 del diseño).
- Requisito «Alcance de la evaluación del descalce» (deriva de la pregunta abierta de la HU, OQ-34).

## Impact

- **Código**: ninguno existente (greenfield). La implementación futura creará los componentes necesarios; su ubicación y tecnología se deciden en la fase de implementación.
- **Sistemas/dependencias**: consume datos del ledger de wallet, de las intenciones de pago y de los resultados reportados por los proveedores de los canales MVP; depende de los acuerdos con partners de adquirencia/gateway.
- **Usuarios**: analistas de operaciones (consumidores del reporte y del resumen diario).
- **Relación con otros cambios**: ver la tabla «Dependencias entre cambios» más arriba. Para la distinción original/duplicado **consume** la capability `payment-idempotency` del cambio `payment-idempotency-protection` (dueño del marcado de origen y del registro de auditoría de duplicados); el reporte y el resumen diario siguen siendo propiedad de este cambio. Consume además los estados de `payer-low-value-payment-confirmation` y `merchant-qr-payment-status-visibility`, sin redefinirlos.
