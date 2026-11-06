# Delta de especificación: estado de pagos QR para comercios

## Purpose

Permitir que un pequeño comercio que cobra con QR vea el estado confiable y actualizado de cada intento de pago de sus clientes, para decidir cuándo entregar el producto o servicio.

## ADDED Requirements

### Requirement: Referencia única por intento de pago QR
El sistema SHALL mostrar al comercio cada intento de pago QR asociado a su cuenta, identificado con una referencia única de transacción.

Origen: criterio 1 de la HU. El escenario «Aislamiento entre comercios» es agregado por análisis. La referencia identifica al intento de pago (ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md)); el flujo que crea el intento QR no está definido en ningún cambio (OQ-08).

#### Scenario: Intento de pago visible con referencia
- **WHEN** un cliente inicia un pago QR hacia un comercio
- **THEN** el comercio ve un intento de pago en su vista con una referencia de transacción

#### Scenario: Referencias distintas por intento
- **WHEN** el comercio tiene dos intentos de pago QR distintos
- **THEN** cada intento muestra una referencia de transacción diferente

#### Scenario: Aislamiento entre comercios
- **WHEN** un comercio consulta su vista
- **THEN** solo ve los intentos de pago QR de su propio comercio

### Requirement: Estado actual dentro del conjunto de estados MVP
El sistema SHALL mostrar, para cada intento de pago QR, un estado actual perteneciente al conjunto de estados habilitado para el MVP. El conjunto mínimo de estados está pendiente de definición (OQ-24).

Origen: criterio 2 de la HU. El escenario «Estado fuera del conjunto habilitado» es agregado por análisis. Qué se muestra al comercio en lugar del valor no mapeado, y si el conjunto es el mismo que los estados terminales del pagador, quedan en OQ-24.

#### Scenario: Estado actual visible
- **WHEN** el comercio abre la vista de un intento de pago QR
- **THEN** se muestra exactamente un estado actual de ese intento

#### Scenario: Estado fuera del conjunto habilitado
- **WHEN** el proveedor informa un estado que no pertenece al conjunto habilitado para el MVP
- **THEN** el sistema no muestra ese valor tal cual y registra el caso para su revisión operativa; qué se muestra en su lugar queda pendiente (OQ-24)

### Requirement: Actualización del estado por eventos del proveedor
El sistema SHALL actualizar el estado visible de una transacción cuando reciba un callback o evento del proveedor que cambie su estado.

Origen: criterio 3 de la HU. Escenarios agregados por análisis: «Evento duplicado», «Evento fuera de orden», «Evento para transacción desconocida» y «Plazo de reflejo en la vista» (OQ-28).

#### Scenario: Cambio de estado por callback
- **WHEN** el proveedor envía un evento que cambia el estado de una transacción existente
- **THEN** la vista del comercio refleja el nuevo estado de esa transacción

#### Scenario: Plazo de reflejo en la vista
- **WHEN** el sistema aplica un evento del proveedor que cambia el estado de una transacción
- **THEN** la vista del comercio muestra el nuevo estado dentro del plazo máximo configurado (valor pendiente, OQ-28)
- **AND** este plazo hace medible el «se actualiza» del criterio de la HU

#### Scenario: Evento duplicado
- **WHEN** el proveedor envía más de una vez el mismo evento para una transacción
- **THEN** el estado visible y el historial de la transacción no se alteran por la repetición
- **AND** esta deduplicación de eventos entrantes es un mecanismo distinto de la idempotencia de solicitudes de pago (`payment-idempotency`); ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md)

#### Scenario: Evento fuera de orden
- **WHEN** llega un evento anterior a otro ya aplicado para la misma transacción
- **THEN** el sistema no revierte el estado visible a un valor más antiguo

#### Scenario: Evento para transacción desconocida
- **WHEN** llega un evento con una referencia que no corresponde a ningún intento conocido
- **THEN** el sistema no crea un intento visible para el comercio y registra el caso para su revisión operativa

#### Scenario: Origen de los escenarios de evento duplicado, fuera de orden y desconocido
- **WHEN** se revisan los escenarios «Evento duplicado», «Evento fuera de orden» y «Evento para transacción desconocida»
- **THEN** se entiende que responden a los riesgos de terceros y a la confiabilidad de la épica

### Requirement: Consulta filtrada del historial de estados
El sistema SHALL permitir al comercio filtrar el historial de estados de sus transacciones por fecha y por referencia de transacción.

Origen: criterio 4 de la HU. La fecha filtrada es la del intento (creación); si también debe poder filtrarse por fecha de cambio de estado, la zona horaria y el rango máximo consultable están en OQ-27.

#### Scenario: Filtro por fecha
- **WHEN** el comercio filtra por una fecha o rango de fechas
- **THEN** ve solo las transacciones cuyo intento cae dentro de ese rango

#### Scenario: Filtro por referencia
- **WHEN** el comercio filtra por una referencia de transacción existente
- **THEN** ve únicamente esa transacción con su estado actual

#### Scenario: Filtros combinados
- **WHEN** el comercio aplica filtro por fecha y por referencia a la vez
- **THEN** ve solo las transacciones que cumplen ambos criterios

#### Scenario: Sin resultados
- **WHEN** ningún intento cumple los filtros aplicados
- **THEN** el sistema indica que no hay resultados, sin mostrar transacciones de otros comercios
