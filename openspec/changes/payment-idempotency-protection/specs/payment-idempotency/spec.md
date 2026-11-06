# Spec Delta

## Purpose

Define el comportamiento idempotente de los intentos de pago: clave de idempotencia, devolución del resultado original ante solicitudes repetidas, auditoría de duplicados y distinción entre originales y reintentos duplicados para conciliación.

## ADDED Requirements

### Requirement: Clave de idempotencia por intento de pago
El sistema MUST asociar a cada intento de pago una clave de idempotencia única por pagador, monto, destino, ventana de intento e identificador de intención.

Origen: criterio 1 de la HU. Términos según [GLOSSARY.md](../../../../../docs/GLOSSARY.md). OQ-01: **Decidida (2026-11-06)**, híbrida. OQ-12 sigue abierta.

#### Scenario: Identificador de intención generado al abrir la confirmación
- **WHEN** el flujo del pagador abre la pantalla de confirmación de un pago
- **THEN** genera un identificador de intención para ese pago y lo envía con la solicitud
- **AND** el servidor incluye ese identificador en la derivación de la clave y la clave existe antes de crear cualquier transacción financiera

#### Scenario: Intento nuevo recibe clave
- **WHEN** se envía un intento de pago
- **THEN** el intento lleva una clave de idempotencia determinada por pagador, monto, destino, ventana de intento e identificador de intención

#### Scenario: Cambio de algún componente genera otra clave
- **WHEN** dos intentos difieren en pagador, monto, destino, ventana de intento o identificador de intención
- **THEN** cada intento tiene una clave de idempotencia distinta y se procesan como transacciones independientes

#### Scenario: Pago legítimo idéntico con otra intención no es duplicado
- **WHEN** el mismo pagador envía dos pagos con igual monto y destino dentro de la misma ventana de intento y con identificadores de intención distintos
- **THEN** cada pago tiene su propia clave, se procesa como transacción independiente y no se registra como duplicado

#### Scenario: Mismo identificador de intención repetido es duplicado
- **WHEN** se recibe de nuevo una solicitud con el mismo identificador de intención, por doble toque o por reintento de red, con los mismos pagador, monto, destino y ventana de intento
- **THEN** la solicitud se trata como duplicado de la clave ya registrada

#### Scenario: Duración de la ventana de intento no definida
- **WHEN** la duración de la ventana de intento aún no está definida (OQ-12, abierta)
- **THEN** su valor se obtiene de configuración y no se fija en esta especificación
- **AND** el valor provisional de 5 min es una propuesta, no aprobada

### Requirement: Solicitud repetida devuelve el resultado original
Cuando se recibe una solicitud con una clave de idempotencia ya registrada, el sistema MUST devolver el resultado original del intento y MUST NOT crear una nueva transacción financiera.

Origen: criterio 2 de la HU. Tres escenarios fueron agregados por análisis (ver abajo). Reintento deliberado tras resultado fallido/expirado: OQ-02, **Decidida (2026-11-06)**, "reintentar" crea un nuevo intento vinculado al original.

#### Scenario: Reintentar tras fallo o expiración crea un nuevo intento vinculado
- **WHEN** el usuario o soporte reintenta tras un resultado fallido o expirado
- **THEN** se crea un nuevo intento con nueva clave y nueva referencia, y se procesa como transacción independiente
- **AND** el nuevo intento queda vinculado al original con el vínculo "reintento de"

#### Scenario: La clave original sigue devolviendo el resultado original
- **WHEN** se recibe una solicitud con la clave de un intento fallido o expirado que ya tuvo un reintento vinculado
- **THEN** el sistema devuelve el resultado original de esa clave y no el del reintento

#### Scenario: Vínculo reintento-original almacenado
- **WHEN** se crea un intento de reintento
- **THEN** el sistema almacena el vínculo del reintento con el intento original, consultable desde cualquiera de los dos
- **AND** el reintento no se registra como duplicado porque tiene clave propia

#### Scenario: Repetición con resultado terminal
- **WHEN** se recibe una solicitud con la misma clave de un intento que ya tiene resultado terminal
- **THEN** el sistema devuelve ese mismo resultado y no se crea una nueva transacción financiera

#### Scenario: Repetición mientras el intento sigue en proceso
- **WHEN** se recibe una solicitud con la misma clave de un intento que aún no tiene resultado terminal
- **THEN** el sistema devuelve el estado actual del intento original y no inicia un segundo procesamiento
- **AND** este escenario fue agregado por análisis: precisa el criterio 2 cuando aún no hay resultado terminal

