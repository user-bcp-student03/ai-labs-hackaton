# Tasks

> El repositorio es greenfield (sin código de aplicación): estas tareas describen trabajo futuro y no referencian archivos existentes. No implementar en este cambio.

## 1. Definiciones pendientes (no resueltas aquí)

_Cubre: preguntas abiertas y supuestos de la HU y decisiones transversales (OQ-04 a OQ-06, OQ-10, OQ-15 a OQ-18 abiertas; OQ-01 a OQ-03 decididas el 2026-11-06)._

- [ ] 1.1 Obtener de producto la regla inicial de monto bajo por proveedor/canal para el MVP (OQ-15, pregunta abierta de la HU); verificar que queda registrada como valor de configuración
- [ ] 1.2 Obtener de producto las etiquetas de los estados terminales (exitoso, fallido, expirado) (OQ-16); verificar que quedan cargadas como contenido configurable
- [ ] 1.3 Acordar con producto/analítica la definición del evento de activación (OQ-05), del abandono y de la fórmula de caída en checkout (OQ-18), el tiempo máximo de un intento (OQ-17) y el criterio de cohorte MVP Perú (OQ-06); verificar que cada definición queda registrada en `docs/OPEN-QUESTIONS.md` con estado distinto de "Abierta"
- [ ] 1.4 Acordar con el cambio `payment-idempotency-protection` el contrato de entrada del identificador de intención (formato, obligatoriedad y comportamiento si falta), conforme a la decisión OQ-01 (híbrida, Decidida 2026-11-06); verificar que ambos cambios describen el mismo contrato
- [ ] 1.5 Registrar en `docs/OPEN-QUESTIONS.md` las decisiones OQ-01, OQ-02 y OQ-03 como «Decidida (2026-11-06)» con la opción elegida; verificar que el estado de las tres deja de ser «Abierta» y que ya no figura la marca de bloqueo sobre este cambio. Acordar con arquitectura qué condiciones de proveedor/consulta se consideran «incierto» para la verificación del intento previo (decisión OQ-03); verificar que quedan documentadas
- [ ] 1.6 Acordar con operaciones qué se comunica al pagador y al historial ante una confirmación tardía de un intento expirado (OQ-10) y confirmar el momento de asignación de la referencia de transacción (OQ-04); verificar que ambas decisiones quedan registradas (agregado por análisis)

## 2. Reglas de monto y validación previa al envío

_Cubre: requisito agregado por análisis «Validación de monto antes del envío» (contexto de la HU)._

- [ ] 2.1 Implementar la configuración de reglas de monto/límites por proveedor/canal
- [ ] 2.2 Validar el monto antes del envío y mostrar un mensaje que indique el motivo del rechazo y el límite aplicable
- [ ] 2.3 Pruebas de los escenarios "Validación de monto antes del envío"

## 3. Pantalla de confirmación

_Cubre: criterio 1 de la HU._

- [ ] 3.1 Mostrar identidad del destino y monto antes de la confirmación final
- [ ] 3.2 Bloquear la confirmación si faltan datos del destino o monto
- [ ] 3.3 Pruebas de los escenarios de "Resumen previo a la confirmación final"

## 4. Estado del pago y resultado terminal único

_Cubre: criterio 2 de la HU; la etiqueta configurable de estados es agregada por análisis (OQ-16)._

- [ ] 4.1 Implementar la máquina de estados del intento (creado, en proceso, exitoso, fallido, expirado) con estados terminales inmutables
- [ ] 4.2 Manejar transiciones asíncronas del proveedor y la expiración por tiempo máximo configurable
- [ ] 4.3 Mostrar estado "en proceso" y resultado terminal con textos desde contenido configurable
- [ ] 4.4 Pruebas de resultado único, señales repetidas y confirmación tardía tras expiración

## 5. Siguiente acción y consumo de idempotencia

_Cubre: criterio 4 de la HU y las decisiones OQ-01, OQ-02 y OQ-03 (Decididas, 2026-11-06); el requisito «Verificación del intento previo antes de un nuevo intento» es agregado por análisis a partir de OQ-03._

