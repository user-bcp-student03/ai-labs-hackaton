# Constitución del MVP de wallet en Perú

Documento fundacional del desarrollo guiado por specs (SDD) para la wallet. Reúne la épica, que es la fuente de verdad del negocio, y los principios que toda historia, spec, diseño y tarea debe respetar. Cualquier artefacto OpenSpec de la wallet debe ser coherente con este documento; si no lo es, se corrige el artefacto o se enmienda este documento con aprobación explícita.

## 1. Épica: MVP de wallet en Perú para pagos cotidianos

### Resumen

Lanzar un MVP de wallet enfocado en Perú que reduzca la fricción en checkout y acelere el onboarding para comportamientos de pago frecuentes y de bajo monto. La épica prioriza velocidad de salida a mercado sin perder confianza del usuario, con confirmaciones claras, manejo confiable de estados y límites alineados a cumplimiento.

### Problema y oportunidad

La caída en checkout es alta y el onboarding es lento para personas que hacen transferencias pequeñas frecuentes y pagos con QR. La línea base local de pagos muestra una adopción fuerte de interoperabilidad y un comportamiento claro en flujos basados en alias, lo que abre una oportunidad para lanzar ahora una propuesta de wallet enfocada.

### Objetivos (un trimestre)

- Reducir la caída en checkout de 30% a 8%.
- Reducir el tiempo de finalización de onboarding de 8 minutos a 3 minutos.
- Mantener usuarios activos mensuales (MAU) entre 1,000 y 2,000 durante los primeros 3 meses posteriores al lanzamiento.
- Lograr un CAC de PEN 10 por usuario nuevo durante los primeros 3 meses posteriores al lanzamiento.

### Usuarios objetivo

- Usuarios de smartphone que hacen transferencias diarias de bajo monto: recorrido rápido y de baja fricción desde la intención hasta la confirmación.
- Pequeños comercios que cobran con QR: aceptación predecible, confirmación confiable y estabilidad operativa diaria.

### Alcance

**Incluye**
- Flujo de onboarding de wallet para el segmento MVP en Perú.
- Flujos núcleo de pago para transferencias de bajo monto y cobro a comercios con QR.
- Visibilidad de confirmación y estado de pago para usuarios y comercios.
- Instrumentación base del funnel de checkout, finalización de onboarding y activación al mes 3.

**Fuera de alcance**
- Despliegue multipaís amplio dentro de esta épica.
- Programas avanzados de lealtad o mecánicas de crecimiento no esenciales.
- Paridad funcional completa entre todos los proveedores/bancos externos desde el día uno.
- Exposición de APIs de pago abiertas y autoservicio para terceros.

### Métricas de éxito

- MVP de wallet lanzado dentro de un trimestre.
- Caída en checkout: de 30% a 8%.
- Tiempo de finalización de onboarding: de 8 a 3 minutos.
- MAU entre 1,000 y 2,000 en los meses 1-3 posteriores al lanzamiento.
- CAC de PEN 10 por usuario nuevo en los meses 1-3 posteriores al lanzamiento.

### Supuestos y restricciones

- El ecosistema es multirriel; el MVP no debe asumir un único riel de procesamiento de extremo a extremo.
- Las integraciones reales son contractuales y con habilitaciones operativas; el alta de proveedores no es autoservicio inmediato.
- Los límites por proveedor pueden estar por debajo del máximo regulatorio; el producto y los mensajes UX deben contemplarlo.
- El producto debe sostener la expectativa operativa de pagos inmediatos con alias (24x7x365).
- El rango de MAU y el objetivo de CAC son umbrales de negocio definidos por el Product Owner.

### Dependencias y riesgos

- Dependencia: los partners de adquirencia/gateway seleccionados para QR y procesamiento wallet son necesarios para preparar el lanzamiento.
- Riesgo: reintentos sin idempotencia robusta pueden generar duplicidad financiera y desvíos de conciliación.
- Riesgo: transiciones asíncronas del estado de pago pueden deteriorar la confianza si la confirmación no es clara.
- Riesgo: el manejo operativo/legal de reversos y disputas debe ser explícito, porque la cancelación unilateral de P2P no está garantizada de forma uniforme.

## 2. Principios de la constitución

Derivados de la épica y de los fundamentos de SDD. Cada principio indica su origen.

### Principios de proceso (SDD)

