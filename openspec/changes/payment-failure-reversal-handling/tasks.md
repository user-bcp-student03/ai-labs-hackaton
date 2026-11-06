# Tasks

> Repositorio greenfield: no existe código de aplicación. Las rutas y tecnologías concretas se definirán al elegir el stack; estas tareas son agnósticas de tecnología. No se implementa nada en este cambio.
>
> Pendientes sin responder (ver grupo 6 y [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md)): categorías de disputa en MVP (OQ-29) y niveles de escalamiento/SLA (OQ-30) no bloquean el modelo base, pero deben resolverse antes de habilitar disputas; OQ-02 y OQ-32 bloquean las tareas 2.3 y 2.1 respectivamente.

## 1. Taxonomía de códigos de motivo

_Cubre: criterio 1 de la HU; el código "no clasificado" es agregado por análisis._

- [ ] 1.1 Definir el catálogo de códigos de motivo de falla/expiración (incluido "no clasificado") y documentarlo; verificar que cada código tenga descripción y tipo (falla técnica / incierto / transferencia ejecutada) revisado con soporte
- [ ] 1.2 Definir el mapeo desde motivos de cada riel/proveedor al catálogo interno y verificarlo con pruebas que cubran motivos conocidos y desconocidos (escenarios del requisito de código de motivo)
- [ ] 1.3 Almacenar el código de motivo y el motivo original asociados a la referencia de transacción; verificar con pruebas que pagos fallidos y expirados siempre quedan con código

## 2. Elegibilidad y vista de soporte

_Cubre: criterio 2 de la HU; las tareas 2.3 y 2.4 son agregadas por análisis (riesgo de duplicidad de la épica)._

- [ ] 2.1 Implementar la regla de elegibilidad (reintento / investigación / disputa) a partir del código de motivo y del estado de ejecución (fuente según OQ-32); verificar con pruebas por cada escenario del spec, incluido el estado incierto que nunca es elegible para reintento
- [ ] 2.2 Mostrar la ruta de atención en la vista de soporte; verificar con pruebas de interfaz/consulta que se muestra para pagos fallidos, expirados y disputados
- [ ] 2.3 Hacer que el reintento de soporte se rija por el contrato de `payment-idempotency` (definido en el cambio `payment-idempotency-protection`) y por lo decidido en OQ-02, sin redefinirlo; verificar con una prueba del escenario «Reintento de soporte sin duplicidad financiera» que no se genera más de un movimiento de fondos (agregado por análisis)
- [ ] 2.4 Rechazar el reintento de soporte si ya existe una transferencia ejecutada y dirigir el caso a investigación o disputa; verificar con una prueba del escenario "Reintento sobre pago ya ejecutado" (agregado por análisis)

## 3. Ruta de ayuda al usuario

_Cubre: criterio 3 de la HU._

- [ ] 3.1 Redactar en español los mensajes para falla técnica y para transferencia ya ejecutada, sin prometer cancelación unilateral; verificar con revisión de producto/legal
- [ ] 3.2 Implementar la selección de ruta de ayuda según el tipo de escenario; verificar con pruebas de ambos escenarios del spec

## 4. Registro de acciones de soporte

_Cubre: criterio 4 de la HU._

- [ ] 4.1 Implementar el registro append-only de acciones con referencia de transacción y estado de resolución; verificar con pruebas de registro de acción y de cambio de estado sin pérdida del historial
- [ ] 4.2 Documentar el modelo de registro y los estados de resolución; verificar que el documento enumera los estados y su relación con la referencia de transacción

## 5. Integración

_Cubre: verificación transversal de los criterios 1 a 4._

- [ ] 5.1 Verificar de extremo a extremo un flujo de falla técnica con reintento y uno de transferencia ejecutada derivada a investigación/disputa, comprobando códigos, ruta visible, mensaje al usuario y registros de soporte

## 6. Definiciones previas a habilitar rutas (agregado por análisis)

- [ ] 6.1 Obtener de producto y cumplimiento las categorías de disputa habilitadas en MVP (OQ-29); verificar que quedan registradas como configuración antes de habilitar la ruta de disputa
- [ ] 6.2 Obtener de soporte y operaciones los niveles de escalamiento y SLA por ruta (OQ-30) y los estados de resolución (OQ-33); verificar que quedan documentados
- [ ] 6.3 Acordar con operaciones la fuente que determina "transferencia ejecutada" e "incierto" (OQ-32) y con arquitectura la semántica del reintento (OQ-02); verificar que ambas decisiones quedan registradas antes de cerrar las tareas 2.1 y 2.3