- [ ] 5.1 Ofrecer exactamente las acciones "reintentar" y "volver" tras fallo o expiración; "reintentar" crea un nuevo intento vinculado al original (nuevo identificador de intención, nueva referencia de transacción y vínculo «reintento de», decisión OQ-02) sin modificar el estado ni el resultado del intento original; verificar con pruebas de los escenarios «Pago fallido», «Pago expirado» y «Reintentar crea un nuevo intento vinculado (decisión OQ-02)»
- [ ] 5.2 Generar el identificador de intención al abrir la pantalla de confirmación y enviarlo a `payment-idempotency` (cambio `payment-idempotency-protection`) en cada envío de esa confirmación, reutilizándolo en las repeticiones y generando uno nuevo por cada intento nuevo (decisión OQ-01); sin derivar ni calcular la clave ni implementar lógica de duplicados propias; verificar con pruebas del escenario «Identificador de intención al abrir la confirmación (decisión OQ-01)»
- [ ] 5.3 Pruebas de aceptación del lado del pagador: ante doble toque y pérdida de conexión se ve un solo cobro y el resultado original (escenario «Repetición de la misma confirmación»), tras «reintentar» el nuevo intento genera como máximo un cobro y la clave original sigue devolviendo el resultado original (escenarios «Reintentar crea un nuevo intento vinculado (decisión OQ-02)» y «La clave original conserva el resultado original (decisión OQ-02)»); la clave y la auditoría de duplicados se prueban en `payment-idempotency-protection`
- [ ] 5.4 Implementar la verificación del intento previo (decisión OQ-03): consultar el estado del intento previo de la misma intención de pago (pagador, monto y destino) antes de crear un nuevo intento; bloquear si está en proceso o incierto (incluida una consulta que no se completa) y permitir si es fallido o expirado; verificar con pruebas de los escenarios «Alcance y definición de incierto», «Previo en proceso bloquea el nuevo intento (decisión OQ-03)», «Previo incierto bloquea el nuevo intento (decisión OQ-03)» y «Previo terminal permite el nuevo intento (decisión OQ-03)»
- [ ] 5.5 Mostrar durante el bloqueo un mensaje accionable (pago anterior en proceso o pendiente de confirmación, esperar su resultado) con las acciones «ver estado del pago anterior» y «volver», con textos desde contenido configurable; verificar que no se crea cobro, intento ni referencia nuevos, que el bloqueo se levanta al llegar el previo a un estado terminal y que una repetición con el mismo identificador de intención no se trata como nuevo intento (escenarios «Mensaje accionable durante el bloqueo (decisión OQ-03)», «Fin del bloqueo al llegar a un estado terminal (decisión OQ-03)» y «Repetición de la misma confirmación no es un nuevo intento»)

## 6. Referencia e historial

_Cubre: criterio 3 de la HU._

- [ ] 6.1 Asignar y mostrar la referencia de transacción en pagos exitosos
- [ ] 6.2 Persistir la referencia en el historial del pagador de forma consistente con el estado terminal
- [ ] 6.3 Pruebas de coincidencia entre referencia mostrada y persistida

## 7. Instrumentación

_Cubre: criterios 5 y 6 de la HU._

- [ ] 7.1 Emitir el evento de activación una sola vez por transacción exitosa, con referencia, pagador, marca de tiempo y atributo de cohorte MVP Perú; verificar con pruebas de los escenarios «Evento por pago exitoso», «Sin evento en pagos no exitosos» y «Sin eventos duplicados»
- [ ] 7.2 Emitir eventos de funnel de checkout (inicio, confirmación final, resultado terminal, abandono) con atributo de cohorte MVP Perú
- [ ] 7.3 Verificar con datos de prueba que el reporte de caída en checkout entrega los conteos por evento y la comparación con la línea base de 30% y el objetivo de 8% como parámetros, y que el conteo mensual de pagadores con evento de activación permite compararse con el rango 1,000–2,000 de los meses 1-3 (escenarios «Reporte de caída en checkout» y «Conteo mensual de pagadores activos»; la fórmula depende de OQ-05 y OQ-18)
