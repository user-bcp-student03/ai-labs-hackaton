# Spec Delta

## Purpose

Define el comportamiento que el pagador observa al completar una transferencia de bajo monto: datos previos a la confirmación, resultado terminal único, referencia persistida, siguiente acción tras fallo o expiración sin cobros duplicados (apoyada en la capability `payment-idempotency`), verificación del intento previo antes de un nuevo intento y evento de activación.

## ADDED Requirements

### Requirement: Resumen previo a la confirmación final
La pantalla de pago MUST mostrar la identidad del destino y el monto de la transferencia antes de que el pagador realice la confirmación final.

Origen: criterio 1 de la HU. El escenario «No se permite confirmar sin datos del destino» es agregado por análisis (precisa el criterio 1).

#### Scenario: Se muestran destino y monto
- **WHEN** el pagador llega al paso de confirmación final de una transferencia de bajo monto
- **THEN** la pantalla muestra la identidad del destino y el monto a transferir

#### Scenario: No se permite confirmar sin datos del destino
- **WHEN** la identidad del destino o el monto no están disponibles
- **THEN** el sistema no habilita la confirmación final y muestra al pagador una acción para volver

### Requirement: Validación de monto antes del envío
El sistema MUST validar el monto antes de enviar el pago e informar al pagador el motivo del rechazo.

Origen: **agregado por análisis** (no es un criterio de aceptación; justificación en el escenario «Justificación del requisito»). Regla inicial de monto bajo: OQ-15.

#### Scenario: Justificación del requisito
- **WHEN** se revisa el origen de esta validación
- **THEN** consta que el contexto de la HU exige que la validación de monto visible al usuario se aplique antes del envío, que la épica indica que los límites por proveedor pueden estar por debajo del máximo regulatorio, y que la regla de monto bajo y el límite aplicable al proveedor/canal son los criterios de validación

#### Scenario: Monto dentro del límite
- **WHEN** el pagador ingresa un monto que cumple la regla de monto bajo y el límite del proveedor/canal
- **THEN** el sistema permite continuar a la confirmación final

#### Scenario: Monto por encima del límite del proveedor
- **WHEN** el pagador ingresa un monto que excede el límite del proveedor/canal, aunque no supere el máximo regulatorio
- **THEN** el sistema no envía el pago y muestra un mensaje que indica que el monto excede el límite permitido y cuál es el límite aplicable al proveedor/canal

#### Scenario: Regla de monto bajo pendiente de definición
- **WHEN** la regla inicial de monto bajo por proveedor/canal aún no está definida (OQ-15, pregunta abierta de la HU)
- **THEN** la regla se obtiene de configuración y no se fija un valor en esta especificación

### Requirement: Resultado terminal único por intento
El sistema MUST entregar al pagador exactamente un resultado terminal por intento de pago, que sea exitoso, fallido o expirado, aun cuando el estado del pago cambie de forma asíncrona.

Origen: criterio 2 de la HU. El escenario «Estado pendiente antes del resultado» es agregado por análisis (transiciones asíncronas indicadas en el contexto de la HU). El tiempo máximo del intento antes de expirar queda en OQ-17 y se obtiene de configuración.

#### Scenario: Estado pendiente antes del resultado
- **WHEN** el pago fue enviado y el proveedor aún no informa un estado final
- **THEN** el pagador ve un estado de procesamiento no terminal y no se muestra un resultado definitivo

#### Scenario: Un solo resultado terminal
- **WHEN** el intento alcanza un estado terminal
- **THEN** el pagador recibe un único resultado (exitoso, fallido o expirado) y las notificaciones o señales posteriores del mismo intento no lo cambian ni lo duplican

#### Scenario: Expiración sin respuesta
- **WHEN** vence el tiempo máximo del intento (valor configurable, OQ-17) sin confirmación del proveedor
- **THEN** el intento se marca como expirado y se informa al pagador como resultado terminal

### Requirement: Referencia de transacción en pagos exitosos
Cuando un pago es exitoso, el sistema MUST mostrar al pagador una referencia de transacción y MUST persistirla en el historial del pagador.

Origen: criterio 3 de la HU. La referencia identifica al intento de pago (término común con comercio, soporte y conciliación); el momento de asignación se asume desde la creación del intento y está en OQ-04.

#### Scenario: Pago exitoso
- **WHEN** el intento termina como exitoso
- **THEN** se muestra la referencia de transacción y esa misma referencia queda registrada en el historial del pagador

#### Scenario: Consulta posterior en el historial
- **WHEN** el pagador consulta su historial después de un pago exitoso
- **THEN** la transacción aparece con la misma referencia mostrada al confirmar

### Requirement: Siguiente acción tras fallo o expiración
Cuando un pago falla o expira, el sistema MUST ofrecer al pagador una siguiente acción (reintentar o volver) sin crear cobros duplicados.

