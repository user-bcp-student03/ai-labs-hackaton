# Tasks

> El repositorio es greenfield (sin código de aplicación): estas tareas describen trabajo futuro y no referencian archivos existentes. No implementar en este cambio.

## 1. Definiciones pendientes (no resueltas aquí)

_Cubre: supuestos y preguntas abiertas de la HU y decisiones transversales (OQ-05, OQ-06, OQ-07, OQ-19 a OQ-23). OQ-19 está decidida (motor configurable); el KYC real sigue pendiente de Cumplimiento._

- [ ] 1.1 Dependencia externa (OQ-19 decidida el 2026-11-06: motor de pasos configurable): el contenido real de KYC y documentación sigue pendiente de Cumplimiento; verificar que, cuando Cumplimiento lo defina, se carga como configuración sin cambiar el motor. No bloquea la construcción del motor y no se inventan requisitos aquí
- [ ] 1.2 Acordar con producto/analítica la frontera oficial de eventos (inicio/fin) que define la duración de onboarding (OQ-20); verificar que queda registrada en la documentación del cambio
- [ ] 1.3 Acordar con producto/analítica el glosario de "activación" (estado de wallet `activo` frente al evento de activación del pagador del cambio `payer-low-value-payment-confirmation`) y cuál alimenta el MAU (OQ-05), aprobando `docs/GLOSSARY.md`; verificar que el glosario queda aprobado y los nombres de eventos/atributos no colisionan
- [ ] 1.4 Confirmar con producto/marketing la fuente y el momento de captura del gasto de adquisición y la definición de "usuario nuevo" para CAC (OQ-22), y los nombres de los estados de la wallet distintos de `activo` (OQ-23); verificar que quedan documentados
- [ ] 1.5 Acordar con producto/analítica el alcance del evento de cierre del flujo y el criterio de abandono (OQ-21) y el criterio de pertenencia a la cohorte MVP Perú (OQ-06); verificar que quedan registrados (agregado por análisis)
- [ ] 1.6 Acordar con analítica y producto quién produce el reporte consolidado de MAU y CAC (OQ-07); verificar que queda un responsable nombrado (agregado por análisis: ningún cambio lo cubre)
- [ ] 1.7 Entregar el contrato de configuración de pasos (por paso: identificador, orden, datos requeridos, reglas de validez y mensaje accionable) con una configuración de ejemplo etiquetada «ejemplo no aprobado»; verificar que está documentado, que Cumplimiento puede cargar sus pasos reales con él sin cambiar el motor y que el ejemplo no se presenta como requisito regulatorio (decisión OQ-19)

## 2. Flujo de onboarding y pasos visibles

_Cubre: criterio 1 de la HU._

- [ ] 2.1 Implementar el motor de pasos configurable a partir del contrato de la tarea 1.7 (lista, orden, datos requeridos y reglas de validación); verificar con una prueba, usando pasos «ejemplo no aprobado», que cambiar la configuración cambia los pasos sin modificar el comportamiento del flujo
- [ ] 2.2 Mostrar la secuencia de pasos, el paso actual y el progreso en todo momento; verificar con pruebas de los escenarios de inicio, avance y permanencia tras error, usando pasos «ejemplo no aprobado»

## 3. Validación bloqueante

_Cubre: criterio 2 de la HU._

- [ ] 3.1 Implementar la validación por paso, tomada de la configuración, que bloquea el avance ante datos faltantes o inválidos; verificar con pruebas de los escenarios de dato faltante, dato inválido, corrección y cambio de regla configurada, usando pasos «ejemplo no aprobado»
- [ ] 3.2 Externalizar en la configuración los mensajes accionables asociados al dato concreto; verificar que cada regla de validación de la configuración de ejemplo tiene un mensaje que indica cómo corregir

## 4. Activación del estado de la wallet

_Cubre: criterio 3 de la HU._

- [ ] 4.1 Implementar el estado de la wallet y la transición a `activo` solo en el cierre exitoso del flujo, idempotente ante cierres repetidos; verificar con pruebas de cierre correcto, onboarding incompleto y cierre repetido
- [ ] 4.2 Habilitar el acceso al punto de entrada de pagos de bajo monto solo con wallet `activo`; verificar con pruebas de acceso permitido y denegado

## 5. Eventos de analítica

_Cubre: criterios 4 y 5 de la HU; la tarea 5.2 es agregada por análisis._

- [ ] 5.1 Registrar los eventos de inicio, de finalización de cada paso y de cierre con marca de tiempo, identificador de onboarding y atributo de cohorte MVP Perú; verificar con pruebas de cada escenario de registro
- [ ] 5.2 Deduplicar eventos por onboarding, tipo y paso ante reintentos del cliente; verificar con una prueba de envío repetido que conserva un único evento (agregado por análisis)
- [ ] 5.3 Dejar los datos listos para calcular duración por usuario y mediana de la cohorte sin fijar la frontera, y generar el reporte mensual de mediana con la comparación 8 → 3 minutos como parámetros; verificar con una consulta de ejemplo que calcula la mediana con una frontera de prueba (escenarios «Cálculo de la mediana de la cohorte» y «Reporte periódico de duración»), una vez definida la tarea 1.2

## 6. Salida analítica de MAU y CAC

_Cubre: criterio 6 de la HU._

- [ ] 6.1 Producir la salida mensual de conteo de nuevos usuarios activos de la cohorte MVP Perú; verificar con datos de prueba de meses 1-3, excluyendo onboardings no finalizados
- [ ] 6.2 Incorporar la atribución de gasto de adquisición, en PEN, según la fuente confirmada en la tarea 1.4, indicando "no disponible" cuando falte el dato; verificar con datos de prueba que permite calcular el CAC por usuario nuevo y los parámetros de referencia 1,000–2,000 y PEN 10 (escenarios «Atribución de gasto de adquisición», «Campos de la salida mensual» y «Mes sin gasto de adquisición disponible»)
- [ ] 6.3 Documentar la salida analítica (campos y significado, incluyendo el glosario de "activación" de la tarea 1.3); verificar que la documentación coincide con los campos entregados

## 7. Integración

- [ ] 7.1 Verificar de extremo a extremo el recorrido de un usuario nuevo con pasos «ejemplo no aprobado» (inicio, pasos, error y corrección, cierre, wallet `activo`, acceso a pagos de bajo monto) y que los eventos registrados son coherentes con ese recorrido
