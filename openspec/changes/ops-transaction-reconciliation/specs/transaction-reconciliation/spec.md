# Spec Delta

## Purpose

Permite a operaciones detectar tempranamente descalces entre las intenciones de pago, los resultados del proveedor y los asientos del ledger de la wallet, y dar seguimiento a su investigación, para mantener la integridad financiera del MVP.

## ADDED Requirements

### Requirement: Conciliación diaria de transacciones por canal
El sistema SHALL generar diariamente una salida de conciliación que compare los registros de transacción de la wallet (intención de pago y asiento de ledger) contra los registros de resultado del proveedor, para cada canal de proveedor del MVP.

Origen: criterio 1 de la HU. Escenarios agregados por análisis: «Registros con datos diferentes», «Intención de pago sin asiento de ledger» y «Salida disponible por cada día conciliado».

#### Scenario: Registros coincidentes
- **WHEN** una transacción de wallet y su resultado del proveedor corresponden entre sí en el día conciliado
- **THEN** la salida de conciliación la incluye como conciliada

#### Scenario: Registro de wallet sin resultado del proveedor
- **WHEN** existe una transacción de wallet del día sin resultado del proveedor correspondiente
- **THEN** la salida de conciliación la incluye como no conciliada y la marca como descalce

#### Scenario: Resultado del proveedor sin registro de wallet
- **WHEN** existe un resultado del proveedor sin transacción de wallet correspondiente
- **THEN** la salida de conciliación lo incluye como no conciliado y lo marca como descalce

#### Scenario: Registros con datos diferentes
- **WHEN** una transacción de wallet y su resultado del proveedor se corresponden por referencia pero difieren en un dato comparado (por ejemplo, monto o estado terminal)
- **THEN** la salida de conciliación la incluye como no conciliada y la marca como descalce con el tipo «diferencia de datos» (catálogo definitivo en OQ-36)
- **AND** los estados terminales del pagador y el conjunto de estados del comercio comparados se consumen de `payer-low-value-payment-confirmation` y `merchant-qr-payment-status-visibility`, sin redefinirlos aquí (OQ-24)
#### Scenario: Intención de pago sin asiento de ledger
- **WHEN** existe una intención de pago con resultado exitoso sin asiento de ledger correspondiente
- **THEN** la salida de conciliación la incluye como no conciliada y la marca como descalce

#### Scenario: Canal sin movimientos
- **WHEN** un canal de proveedor del MVP no tiene registros en el día conciliado
- **THEN** la salida de conciliación indica el canal con cero registros en lugar de omitirlo
- **AND** los canales de proveedor que componen el MVP quedan pendientes de definición (OQ-09)

#### Scenario: Salida disponible por cada día conciliado
- **WHEN** finaliza un día conciliado según el criterio de corte configurado (OQ-35)
- **THEN** existe una salida de conciliación para ese día y para cada canal, sin generar más de una salida vigente por día y canal
- **AND** la hora de corte, la zona horaria y el tratamiento de estados pendientes del «día conciliado» quedan pendientes de definición (OQ-35)
### Requirement: Marcado de descalces
El sistema SHALL marcar cada descalce con la referencia de la transacción, el tipo de descalce y el estado actual de investigación.

Origen: criterio 2 de la HU. El catálogo de tipos de descalce y los estados de investigación son supuestos de trabajo pendientes de confirmar con operaciones (OQ-36).

#### Scenario: Descalce con datos completos
- **WHEN** se detecta un descalce
- **THEN** el registro del descalce contiene referencia de transacción, tipo de descalce y estado de investigación

#### Scenario: Estado inicial de investigación
- **WHEN** se detecta un descalce nuevo
- **THEN** el sistema le asigna un estado de investigación inicial que indica que aún no está resuelto

#### Scenario: Actualización del estado de investigación
- **WHEN** un analista de operaciones actualiza el estado de investigación de un descalce
- **THEN** el reporte y el resumen posteriores reflejan el estado actualizado

### Requirement: Filtrado de reportes de conciliación
El sistema SHALL permitir filtrar los reportes de conciliación por fecha y por canal de proveedor.

Origen: criterio 3 de la HU.

#### Scenario: Filtro por fecha
- **WHEN** el analista solicita el reporte de una fecha determinada
- **THEN** el reporte contiene solo registros de esa fecha

#### Scenario: Filtro por canal de proveedor
- **WHEN** el analista solicita el reporte de un canal de proveedor determinado
- **THEN** el reporte contiene solo registros de ese canal

#### Scenario: Filtro combinado sin resultados
- **WHEN** el analista aplica filtros de fecha y canal que no coinciden con ningún registro
- **THEN** el reporte se devuelve vacío con indicación explícita de que no hay registros, sin error

