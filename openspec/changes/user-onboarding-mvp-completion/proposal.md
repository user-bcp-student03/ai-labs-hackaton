# Proposal

## Why

El onboarding actual es lento (mediana de 8 minutos) y es una de las fuentes de abandono antes del primer pago. La épica busca bajar esa mediana a 3 minutos dentro del trimestre posterior al lanzamiento, y necesita además la instrumentación de adquisición/activación para verificar MAU (1,000–2,000) y CAC (PEN 10 por usuario nuevo) en los meses 1-3.

## Fuentes

- Historia de usuario: [Registro y activación del MVP de wallet](../../../docs/stories/user-onboarding-mvp-completion.sp.md)
- Épica: [MVP de wallet en Perú](../../../docs/epic/peru-wallet-mvp.sp.md)

## What Changes

- Decisión OQ-19 (2026-11-06): se construye únicamente un **motor de pasos configurable**. Los pasos, su orden, los datos requeridos, las reglas de validación y los mensajes provienen de configuración; los pasos reales de KYC/documentación los define Cumplimiento más adelante, sin cambiar el motor.
- Flujo de onboarding guiado, gobernado por esa configuración, que muestra la secuencia de pasos requeridos y el paso actual en todo momento.
- Validación por paso: si falta información obligatoria o hay datos inválidos (según la configuración), se bloquea el avance y se muestra un mensaje accionable.
- Contrato de configuración de pasos (estructura de la definición de pasos y reglas) entregado como parte del cambio, con una configuración de **ejemplo no aprobado** solo para demostración y pruebas.
- Al finalizar correctamente el onboarding, el estado de la wallet pasa a `activo` y el usuario accede al punto de entrada de pagos de bajo monto.
- Eventos de analítica: inicio de onboarding, finalización de cada paso y cierre del flujo.
- Salida analítica de onboarding con conteos mensuales de nuevos usuarios activos y la atribución de gasto de adquisición necesaria para verificar MAU y CAC.
- Instrumentación necesaria para medir la mediana de duración de onboarding (8 → 3 minutos) en la cohorte MVP Perú, con un reporte periódico de esa mediana.

## Alcance

### Dentro de alcance

- Flujo de onboarding de la wallet para la cohorte MVP Perú, desde el inicio hasta el cierre del flujo.
- Motor de pasos configurable: definición de pasos, paso actual visible, validación bloqueante con mensaje accionable y progreso, todo a partir de configuración.
- Contrato de configuración de pasos y una configuración de ejemplo (etiquetada «ejemplo no aprobado», no es un requisito regulatorio) para demostración y pruebas.
- Indicador de pasos y paso actual; validación y bloqueo de avance con mensajes accionables.
- Transición del estado de la wallet a `activo` y acceso al punto de entrada de pagos de bajo monto.
- Eventos de inicio, de finalización de cada paso y de cierre del flujo.
- Salida analítica de onboarding (conteos mensuales de nuevos usuarios activos y atribución de gasto de adquisición).

### Fuera de alcance

- Requisitos reales de KYC y documentación (pasos, datos obligatorios y reglas): los define Cumplimiento más adelante y se cargan como configuración sin cambiar el motor. Este cambio no los inventa; cualquier paso usado en demos o pruebas es «ejemplo no aprobado» y no se presenta como requisito regulatorio.
- Definición oficial de la frontera de eventos que determina la duración de onboarding (pregunta abierta; no se responde en este cambio).
- Flujo de pago de bajo monto, resultado terminal y evento de activación del pagador por transacción exitosa (cambio `payer-low-value-payment-confirmation`).
- Cobro a comercios con QR (`merchant-qr-payment-status-visibility`), manejo de fallos y reversos (`payment-failure-reversal-handling`) y conciliación (`ops-transaction-reconciliation`).
- Cálculo/reporte consolidado de MAU y CAC y la captura del gasto de adquisición en sí; este cambio solo expone los datos de salida necesarios (responsable del reporte consolidado: OQ-07).
- Despliegue multipaís, programas de lealtad, paridad completa entre proveedores/bancos y APIs abiertas de pago (fuera de alcance de la épica).

## Capabilities

### New Capabilities

- `user-onboarding-mvp-completion`: onboarding guiado de la wallet con indicador de pasos, validación bloqueante, activación del estado de la wallet, eventos de analítica y salida analítica para MAU/CAC.

