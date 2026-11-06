# Wallet MVP Perú: alcance del trabajo (onboarding y pago de bajo monto)

Épica: [MVP de wallet en Perú](./epic/peru-wallet-mvp.sp.md).

## 1. Parte del wallet que trabajaremos

Se trabajan dos historias del mismo usuario: el que transfiere a diario montos bajos. Cubren el recorrido completo, desde registrarse hasta pagar y recibir la confirmación.

| Historia | Usuario | Parte del wallet |
|---|---|---|
| [Registro y activación del MVP de wallet](./user-stories/user-onboarding-mvp-completion.sp.md) | Usuario con transferencias diarias de bajo monto | Onboarding y activación, con instrumentación analítica |
| [Confirmación de pagos de bajo monto](./user-stories/payer-low-value-payment-confirmation.sp.md) | Pagador | Transferencia de bajo monto y resultado final del pago |

Objetivos de la épica a los que contribuyen:

- Onboarding: bajar el tiempo de finalización de 8 a 3 minutos.
- Pago: bajar la caída en checkout de 30% a 8%.
- Ambas: MAU entre 1,000 y 2,000 en los meses 1-3.
- Onboarding: CAC de PEN 10 por usuario nuevo en los meses 1-3.

## 2. Funciones incluidas

### Onboarding y activación
1. Flujo guiado que muestra la secuencia de pasos y el paso actual.
2. Validación que bloquea el avance ante datos faltantes o inválidos, con mensaje accionable.
3. Cambio del estado de la wallet a activo al terminar, con acceso al pago de bajo monto.
4. Registro de eventos: inicio de onboarding, finalización de cada paso y cierre del flujo.
5. Medición de la mediana de tiempo de onboarding (objetivo: 3 minutos en el trimestre posterior al lanzamiento).
6. Salida analítica mensual de nuevos usuarios activos y atribución de gasto de adquisición, para verificar MAU y CAC.

### Confirmación de pagos de bajo monto
1. Pantalla previa a la confirmación con la identidad del destino y el monto.
2. Validación del monto visible al usuario antes del envío, según el límite del proveedor.
3. Un único resultado terminal por intento: exitoso, fallido o expirado.
4. Referencia de transacción en los pagos exitosos, guardada en el historial.
5. Siguiente acción clara (reintentar o volver) ante fallo o expiración, sin cobros duplicados.
6. Medición de la caída en checkout de este flujo (objetivo: de 30% a 8% en el trimestre posterior al lanzamiento).
7. Evento de activación en cada pago exitoso, para el cálculo de MAU.

### Punto de unión entre ambas historias
- El onboarding termina dando acceso al pago de bajo monto, y el pago exitoso emite el evento de activación que alimenta el MAU.

## 3. Límites del alcance

### Fuera de alcance
- Cobro a comercios con QR y visibilidad del estado para comercios.
- Monitoreo y conciliación para operaciones y compliance.
- Reversos y disputas.
- Despliegue multipaís, programas de lealtad o crecimiento, paridad completa entre proveedores y APIs abiertas (exclusiones de la épica).

### Restricciones heredadas de la épica
- No asumir un único riel de procesamiento de extremo a extremo.
- Las integraciones con proveedores son contractuales, no de autoservicio inmediato.
- Los límites por proveedor pueden ser menores al máximo regulatorio, y la UX debe contemplarlo.
- Se espera continuidad operativa de pagos inmediatos (24x7x365).
- La confirmación debe contemplar transiciones asíncronas del estado de pago.

## 4. Supuestos y preguntas abiertas

Supuestos:
- Los requisitos de KYC y documentación se definen con cumplimiento y producto antes de implementar.
- Los umbrales de MAU y CAC los definió el Product Owner.
- Las etiquetas de los estados terminales visibles al usuario se definen con producto.

Preguntas abiertas:
- ¿Qué eventos analíticos marcan el inicio y el fin de la duración del onboarding?
- ¿Qué regla inicial de monto bajo se configurará por proveedor y canal en el lanzamiento?

## 5. Dependencias y riesgos relevantes

- Riesgo: los reintentos sin idempotencia robusta pueden generar cobros duplicados y desvíos de conciliación. Afecta al criterio de no duplicar cobros.
- Riesgo: las transiciones asíncronas del estado de pago pueden deteriorar la confianza si la confirmación no es clara.
- Dependencia: los partners de pago y procesamiento wallet deben estar habilitados para el lanzamiento.

## 6. Planificación por sprint

El trabajo se reparte en 2 sprints, una historia por sprint.

| Sprint | Prioridad | Historia | Objetivo del sprint |
|---|---|---|---|
| Sprint 1 | Prioridad 1 | [Registro y activación del MVP de wallet](./user-stories/user-onboarding-mvp-completion.sp.md) | El usuario completa el onboarding y su wallet queda activa, con los eventos de analítica emitidos |
| Sprint 2 | Prioridad 2 | [Confirmación de pagos de bajo monto](./user-stories/payer-low-value-payment-confirmation.sp.md) | El pagador completa una transferencia de bajo monto y recibe un resultado terminal único |

Lo del sprint 1 se atiende primero. Lo del sprint 2 es de segunda prioridad.

### Sprint 1: onboarding (prioridad 1)
- Criterios CA1 a CA4: flujo guiado, validación con mensajes accionables, wallet activa y registro de eventos.
- CA6 (reporte de MAU y CAC): se construye la salida analítica de nuevos usuarios activos y la atribución del gasto de adquisición.
- Las tareas por rol están en [tareas-onboarding.md](./tareas-onboarding.md).

### Sprint 2: confirmación de pago (prioridad 2)
- Criterios CA1 a CA4: destino y monto antes de confirmar, resultado terminal único, referencia en el historial y siguiente acción sin cobros duplicados.
- CA6 del pago: el evento de activación en cada pago exitoso, que completa el cálculo de MAU.
- Validación del monto según el límite del proveedor antes del envío.

### Metas que se verifican después del lanzamiento
- Tiempo mediano de onboarding de 8 a 3 minutos (CA5 del onboarding).
- Caída en checkout de 30% a 8% (CA5 del pago).
- MAU entre 1,000 y 2,000 y CAC de PEN 10 en los meses 1-3.

Estas metas dependen de la operación real de la cohorte MVP en Perú. Los sprints entregan el producto y la medición, no el resultado.

### Dependencias entre sprints
- El onboarding da acceso al punto de entrada de pagos de bajo monto. Al cerrar el sprint 1 todavía no existe el flujo de pago, así que ese acceso debe quedar definido y probado como punto de entrada, sin pago funcional hasta el sprint 2.
- El MAU solo se puede calcular completo al cerrar el sprint 2, porque su evento de activación sale del pago exitoso.
- Las preguntas abiertas de la sección 4 deben resolverse antes del sprint en que afectan: los eventos de onboarding antes del sprint 1 y la regla de monto bajo antes del sprint 2.
- La idempotencia de reintentos (sección 5) debe diseñarse antes de construir el flujo de pago, en el sprint 2.