1. **La spec es la fuente de verdad.** Primero se define el comportamiento observable (spec), después el diseño y las tareas, y al final el código. El código no introduce comportamiento que no esté en una spec.
2. **Trazabilidad completa.** Toda spec referencia su historia y esta épica; todo diseño referencia su spec; toda tarea referencia su requisito. Cadena: épica → HU → proposal → spec → design → tasks → código y pruebas.
3. **Compuerta de revisión humana.** Una persona revisa y aprueba la spec antes de pasar a Architect, y el diseño antes de implementar.
4. **Lo ambiguo se explicita.** Distinguir requisito, restricción, supuesto y pregunta abierta. No se inventa lo no definido; se registra como pregunta abierta con responsable.
5. **Separar qué de cómo.** Las specs describen comportamiento observable y no eligen tecnología. La solución técnica es decisión de Architect.
6. **Metas de negocio fuera de los escenarios.** Las métricas (caída en checkout, tiempo de onboarding, MAU, CAC) se registran en el proposal y se verifican con instrumentación; los escenarios solo cubren comportamiento verificable.
7. **Cambios incrementales y reversibles.** Un cambio OpenSpec por capacidad, revisable de forma independiente.

### Principios de producto

8. **Confirmación clara y terminal.** Cada intento de pago termina en exactamente un resultado terminal (exitoso, fallido o expirado) que no cambia después. *Origen: riesgo de transiciones asíncronas.*
9. **Idempotencia obligatoria.** Reintentos, doble confirmación y reenvío de eventos no generan cobros, registros ni eventos duplicados. *Origen: riesgo de duplicidad financiera y conciliación.*
10. **Estados asíncronos explícitos.** El usuario ve un estado pendiente hasta que haya resultado terminal; una actualización tardía no sobrescribe un resultado terminal.
11. **Límites visibles antes del envío.** Los límites por proveedor o canal, que pueden estar por debajo del máximo regulatorio, se validan y se explican al usuario antes de enviar. *Origen: restricciones.*
12. **Sin acoplamiento a un único riel.** Las specs no asumen un proveedor ni un riel de procesamiento específico. *Origen: ecosistema multirriel.*
13. **Siguiente paso siempre claro.** Ante pendiente, fallo, expiración o rechazo, el usuario recibe la acción siguiente (reintentar, volver o esperar una decisión).
14. **Disponibilidad esperada 24x7x365** para los flujos de pago inmediatos; los fallos de proveedor se comunican sin crear cuentas ni cobros inconsistentes.
15. **Instrumentación desde el inicio.** Embudo de checkout, finalización de onboarding y evento de activación para MAU quedan medidos desde el MVP.

### Principios de seguridad y calidad

16. **Datos ficticios en el MVP.** Solo documentos de prueba (`TEST`, prefijo `TEST-`); no se usan datos reales ni secretos reales.
17. **Autorización ligada a la identidad**, validación de entradas, límites de tamaño y de tasa, y logs sin datos sensibles.
18. **Contratos existentes protegidos.** No se modifican `POST /auth/login`, `GET/POST /api/tasks`, `GET /api/summary` ni `POST /api/requirements` sin decisión explícita.
19. **Calidad verificable.** Cobertura de 85% o más en el código modificado, pruebas de caracterización antes de refactorizar, y sin silenciar alertas de seguridad ni reducir quality gates.
20. **Operaciones y cumplimiento.** Los estados de pago deben poder monitorearse y conciliarse; reversos y disputas se tratan como decisión explícita, no como detalle.

## 3. Trazabilidad de la épica

### Historias candidatas y su cobertura

| Historia candidata | Cambio OpenSpec | Estado |
|---|---|---|
| Onboarding rápido con siguiente paso claro | [wallet-onboarding-kyc](../openspec/changes/wallet-onboarding-kyc/proposal.md) | Spec creada |
| Pago de bajo monto con confirmación clara | [wallet-payment-confirmation](../openspec/changes/wallet-payment-confirmation/proposal.md) | Spec creada |
| Comercio cobra con QR y valida el estado | Por definir | Sin spec |
| Operaciones/compliance monitorea y concilia | Por definir | Sin spec |

### Objetivos de la épica y dónde se atienden

| Objetivo | Cobertura |
|---|---|
| Caída en checkout de 30% a 8% | `wallet-payment-confirmation` (proposal) |
| Onboarding de 8 a 3 minutos | `wallet-onboarding-kyc`: pendiente de añadir al proposal como métrica |
| MAU de 1,000 a 2,000 | `wallet-payment-confirmation`: evento de activación |
| CAC de PEN 10 | Fuera de las specs actuales; requiere definición del Product Owner |

## 4. Enmiendas

Cambios a este documento requieren aprobación de una persona y se registran en el control de versiones.