Origen: criterio 4 de la HU. Decisiones OQ-01 y OQ-02 (Decidida, 2026-11-06); el bloqueo por intento previo está en el requisito «Verificación del intento previo antes de un nuevo intento». Ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md); detalles en los escenarios.

#### Scenario: Apoyo en payment-idempotency
- **WHEN** se evalúa la protección contra cobros duplicados de este flujo
- **THEN** se apoya en la capability `payment-idempotency` sin redefinirla en este flujo

#### Scenario: Identificador de intención al abrir la confirmación (decisión OQ-01)
- **WHEN** se abre la pantalla de confirmación de un pago
- **THEN** este flujo genera un identificador de intención y lo envía a `payment-idempotency` en cada envío de esa confirmación
- **AND** `payment-idempotency` deriva la clave a partir de ese identificador más pagador, monto, destino y ventana de intento, y este flujo no deriva ni calcula la clave

#### Scenario: Distinción de términos
- **WHEN** se usan los términos «reintentar» y «reintento duplicado»
- **THEN** «reintentar» es la acción del usuario y «reintento duplicado» es la solicitud repetida con la misma clave; son distintos (ver GLOSSARY.md)

#### Scenario: Pago fallido
- **WHEN** el intento termina como fallido
- **THEN** el pagador ve el resultado y exactamente las acciones "reintentar" y "volver"

#### Scenario: Pago expirado
- **WHEN** el intento termina como expirado
- **THEN** el pagador ve el resultado y exactamente las acciones "reintentar" y "volver"

#### Scenario: Repetición de la misma confirmación
- **WHEN** el pagador repite la confirmación del mismo intento por doble toque o pérdida de conexión
- **THEN** este flujo reenvía el mismo identificador de intención, el sistema no genera más de un cobro para ese intento, conforme al comportamiento de `payment-idempotency`, y el pagador ve el resultado original de ese intento

#### Scenario: Reintentar crea un nuevo intento vinculado (decisión OQ-02)
- **WHEN** el pagador elige "reintentar" tras un intento fallido o expirado y la verificación del intento previo lo permite
- **THEN** el sistema crea un nuevo intento con un nuevo identificador de intención (nueva clave en `payment-idempotency`), una nueva referencia de transacción y el vínculo «reintento de» hacia el intento original
- **AND** el nuevo intento genera como máximo un cobro

#### Scenario: La clave original conserva el resultado original (decisión OQ-02)
- **WHEN** se recibe una solicitud con el identificador de intención del intento original ya fallido o expirado
- **THEN** el sistema devuelve el resultado original de ese intento, no crea un cobro y no lo reemplaza por el del nuevo intento vinculado

#### Scenario: Intento expirado con confirmación tardía
- **WHEN** un intento expirado recibe posteriormente una confirmación del proveedor
- **THEN** el sistema no genera un segundo cobro, el resultado terminal ya entregado no se modifica y la inconsistencia queda registrada como discrepancia disponible para su tratamiento operativo (fuera de alcance de este cambio; OQ-10)

### Requirement: Verificación del intento previo antes de un nuevo intento
El sistema MUST consultar el estado del intento previo y MUST NOT permitir un nuevo intento mientras ese intento esté en proceso o incierto.

Origen: decisión OQ-03 (Decidida, 2026-11-06). Alcance y definición de «incierto» en escenarios (agregados por análisis).

#### Scenario: Alcance y definición de incierto
- **WHEN** se evalúa qué intento previo bloquea y qué significa «incierto»
- **THEN** el intento previo es el de la misma intención de pago (pagador, monto y destino) y «incierto» designa al intento sin resultado terminal cuyo estado no pudo confirmarse con el proveedor
- **AND** no es un estado nuevo de la máquina de estados y ambos criterios son agregados por análisis

#### Scenario: Previo en proceso bloquea el nuevo intento (decisión OQ-03)
- **WHEN** el pagador intenta un nuevo intento de la misma intención de pago y el intento previo no es terminal (creado o en proceso)
- **THEN** el sistema no crea el nuevo intento, no envía nada a `payment-idempotency` y no genera un cobro nuevo

#### Scenario: Previo incierto bloquea el nuevo intento (decisión OQ-03)
- **WHEN** el pagador intenta un nuevo intento y el estado del intento previo es incierto, incluido el caso en que la consulta de verificación no se completa
- **THEN** el sistema no crea el nuevo intento y no genera un cobro nuevo

#### Scenario: Previo terminal permite el nuevo intento (decisión OQ-03)
- **WHEN** el pagador intenta un nuevo intento y el intento previo terminó como fallido o expirado
- **THEN** el sistema permite crear el nuevo intento vinculado al previo, conforme al escenario «Reintentar crea un nuevo intento vinculado (decisión OQ-02)»

