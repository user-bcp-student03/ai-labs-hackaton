# Propuesta

- Historia de usuario: [Visibilidad del estado de pagos QR para comercios](../../../docs/stories/merchant-qr-payment-status-visibility.sp.md)
- Épica: [MVP de wallet en Perú](../../../docs/epic/peru-wallet-mvp.sp.md)

## Por qué

Los pequeños comercios que cobran con QR necesitan saber con confiabilidad si el pago de un cliente fue confirmado antes de entregar el producto o servicio. La épica identifica como riesgos explícitos la dependencia de terceros (adquirencia/gateway) y que las transiciones asíncronas del estado de pago deterioran la confianza si la confirmación no es clara. Sin una vista de estado confiable, el comercio entrega sin pago confirmado o retiene entregas innecesariamente.

## Qué cambia

- Se introduce una vista para el comercio de cada intento de pago QR, identificado con una referencia única de transacción.
- Cada intento muestra su estado actual, dentro del conjunto de estados habilitado para el MVP (el conjunto mínimo aún no está definido; ver preguntas abiertas).
- El estado visible se actualiza cuando llegan callbacks/eventos del proveedor que cambian el estado de la transacción.
- El comercio puede filtrar el historial de estados por fecha y por referencia de transacción.

No hay cambios incompatibles (**BREAKING**): el repositorio es greenfield y no existe código de aplicación ni specs previas en `openspec/specs/`.

## Alcance

### Dentro de alcance

- Listado/visualización de intentos de pago QR por comercio con referencia única de transacción (criterio 1).
- Visualización del estado actual de cada intento dentro del conjunto de estados MVP (criterio 2).
- Actualización de la vista ante callbacks/eventos del proveedor que modifican el estado (criterio 3).
- Filtro del historial de estados por fecha y referencia de transacción (criterio 4).

### Fuera de alcance

- Definir el conjunto final de estados (pregunta abierta de la HU; no se responde aquí).
- Decidir el canal de consulta del comercio (app, web o ambos; supuesto abierto de la HU).
- Visibilidad de confirmación para el pagador, onboarding y transferencias de bajo monto (otras historias de la épica).
- Monitoreo y conciliación para operaciones/compliance.
- Reversos, disputas y devoluciones.
- Idempotencia de solicitudes de pago (clave, resultado original, auditoría de duplicados): propiedad de `payment-idempotency-protection`; aquí solo se deduplican los eventos entrantes del proveedor.
- Creación del intento de pago QR por parte del cliente (ningún cambio la define; OQ-08).
- Alta y contratación de proveedores de adquirencia/gateway; paridad entre todos los proveedores.
- APIs abiertas para terceros y despliegue multipaís (fuera de alcance de la épica).

## Capabilities

### New Capabilities

- `merchant-qr-payment-status`: visibilidad para el comercio del estado de cada intento de pago QR, su actualización por eventos del proveedor y la consulta filtrada del historial.

### Modified Capabilities

Ninguna: no existen specs previas en `openspec/specs/`.

## Supuestos y preguntas abiertas

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). No se responden en este cambio.

- Supuesto: el canal de consulta del comercio (app, web o ambos) queda por definir (OQ-25).
- Pregunta abierta (OQ-24): ¿cuál es el conjunto mínimo de estados requerido para la operación de comercios en el lanzamiento MVP? Incluye su relación con los estados terminales del pagador y qué se muestra ante un estado del proveedor sin equivalente. La spec y el diseño lo tratan como parámetro pendiente.
- OQ-08: ningún cambio define el flujo mediante el cual el cliente inicia el pago QR que genera el intento visible para el comercio; este cambio asume que el intento existe.
- OQ-26: proveedores de adquirencia/gateway y garantías de sus callbacks (orden, reintentos, firma).
- OQ-27: retención y rango máximo del historial consultable, y qué fecha se filtra (creación del intento o cambio de estado).
- OQ-28: plazo máximo entre aplicar un evento y reflejarlo en la vista del comercio (agregado por análisis, para volver medible el criterio 3).

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | proveedores de adquirencia/gateway (externo) | Origen de los callbacks/eventos (OQ-26). |
| Depende de (supuesto) | creación del intento QR | Ningún cambio la define (OQ-08). |
| Puede reutilizar | `payment-idempotency-protection` | Registro de duplicados e identificadores de correlación; no adopta su clave. Dependencia opcional. |
| Debe ser coherente con | `payer-low-value-payment-confirmation` | El conjunto de estados del comercio debe poder correlacionarse con los estados terminales del pagador (OQ-24). |
| Es consumido por | `ops-transaction-reconciliation` | Los estados visibles al comercio son uno de los estados que la conciliación compara con el resultado del proveedor. |

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Escenario «Aislamiento entre comercios» (seguridad; se deriva del criterio 1 aplicado por comercio).
- Escenarios «Estado fuera del conjunto habilitado», «Evento duplicado», «Evento fuera de orden» y «Evento para transacción desconocida» (riesgos de confiabilidad de confirmación y de terceros de la épica).
- Escenario «Plazo de reflejo en la vista» (hace medible el criterio 3; OQ-28).
- Validación de origen de callbacks (tarea 2.1; riesgo de terceros).

## Impacto

- Código: no existe código de aplicación en el repositorio (greenfield); este cambio solo produce artefactos de planificación y no implementa nada.
- Sistemas: dependencia de los callbacks/eventos de los partners de adquirencia/gateway aún no seleccionados/contratados; el MVP no debe asumir un único riel.
- Riesgos relacionados de la épica: confiabilidad de confirmación y duplicidad de eventos/solicitudes ante reintentos.
