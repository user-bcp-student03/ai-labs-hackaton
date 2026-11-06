# Tasks

> Repositorio greenfield: no hay código existente. Las tareas describen trabajo futuro de implementación; las herramientas se definen durante la implementación (supuesto de la HU).

## 1. Definiciones previas

_Cubre: supuestos y preguntas abiertas de la HU y decisiones transversales (OQ-09, OQ-14, OQ-24, OQ-33 a OQ-37)._

- [ ] 1.1 Confirmar con operaciones los canales de proveedor del MVP y la referencia de transacción común para el cruce (OQ-09); verificar que quedan documentados
- [ ] 1.2 Confirmar el catálogo de tipos de descalce y los estados de investigación, incluido el estado "resuelto" (OQ-36), y la regla de conteo de resueltos frente a no conciliados (OQ-37); verificar que quedan documentados
- [ ] 1.3 Definir el criterio de día conciliado (hora de corte, zona horaria) y el tratamiento de estados asíncronos pendientes (OQ-35); verificar que queda como valor de configuración
- [ ] 1.4 Elegir herramientas y ubicación de los componentes de conciliación (decisión de implementación)
- [ ] 1.5 Acordar con `payment-idempotency-protection` cómo se expone el marcado original/duplicado (con vínculo al original) y a qué día se asigna un reintento duplicado (OQ-14); verificar con una nota de acuerdo
- [ ] 1.6 Acordar con `payer-low-value-payment-confirmation` y `merchant-qr-payment-status-visibility` los estados y la referencia que se consumen (OQ-24, OQ-09); verificar con una nota de acuerdo por cada uno (agregado por análisis)
- [ ] 1.7 Acordar con soporte y operaciones la relación entre el estado de investigación del descalce y el estado de resolución de soporte (OQ-33); verificar que queda registrada (agregado por análisis)

## 2. Conciliación diaria

_Cubre: criterio 1 de la HU; las tareas 2.4 y 2.5 son agregadas por análisis._

- [ ] 2.1 Obtener registros de wallet (intención y asiento de ledger) y resultados del proveedor por canal y día
- [ ] 2.2 Cruzar registros por referencia de transacción y clasificarlos como conciliados o no conciliados
- [ ] 2.3 Incluir los canales sin movimientos con cero registros en la salida; verificar con una prueba del escenario «Canal sin movimientos»
- [ ] 2.4 Detectar registros con datos diferentes (monto o estado terminal) e intenciones exitosas sin asiento de ledger; verificar con pruebas de los escenarios «Registros con datos diferentes» e «Intención de pago sin asiento de ledger» (agregado por análisis)
- [ ] 2.5 Generar una salida por día y canal según el criterio de corte; verificar con una prueba del escenario «Salida disponible por cada día conciliado» (agregado por análisis)

## 3. Consumo del marcado original/duplicado

_Cubre: criterio 4 de la HU de idempotencia consumido aquí; la tarea 3.3 es agregada por análisis._

- [ ] 3.1 Leer el marcado de origen (original o duplicado, con vínculo al original) provisto por `payment-idempotency` sin recalcularlo ni redefinirlo
- [ ] 3.2 Excluir los reintentos duplicados del cruce como transacciones independientes, evitando marcarlos como descalce solo por no tener resultado propio del proveedor
- [ ] 3.3 Manejar los registros sin marcado de origen indicándolos como tales, sin asumirlos originales ni duplicados (agregado por análisis)
- [ ] 3.4 Marcar como descalce los casos con más de una transacción financiera asociada a un mismo intento original; verificar con una prueba del escenario «Varias transacciones financieras para un mismo intento original» (agregado por análisis)

## 4. Marcado y seguimiento de descalces

_Cubre: criterio 2 de la HU._

- [ ] 4.1 Registrar cada descalce con referencia, tipo y estado de investigación inicial
- [ ] 4.2 Permitir actualizar el estado de investigación de un descalce

## 5. Reportes y resumen

_Cubre: criterios 3 y 4 de la HU; la tarea 5.5 es agregada por análisis (OQ-34)._

- [ ] 5.1 Implementar el reporte de conciliación con filtros por fecha y canal (incluido el caso vacío sin error)
- [ ] 5.2 Mostrar en el reporte la distinción original/reintento duplicado, con el vínculo de cada duplicado a su original, respetando los mismos filtros
- [ ] 5.3 Generar el resumen diario con totales de conciliados, no conciliados y resueltos, también filtrable por canal
- [ ] 5.4 Informar en el resumen el total de reintentos duplicados por separado, sin incluirlos en los totales de conciliados, no conciliados ni resueltos
- [ ] 5.5 Asegurar que el resumen no evalúe umbrales de descalce mientras OQ-34 siga sin respuesta (agregado por análisis)

## 6. Verificación

- [ ] 6.1 Pruebas de los escenarios de `specs/transaction-reconciliation/spec.md`, incluida la distinción de originales y duplicados
- [ ] 6.2 Validar con `openspec validate ops-transaction-reconciliation --strict`