### Modified Capabilities

Ninguna. No existen specs previas en `openspec/specs/`.

## Impact

- El repositorio es greenfield: no hay código de aplicación, por lo que no se referencian archivos ni módulos existentes. El impacto se describe en `design.md` a nivel de componentes lógicos.
- Sistemas afectados (lógicos): flujo/pantallas de onboarding, servicio de registro y estado de wallet, instrumentación de eventos de analítica, salida analítica de onboarding.
- Dependencias: definición real de KYC/documentación por Cumplimiento (dependencia externa para la configuración de producción; no bloquea el motor); fuente del gasto de adquisición (por confirmar); acuerdo sobre la frontera de eventos de duración.
- Relación con el cambio `payer-low-value-payment-confirmation`: ambos usan el término "activación" con significados distintos; ver `design.md` y [GLOSSARY.md](../../../docs/GLOSSARY.md).

## Supuestos y preguntas abiertas

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). Salvo OQ-19, no se responden en este cambio.

- OQ-19: **Decidida (2026-11-06)** — opción elegida: motor de pasos configurable. Se construye solo el motor; los pasos reales de KYC/documentación y sus datos requeridos los define Cumplimiento después, sin cambiar el motor. El contenido real de KYC sigue **pendiente de Cumplimiento como dependencia** (ya no es una pregunta abierta de diseño). Los pasos de ejemplo son «ejemplo no aprobado».
- OQ-20: abierta. Frontera de eventos analíticos que define la duración de onboarding. Valor provisional (propuesta, no aprobada): inicio = evento de inicio; fin = cierre por finalización exitosa.
- OQ-21: abierta. Qué casos emiten el evento de «cierre del flujo» y cómo se determina el abandono. Valor provisional (propuesta, no aprobada): cierre solo por finalización exitosa y abandono medido por inactividad configurable.
- OQ-22: abierta. Fuente y momento de captura del gasto de adquisición y definición de «usuario nuevo» para CAC. Sin valor provisional; bloquea la tarea 6.2.
- OQ-23: abierta. Nombres de los estados de wallet distintos de `activo`. Valor provisional (propuesta, no aprobada): `pendiente`.
- OQ-05: abierta. Qué evento alimenta oficialmente el MAU (estado de wallet `activo` vs evento de activación del pagador). Valor provisional (propuesta, no aprobada): MAU = pagadores distintos con al menos un evento de activación en el mes.
- OQ-06: abierta. Criterio de pertenencia a la cohorte MVP Perú. Valor provisional (propuesta, no aprobada): asignarla al inicio del onboarding, con atributo de cohorte configurable.
- OQ-07: abierta. Responsable del reporte consolidado de MAU y CAC. Sin valor provisional; no bloquea el desarrollo, bloquea la verificación de los objetivos de la épica.

## Dependencias entre cambios

| Relación | Cambio | Detalle |
|---|---|---|
| Depende de | ninguno | Es el punto de entrada del recorrido del usuario; sus únicas dependencias son definiciones externas (configuración real de KYC por Cumplimiento, fuente de gasto de adquisición). |
| Es consumido por | `payer-low-value-payment-confirmation` | Precondición: solo una wallet `activo` accede al punto de entrada de pagos de bajo monto. |
| Comparte término con | `payer-low-value-payment-confirmation` | «Activación» con dos significados distintos; no se fusionan (OQ-05). |

## Agregado por análisis

Elementos que no provienen de un criterio de aceptación de la HU y se conservan etiquetados:

- Escenarios de configuración de pasos (pasos y validaciones provenientes de configuración; cambiar la configuración cambia los pasos sin cambiar el comportamiento) y la etiqueta «ejemplo no aprobado»: derivan de la decisión OQ-19 (2026-11-06), no de un criterio de la HU.
- Escenario «Eventos sin duplicados» (deduplicación de eventos por reintentos del cliente; protege los criterios 4 y 5).
- Escenario «Mes sin gasto de adquisición disponible» (evita que un dato faltante se lea como gasto cero; protege el criterio 6).
- Escenarios de reporte de duración y de campos de la salida mensual, que expresan los criterios 5 y 6 como salida medible (no agregan comportamiento nuevo).