### Requirement: Resumen diario de conciliación
El sistema SHALL generar un resumen diario con los totales de registros conciliados, no conciliados y resueltos.

Origen: criterio 4 de la HU. La regla de conteo entre «no conciliados» y «resueltos» (si un descalce resuelto se resta de los no conciliados o se informa como subconjunto de ellos) está en OQ-37.

#### Scenario: Totales del día
- **WHEN** se completa la conciliación de un día
- **THEN** el resumen incluye el total de registros conciliados, no conciliados y resueltos de ese día

#### Scenario: Resumen por canal
- **WHEN** el analista consulta el resumen filtrado por canal de proveedor
- **THEN** los totales corresponden únicamente a ese canal

#### Scenario: Descalce resuelto
- **WHEN** un descalce pasa al estado de investigación resuelto
- **THEN** el resumen lo cuenta en el total de resueltos y deja de contarlo como descalce con investigación pendiente; su tratamiento en el total de no conciliados queda pendiente (OQ-37)

### Requirement: Distinción de originales y reintentos duplicados en reporte y resumen
El sistema SHALL consumir el marcado de origen (original o reintento duplicado) provisto por `payment-idempotency` para distinguir originales de reintentos duplicados en el reporte y el resumen diario.

Origen: criterio 4 de la HU de idempotencia (`payment-idempotency-protection`), consumido aquí; el escenario «Registro sin marcado de origen» es agregado por análisis.

#### Scenario: Intento original identificado en el reporte
- **WHEN** el reporte incluye un intento marcado como original
- **THEN** el reporte lo identifica como original
- **AND** la forma de exponer el marcado queda pendiente de definición (OQ-14)

#### Scenario: Marcado y auditoría de duplicados no son definidos por la conciliación
- **WHEN** la conciliación consume el marcado de origen provisto por la capability `payment-idempotency`
- **THEN** el sistema MUST NOT definir, generar ni modificar ese marcado ni el registro de auditoría de duplicados

#### Scenario: Duplicado cuyo original cae en otro día
- **WHEN** el reporte incluye un reintento duplicado cuyo intento original pertenece a otro día
- **THEN** el día asignado al duplicado queda pendiente de definición (OQ-14)

#### Scenario: Terminología de originales, duplicados y transacción financiera
- **WHEN** el reporte o el resumen usan los términos «original», «reintento duplicado» y «transacción financiera»
- **THEN** se entienden según [GLOSSARY.md](../../../../../docs/GLOSSARY.md)

#### Scenario: Reintento duplicado identificado y vinculado
- **WHEN** el reporte incluye una solicitud marcada como reintento duplicado
- **THEN** el reporte la identifica como reintento duplicado y la vincula al intento original

#### Scenario: Duplicado no se concilia como transacción adicional
- **WHEN** la conciliación procesa un reintento duplicado
- **THEN** no lo cruza como una transacción de wallet independiente contra el resultado del proveedor y no lo marca como descalce solo por no tener un resultado propio del proveedor

#### Scenario: Totales del resumen excluyen duplicados
- **WHEN** se genera el resumen diario y existen reintentos duplicados en el día
- **THEN** los totales de conciliados, no conciliados y resueltos no incluyen los reintentos duplicados y el resumen informa el total de reintentos duplicados por separado

#### Scenario: Filtros aplicados a duplicados
- **WHEN** el analista filtra el reporte o el resumen por fecha o por canal de proveedor
- **THEN** los reintentos duplicados se incluyen o excluyen según los mismos filtros que los demás registros

#### Scenario: Registro sin marcado de origen
- **WHEN** un registro llega a la conciliación sin marcado de origen
- **THEN** el reporte lo indica como sin marcado de origen y no lo asume como original ni como duplicado

#### Scenario: Varias transacciones financieras para un mismo intento original
- **WHEN** la conciliación encuentra más de una transacción financiera asociada a un mismo intento original
- **THEN** el reporte lo marca como descalce, con el tipo que defina el catálogo (OQ-36), porque la capability `payment-idempotency` garantiza como máximo una transacción financiera por clave (escenario agregado por análisis, derivado de la decisión 8 del diseño)

### Requirement: Alcance de la evaluación del descalce
El sistema SHALL reportar los totales de descalce sin evaluarlos contra un umbral de aceptación hasta que ese umbral sea definido por el negocio.

Origen: **agregado por análisis**. Justificación: la HU deja abierta la tasa máxima diaria de descalce aceptable (OQ-34); este requisito evita fijar un umbral no aprobado.

#### Scenario: Resumen sin umbral definido
- **WHEN** se genera el resumen diario y no existe un umbral de descalce definido
- **THEN** el resumen muestra solo los totales y no indica aprobación ni rechazo por tasa de descalce