#### Scenario: Mensaje accionable durante el bloqueo (decisión OQ-03)
- **WHEN** el sistema bloquea un nuevo intento por un previo en proceso o incierto
- **THEN** el pagador ve un mensaje que indica que su pago anterior sigue en proceso o pendiente de confirmación y que debe esperar su resultado, con las acciones «ver estado del pago anterior» y «volver»
- **AND** no se crea ningún cobro, intento ni referencia nueva, y el texto proviene de contenido configurable

#### Scenario: Fin del bloqueo al llegar a un estado terminal (decisión OQ-03)
- **WHEN** el intento previo bloqueante alcanza un estado terminal, incluida la expiración por tiempo máximo (OQ-17)
- **THEN** el bloqueo se levanta y, si el resultado es fallido o expirado, el pagador puede elegir "reintentar"

#### Scenario: Repetición de la misma confirmación no es un nuevo intento
- **WHEN** el pagador repite la confirmación del mismo intento con el mismo identificador de intención mientras sigue en proceso
- **THEN** se trata como solicitud repetida conforme a `payment-idempotency` (estado actual del intento original) y no como un nuevo intento bloqueado

### Requirement: Etiquetas de estados terminales pendientes de definición
El sistema MUST distinguir los tres estados terminales (exitoso, fallido, expirado) mediante identificadores y etiquetas diferentes entre sí; los textos finales mostrados al usuario MUST provenir de configuración de contenido hasta que producto los defina.

Origen: **agregado por análisis**. Justificación: la HU declara como supuesto que las etiquetas de los estados terminales quedan por definir con producto (OQ-16).

#### Scenario: Estados distinguibles
- **WHEN** el pagador ve un resultado terminal
- **THEN** la etiqueta mostrada corresponde a uno solo de los tres estados y es distinta de las etiquetas de los otros dos

### Requirement: Evento de activación del pagador
Cada transacción exitosa del pagador MUST emitir el evento de activación utilizado en el cálculo de MAU, una sola vez por transacción.

Origen: criterio 6 de la HU. El «evento de activación del pagador» es distinto del estado de wallet `activo` del onboarding (ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md)). Qué evento alimenta oficialmente el MAU y cómo se define el MAU está en OQ-05; el reporte consolidado de MAU, en OQ-07.

#### Scenario: Evento por pago exitoso
- **WHEN** un intento termina como exitoso
- **THEN** se emite un evento de activación con la referencia de transacción, el identificador del pagador, la marca de tiempo y el atributo de cohorte MVP Perú

#### Scenario: Sin evento en pagos no exitosos
- **WHEN** un intento termina como fallido o expirado
- **THEN** no se emite evento de activación

#### Scenario: Sin eventos duplicados
- **WHEN** se reciben señales repetidas del mismo pago exitoso
- **THEN** se emite un único evento de activación para esa transacción

#### Scenario: Conteo mensual de pagadores activos
- **WHEN** analítica consulta los eventos de activación de un mes de los meses 1-3 posteriores al lanzamiento
- **THEN** puede obtener el número de pagadores distintos con al menos un evento de activación en ese mes (según la definición de MAU de OQ-05) y compararlo con el rango de referencia 1,000–2,000, configurable como parámetro de reporte

### Requirement: Instrumentación del funnel de checkout
El sistema MUST registrar los eventos del funnel de checkout de este flujo para la cohorte MVP Perú y MUST permitir reportar la tasa de caída en checkout frente a la línea base de 30% y el objetivo de 8% dentro del trimestre posterior al lanzamiento.

Origen: criterio 5 de la HU. La fórmula de la tasa (qué es "abandono", numerador y denominador) y el período exacto de la línea base de 30% están en OQ-18; la pertenencia a la cohorte, en OQ-06.

#### Scenario: Eventos de funnel registrados
- **WHEN** un pagador de la cohorte MVP Perú avanza o abandona el flujo de pago
- **THEN** quedan registrados, con marca de tiempo y referencia del intento, los eventos de inicio, confirmación final y resultado terminal del intento, o el abandono

#### Scenario: Reporte de caída en checkout
- **WHEN** se genera el reporte de un período para la cohorte MVP Perú
- **THEN** el reporte incluye los conteos de intentos iniciados, confirmaciones finales, resultados exitoso, fallido y expirado, y abandonos, la tasa de caída en checkout del período, y su comparación con la línea base de 30% y el objetivo de 8% como parámetros configurables

#### Scenario: Fórmula de la tasa pendiente de definición
- **WHEN** la definición de "caída en checkout" aún no está acordada (OQ-18)
- **THEN** el reporte entrega los conteos por evento del escenario anterior sin fijar la fórmula de la tasa en esta especificación
