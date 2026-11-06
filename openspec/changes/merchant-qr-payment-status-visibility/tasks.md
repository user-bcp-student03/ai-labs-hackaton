# Tareas

Nota: el repositorio es greenfield (sin código de aplicación). Las rutas y tecnologías concretas se definen al implementar; estas tareas no asumen archivos existentes. Las preguntas abiertas (OQ-24 conjunto de estados MVP, OQ-25 canal app/web, OQ-26 proveedores, OQ-27 historial, OQ-28 plazo de reflejo, OQ-08 creación del intento QR) siguen pendientes: las tareas que dependen de ellas lo indican y deben usar valores configurables. Registro: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

## 1. Modelo de transacción y estados

_Cubre: criterios 1 y 2 de la HU._

- [ ] 1.1 Definir el modelo de intento de pago QR con referencia única de transacción y pertenencia a un comercio (la creación del intento depende de OQ-08); verificar con pruebas que dos intentos nunca comparten referencia y que cada intento queda asociado a un solo comercio.
- [ ] 1.2 Implementar el mapeo configurable entre estados/eventos del proveedor y el conjunto de estados MVP (valores pendientes de OQ-24, no fijados aquí); verificar con pruebas que un estado no mapeado no se muestra tal cual y queda registrado para revisión.
- [ ] 1.3 Documentar el modelo y el mapeo de estados, marcando el conjunto MVP como pendiente de definición (OQ-24); verificar que el documento enlaza la HU y la épica.

## 2. Procesamiento de eventos del proveedor

_Cubre: criterio 3 de la HU; las tareas 2.1, 2.3 y 2.4 son agregadas por análisis (riesgos de terceros y confiabilidad de la épica)._

- [ ] 2.1 Implementar la recepción de callbacks/eventos del proveedor con validación de origen (método según proveedor, por definir en OQ-26); verificar con pruebas que un evento no autenticado se rechaza (agregado por análisis).
- [ ] 2.2 Persistir el historial de eventos append-only y derivar el estado actual; verificar con pruebas que un evento válido cambia el estado visible de la transacción.
- [ ] 2.3 Aplicar deduplicación y tolerancia a desorden de eventos; verificar con pruebas los escenarios de evento duplicado y evento fuera de orden de la spec (agregado por análisis).
- [ ] 2.4 Manejar eventos con referencia desconocida; verificar con pruebas que no se crea un intento visible y que el caso queda registrado (agregado por análisis).

## 3. Consulta del comercio

_Cubre: criterios 1, 3 y 4 de la HU; el aislamiento entre comercios (3.1) es agregado por análisis._

- [ ] 3.1 Implementar la consulta de intentos con referencia y estado actual, restringida al comercio autenticado; verificar con pruebas el escenario de aislamiento entre comercios.
- [ ] 3.2 Implementar filtros por fecha y por referencia (individuales y combinados) con respuesta de "sin resultados"; verificar con pruebas los escenarios de filtro de la spec.
- [ ] 3.3 Implementar la actualización de la vista tras aplicar un evento, con el mecanismo adaptado al canal que se defina (OQ-25); verificar que un cambio de estado por callback se refleja en la vista del comercio dentro del plazo máximo configurado (OQ-28, escenario «Plazo de reflejo en la vista»).
- [ ] 3.4 Documentar el uso de la consulta y filtros para el comercio; verificar que el documento describe los escenarios de la spec.

## 4. Integración

- [ ] 4.1 Ejecutar un flujo de extremo a extremo con un proveedor simulado (creación del intento, eventos de cambio de estado, duplicados y filtros) y verificar que el resultado coincide con todos los escenarios de `merchant-qr-payment-status`.
- [ ] 4.2 Ejecutar `openspec validate merchant-qr-payment-status-visibility` y verificar que no reporta errores.

## 5. Seguimiento de definiciones pendientes (agregado por análisis)

- [ ] 5.1 Resolver OQ-24 (conjunto mínimo de estados y relación con los estados del pagador) y OQ-25 (canal) antes de fijar textos y mecanismo de refresco; verificar que ambas quedan registradas en `docs/OPEN-QUESTIONS.md` con estado distinto de "Abierta"
- [ ] 5.2 Confirmar OQ-26 (proveedores y garantías de callbacks), OQ-27 (historial) y OQ-28 (plazo de reflejo) y OQ-08 (creación del intento QR); verificar que cada una queda registrada
- [ ] 5.3 Archivar el cambio tras cumplir los requisitos de revisión del proyecto
