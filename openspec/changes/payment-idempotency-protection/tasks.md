# Tasks

> El repositorio es greenfield (sin código de aplicación): estas tareas describen trabajo futuro y no referencian archivos existentes. No implementar en este cambio.

## 1. Definiciones pendientes (no resueltas aquí)

_Cubre: preguntas abiertas de la HU y decisiones transversales (OQ-11, OQ-12, OQ-13 abiertas; OQ-01, OQ-02, OQ-14 decididas el 2026-11-06)._

- [ ] 1.1 Obtener de producto/operaciones la aprobación de la ventana de retención de claves por canal (OQ-11, pregunta abierta de la HU; propuesta provisional de 24 h por canal, no aprobada) y de la duración de la ventana de intento (OQ-12; propuesta provisional de 5 min, no aprobada); verificar que quedan registradas como valores de configuración
- [ ] 1.2 Acordar con los equipos de `payer-low-value-payment-confirmation`, `payment-failure-reversal-handling` y `ops-transaction-reconciliation` que consumirán el contrato de `payment-idempotency`; verificar con una nota de acuerdo por cada uno
- [ ] 1.3 Verificar que las decisiones del 2026-11-06 (OQ-01 híbrida, OQ-02 nuevo intento vinculado, OQ-14 diferir) figuran como "Decidida (2026-11-06)" en `docs/OPEN-QUESTIONS.md` y que los equipos de los cambios hermanos las conocen; ya no bloquean el grupo 2 (agregado por análisis: coordina el solape con pagador, soporte y conciliación)
- [ ] 1.4 Acordar con operaciones/compliance el período de conservación del registro de auditoría de duplicados (OQ-13; propuesta provisional "sin purga", no aprobada); verificar que queda registrado como valor de configuración (agregado por análisis: supuesto del diseño)

## 2. Clave de idempotencia y resultado original

_Cubre: criterios 1 y 2 de la HU; las tareas 2.4 y 2.5 son agregadas por análisis (restricción multirriel de la épica y decisión OQ-02)._

- [ ] 2.1 Implementar la derivación de la clave en el servidor por pagador, monto, destino, ventana de intento e identificador de intención recibido del flujo del pagador (OQ-01, decidida: híbrida); verificar con pruebas de los escenarios "Intento nuevo recibe clave", "Cambio de algún componente genera otra clave", "Pago legítimo idéntico con otra intención no es duplicado" y "Mismo identificador de intención repetido es duplicado"
- [ ] 2.2 Implementar el registro atómico clave → transacción/resultado; verificar con una prueba de solicitudes concurrentes con la misma clave que crea una sola transacción
- [ ] 2.3 Devolver el resultado original (terminal o estado actual) ante solicitudes repetidas sin crear transacción financiera; verificar con pruebas de los escenarios de repetición con resultado terminal y en proceso
- [ ] 2.4 Verificar con un proveedor simulado en al menos dos canales que el comportamiento es idéntico sin depender del riel (agregado por análisis)
- [ ] 2.5 Crear un nuevo intento vinculado (nueva clave, nueva referencia, vínculo "reintento de") al reintentar tras fallo o expiración, y almacenar el vínculo reintento → original; verificar con pruebas de los escenarios "Reintentar tras fallo o expiración crea un nuevo intento vinculado", "La clave original sigue devolviendo el resultado original" y "Vínculo reintento-original almacenado" (OQ-02, decidida; agregado por análisis)

## 3. Auditoría de duplicados

_Cubre: criterio 3 de la HU._

- [ ] 3.1 Registrar cada solicitud duplicada (append-only) con identificador de solicitud, identificador de correlación y clave; verificar con pruebas de los escenarios "Duplicado registrado" y "Cada duplicado genera su propio registro"
- [ ] 3.2 Permitir relacionar un duplicado con el original por clave y correlación; verificar con una consulta de auditoría de ejemplo

## 4. Retención de claves

_Cubre: requisito "Retención de claves configurable por canal" (agregado por análisis; deriva de OQ-11)._

- [ ] 4.1 Leer la ventana de retención por canal desde configuración (valor provisional de 24 h por canal, propuesta no aprobada); verificar con pruebas de los escenarios de ventana definida y no definida (agregado por análisis)
- [ ] 4.2 Documentar el comportamiento por defecto mientras la ventana no esté definida; verificar que el documento referencia OQ-11 (agregado por análisis)

## 5. Insumo para conciliación

_Cubre: criterio 4 de la HU._

- [ ] 5.1 Marcar cada solicitud con tipo (original o duplicado) y vínculo al original, y exponer además la fecha de la solicitud y la fecha del original como fuente de datos; verificar con pruebas de los escenarios "Intento original identificado", "Reintento duplicado identificado", "Datos expuestos por solicitud" y "Reintento vinculado distinguido del duplicado" (OQ-14, decidida: diferir)
- [ ] 5.2 Verificar con datos de ejemplo que los duplicados no se cuentan como transacciones financieras adicionales en los totales
- [ ] 5.3 Entregar a `ops-transaction-reconciliation` la descripción del atributo de tipo, el vínculo al original y las dos fechas; verificar que su equipo confirma el formato y que la regla de día de reporte del duplicado queda a cargo de conciliación (Fase 2), con prueba del escenario "Día de reporte del duplicado no asignado aquí"

## 6. Integración

_Cubre: verificación transversal de los criterios 1 a 4._

- [ ] 6.1 Ejecutar un flujo de extremo a extremo (intento original, reintento duplicado, reintento vinculado tras fallo, consulta de auditoría y salida con tipo, vínculo y fechas) con un proveedor simulado; verificar que coincide con todos los escenarios de `payment-idempotency`
