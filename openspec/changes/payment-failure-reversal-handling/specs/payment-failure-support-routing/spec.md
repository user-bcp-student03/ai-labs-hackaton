# Spec Delta

## Purpose

Define cómo se clasifican los pagos fallidos y expirados, cómo se determina y muestra la ruta de atención (reintento, investigación o disputa) y cómo se registran las acciones de soporte, para dar guía consistente al usuario y resoluciones predecibles a soporte.

## ADDED Requirements

### Requirement: Código de motivo legible por máquina para pagos fallidos y expirados
El sistema SHALL clasificar todo pago con resultado fallido o expirado y SHALL almacenar un código de motivo legible por máquina asociado a la transacción.

Origen: criterio 1 de la HU. El escenario «Motivo de origen no reconocido» es agregado por análisis (evita perder casos). Los rieles/proveedores que exponen motivos utilizables están en OQ-31.

#### Scenario: Pago fallido recibe código de motivo
- **WHEN** un pago termina con resultado fallido
- **THEN** el sistema almacena un código de motivo de un conjunto definido y lo asocia a la referencia de la transacción

#### Scenario: Pago expirado recibe código de motivo
- **WHEN** un pago expira sin completarse
- **THEN** el sistema almacena un código de motivo que identifica la expiración y lo asocia a la referencia de la transacción

#### Scenario: Motivo de origen no reconocido
- **WHEN** el riel o proveedor devuelve un motivo que el sistema no puede mapear
- **THEN** el sistema almacena un código de motivo genérico "no clasificado" y conserva el motivo original para investigación

### Requirement: Ruta de atención visible en la vista de soporte
El sistema SHALL mostrar en la vista de soporte, para cada pago fallido, expirado o disputado, si es elegible para reintento, investigación o flujo de disputa.

Origen: criterio 2 de la HU. El escenario «Pago elegible para investigación» por estado incierto es agregado por análisis.

#### Scenario: Pago elegible para reintento
- **WHEN** soporte consulta un pago cuyo código de motivo corresponde a una falla técnica sin transferencia ejecutada
- **THEN** la vista de soporte indica que el pago es elegible para reintento

#### Scenario: Definiciones y fuentes de la elegibilidad
- **WHEN** se evalúa la elegibilidad de un pago con «estado incierto» o «transferencia ejecutada»
- **THEN** ambos términos se interpretan según [GLOSSARY.md](../../../../../docs/GLOSSARY.md); la fuente que determina que una transferencia fue ejecutada está en OQ-32 y las categorías de disputa en OQ-29

#### Scenario: Pago elegible para investigación
- **WHEN** soporte consulta un pago cuyo estado final es incierto o cuyo motivo no está clasificado
- **THEN** la vista de soporte indica que el pago es elegible para investigación y no para reintento

#### Scenario: Pago elegible para disputa
- **WHEN** soporte consulta un pago asociado a un escenario de disputa de una categoría habilitada (OQ-29)
- **THEN** la vista de soporte indica que el pago es elegible para el flujo de disputa

### Requirement: Reintento sin duplicidad financiera
El sistema SHALL ejecutar todo reintento originado desde soporte conforme al contrato de la capability `payment-idempotency`, de modo que no se genere un segundo movimiento de fondos para la misma intención de pago.

Origen: **agregado por análisis**. Justificación: la HU no lo exige como criterio; deriva del riesgo de duplicidad por reintentos de la épica y de los criterios 2 y 3 (elegibilidad de reintento).

#### Scenario: Alcance de esta capability respecto de la idempotencia
- **WHEN** se define el comportamiento de un reintento originado desde soporte
- **THEN** el contrato de `payment-idempotency` (propiedad del cambio `payment-idempotency-protection`) no se redefine aquí; esta capability solo define cuándo soporte puede reintentar y cómo se enruta el caso cuando no corresponde

#### Scenario: Mecanismo de reintento no decidido
- **WHEN** se debe determinar si el reintento reutiliza la clave del intento original o crea un nuevo intento vinculado
- **THEN** esta capability no lo decide (OQ-02); se tiene en cuenta que reutilizar la clave devolvería el resultado original y no reintentaría el pago

#### Scenario: Reintento de soporte sin duplicidad financiera
- **WHEN** soporte reintenta un pago elegible para reintento
- **THEN** el reintento se rige por `payment-idempotency` y no se genera más de un movimiento de fondos para la misma intención de pago; el mecanismo (misma clave o nuevo intento vinculado) queda definido por OQ-02

#### Scenario: Reintento sobre pago ya ejecutado
- **WHEN** soporte intenta reintentar un pago para el cual ya existe una transferencia ejecutada
- **THEN** el sistema rechaza el reintento y dirige el caso a investigación o disputa

### Requirement: Ruta de ayuda al usuario diferenciada por tipo de escenario
El sistema SHALL ofrecer al usuario una ruta de ayuda que diferencie una falla técnica de un escenario de transferencia ya ejecutada.

Origen: criterio 3 de la HU. El contenido final de los mensajes y los pasos siguientes dependen de los niveles de escalamiento y SLA (OQ-30).

#### Scenario: Falla técnica
- **WHEN** el usuario consulta un pago fallido o expirado sin transferencia ejecutada
- **THEN** la ruta de ayuda indica que no se completó el movimiento de fondos y presenta al menos una acción siguiente definida para falla técnica (por ejemplo, reintentar o contactar a soporte; contenido definido con soporte)

#### Scenario: Transferencia ya ejecutada
- **WHEN** el usuario consulta un pago cuya transferencia ya fue ejecutada
- **THEN** la ruta de ayuda indica que la transferencia fue ejecutada, no promete cancelación ni reverso unilateral y orienta a investigación o disputa

### Requirement: Registro de acciones de soporte
El sistema SHALL registrar cada acción de soporte sobre un pago con la referencia de transacción y el estado de resolución.

Origen: criterio 4 de la HU. Los valores posibles del estado de resolución y su relación con el estado de investigación de conciliación están en OQ-33.

#### Scenario: Acción de soporte registrada
- **WHEN** soporte ejecuta una acción sobre un pago (por ejemplo, reintento, inicio de investigación o apertura de disputa)
- **THEN** el sistema registra la acción con la referencia de transacción y un estado de resolución

#### Scenario: Cambio de estado de resolución
- **WHEN** el estado de resolución de un caso de soporte cambia
- **THEN** el sistema conserva el registro de la acción original y agrega el nuevo estado vinculado a la misma referencia de transacción