#### Scenario: Mismo comportamiento en cualquier riel
- **WHEN** la solicitud repetida corresponde a un intento procesado por cualquier canal o riel del MVP
- **THEN** se aplica el mismo comportamiento de resultado original sin depender del riel subyacente
- **AND** este escenario fue agregado por análisis: restricción multirriel de la épica

#### Scenario: Una sola transacción por clave
- **WHEN** una misma clave de idempotencia se recibe varias veces
- **THEN** existe como máximo una transacción financiera asociada a esa clave
- **AND** este escenario fue agregado por análisis: expresa el criterio 2 como invariante verificable

### Requirement: Registro de auditoría de solicitudes duplicadas
El sistema MUST registrar cada evento de solicitud duplicada con el identificador de solicitud y el identificador de correlación.

Origen: criterio 3 de la HU. El período de conservación del registro queda en OQ-13 (abierta); la propuesta provisional "sin purga" es una propuesta, no aprobada.

#### Scenario: Duplicado registrado
- **WHEN** se detecta una solicitud duplicada
- **THEN** se registra un evento con el identificador de solicitud, el identificador de correlación y la clave de idempotencia del intento original

#### Scenario: Cada duplicado genera su propio registro
- **WHEN** la misma clave se repite en varias solicitudes
- **THEN** cada solicitud duplicada tiene su propio registro y el registro del intento original no se modifica

#### Scenario: Trazabilidad entre original y duplicado
- **WHEN** auditoría consulta un registro de duplicado
- **THEN** puede relacionarlo con el intento original mediante la clave de idempotencia y el identificador de correlación

### Requirement: Distinción de originales y duplicados para conciliación
Las salidas de conciliación MUST distinguir de forma explícita los intentos originales de los reintentos duplicados.

Origen: criterio 4 de la HU. Esta capability solo provee el marcado; el reporte y el resumen pertenecen a `ops-transaction-reconciliation`. OQ-14: **Decidida (2026-11-06)**, opción DIFERIR: se expone por solicitud el tipo, el vínculo al original y ambas fechas; la regla que asigna un duplicado a un día de reporte la decide después conciliación (Fase 2).

#### Scenario: Intento original identificado
- **WHEN** una salida de conciliación incluye un intento que originó una transacción financiera
- **THEN** el intento se identifica con tipo original

#### Scenario: Reintento duplicado identificado
- **WHEN** una salida de conciliación incluye una solicitud repetida con una clave ya registrada
- **THEN** la solicitud se identifica con tipo duplicado y se vincula al intento original

#### Scenario: Datos expuestos por solicitud
- **WHEN** conciliación consulta una solicitud
- **THEN** recibe el tipo (original o duplicado), el vínculo al original, la fecha de la solicitud y la fecha del original

#### Scenario: Día de reporte del duplicado no asignado aquí
- **WHEN** la fecha de la solicitud duplicada difiere de la fecha del original
- **THEN** esta capability expone ambas fechas sin asignar el duplicado a un día de reporte
- **AND** la regla de asignación queda diferida a conciliación (Fase 2)

#### Scenario: Reintento vinculado distinguido del duplicado
- **WHEN** una salida de conciliación incluye un nuevo intento creado por "reintentar" tras fallo o expiración
- **THEN** se identifica como intento original con su propia referencia y el vínculo "reintento de", y no como duplicado

#### Scenario: Duplicados no cuentan como transacciones adicionales
- **WHEN** se calculan totales de transacciones en una salida de conciliación
- **THEN** los reintentos duplicados no se cuentan como transacciones financieras adicionales

### Requirement: Retención de claves configurable por canal
El sistema MUST obtener de configuración, por canal, la ventana de retención de las claves de idempotencia, y no se fija un valor en esta especificación.

Origen: **agregado por análisis**. Justificación: la HU deja abierta la pregunta de la ventana de retención (OQ-11, abierta); este requisito solo garantiza que el valor sea configurable y no queda codificado. El comportamiento ante una clave fuera de la ventana de retención no se define aquí (OQ-11).

#### Scenario: Ventana de retención por canal
- **WHEN** se evalúa si una clave sigue vigente para un canal
- **THEN** se usa la ventana de retención configurada para ese canal

#### Scenario: Ventana de retención no definida
- **WHEN** la ventana de retención de un canal aún no está definida (OQ-11, pregunta abierta de la HU)
- **THEN** el valor se resuelve por configuración y la definición queda pendiente de producto y operaciones
- **AND** el valor provisional de 24 h por canal es una propuesta, no aprobada
