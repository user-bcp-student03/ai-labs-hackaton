# Design

## Context

- El repositorio es **greenfield**: no existe código de aplicación, stack definido ni specs previas en `openspec/specs/`. Este diseño describe componentes lógicos; no se referencian archivos existentes.
- Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/user-onboarding-mvp-completion/spec.md`.
- Fuentes: [historia](../../../docs/stories/user-onboarding-mvp-completion.sp.md) y [épica](../../../docs/epic/peru-wallet-mvp.sp.md). La épica fija la meta de duración de onboarding (8 → 3 minutos) y los umbrales de MAU (1,000–2,000) y CAC (PEN 10) en los meses 1-3.
- Existe un cambio hermano, `payer-low-value-payment-confirmation`, que también usa el término "activación" (ver Decisión 1) y que depende de este cambio como precondición de acceso (wallet `activo`). Terminología: [GLOSSARY.md](../../../docs/GLOSSARY.md). Preguntas abiertas: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

## Goals / Non-Goals

**Goals:**

- Un motor de pasos configurable (decisión OQ-19, 2026-11-06): pasos, orden, datos requeridos, reglas y mensajes provienen de configuración, con validación que bloquea el avance y mensajes accionables.
- Una transición única, consistente y verificable del estado de la wallet a `activo`.
- Eventos de analítica confiables (sin duplicados) con marcas de tiempo, de modo que la frontera de duración pueda definirse después sin cambiar la instrumentación.
- Una salida analítica que habilite verificar MAU y CAC sin que este cambio calcule esas métricas.

**Non-Goals:**

- Definir los requisitos reales de KYC/documentación ni los campos concretos de cada paso: los define Cumplimiento después y se cargan como configuración. Los pasos de ejemplo son «ejemplo no aprobado» y no se presentan como requisitos regulatorios.
- Elegir tecnología, proveedor de identidad o herramienta de analítica.
- Calcular o reportar MAU/CAC, o capturar el gasto de adquisición en sí.
- Modificar el cambio hermano `payer-low-value-payment-confirmation`.

## Decisions

1. **"Activación" tiene dos significados distintos; no se fusionan.**
   - Este cambio: **estado de la wallet `activo`**, un hecho de ciclo de vida de la cuenta que ocurre una vez, al finalizar correctamente el onboarding.
   - Cambio `payer-low-value-payment-confirmation`: **evento de activación del pagador**, emitido por cada transacción exitosa (una vez por transacción) para el cálculo de MAU.
   - Son hechos independientes: una wallet `activo` puede no haber emitido aún ningún evento de activación del pagador (aún no pagó), y el evento de activación no cambia el estado de la wallet. Este cambio **no** emite el evento de activación del pagador y el otro cambio **no** cambia el estado de la wallet.
   - Para evitar ambigüedad, este diseño usa "wallet activa / estado `activo`" para este hecho y "evento de activación del pagador" para el otro. Si ambos cambios se aplican, los nombres de eventos y atributos deben ser distintos.
   - *Alternativa:* tratarlos como un solo concepto (por ejemplo, que el estado `activo` se derive de la primera transacción exitosa); descartada porque contradice el criterio 3 de la HU (el estado cambia al finalizar el onboarding) y acoplaría ambos flujos. Qué evento alimenta oficialmente el MAU es la pregunta abierta OQ-05.
2. **Motor de pasos configurable (decisión OQ-19, 2026-11-06).** La lista de pasos requeridos, su orden, los datos requeridos, las reglas de validación y los mensajes accionables se definen por configuración, no fijados en el flujo. Cambiar la configuración cambia los pasos sin cambiar el comportamiento del motor (paso actual, bloqueo, progreso, eventos y transición a `activo`).
   - **Contrato de configuración:** cada paso declara identificador, orden, datos requeridos, reglas de validez y mensaje accionable por regla; el motor solo interpreta esa estructura y no conoce pasos concretos. El contrato es un entregable de este cambio (tarea 1.7).
   - **Configuración de ejemplo:** para demostración y pruebas se usa una configuración etiquetada «ejemplo no aprobado»; no representa requisitos de KYC ni regulatorios y no se inventan requisitos.
   - **Pendiente de Cumplimiento (dependencia, no pregunta de diseño):** los pasos y datos reales de KYC/documentación se cargarán como configuración cuando Cumplimiento los defina, sin cambiar el motor.
   - *Alternativa:* pasos codificados de forma fija; descartada porque los requisitos de KYC no existen y deben poder cambiar sin rediseñar.
3. **Validación bloqueante por paso.** Cada paso valida sus datos antes de permitir el avance; los errores se asocian al dato concreto y se presentan con el texto de corrección (contenido externalizado). El paso actual no cambia mientras haya errores.
4. **Estado de la wallet.** Estados mínimos relevantes para este cambio: un estado previo a la activación (nombre por definir, OQ-23) y `activo`. La transición a `activo` solo ocurre en el cierre exitoso del flujo, es idempotente (repetir el cierre no genera efectos adicionales) y se aplica de forma coherente con el registro del evento de cierre. *Alternativa:* activar al completar cada paso; descartada por el criterio 3.
5. **Eventos de onboarding.** Eventos de inicio, de finalización de cada paso (con identificador de paso) y de cierre del flujo, todos con marca de tiempo, identificador de onboarding/usuario y atributo de cohorte MVP Perú, deduplicados por (onboarding, tipo, paso). Se registran todas las marcas necesarias para que la frontera de duración (OQ-20) se elija después en la capa analítica; el alcance del evento de cierre (éxito vs abandono) está en OQ-21. *Alternativa:* calcular la duración en el cliente; descartada por ser menos confiable y no auditable.
6. **Salida analítica.** Se expone una salida mensual con conteo de nuevos usuarios con wallet `activo`, la atribución de gasto de adquisición por usuario/cohorte (en PEN) y los parámetros de referencia de MAU, CAC y duración. Además se entrega un reporte mensual de mediana de duración de onboarding. La fuente del gasto de adquisición y la definición de "usuario nuevo activo" frente a MAU se asumen por acordar (OQ-22, OQ-05); el reporte consolidado de MAU y CAC no es parte de este cambio (OQ-07).

## Risks / Trade-offs

- [Confusión entre "wallet activa" y "evento de activación del pagador" en analítica y MAU] → Nombres distintos, glosario acordado y documentación en este diseño; ver pregunta abierta.
- [Frontera de duración definida tarde puede exigir datos no registrados] → Registrar marcas de tiempo de inicio, de cada paso y de cierre; cualquier frontera razonable se puede calcular con ellas.
- [Requisitos de KYC pueden añadir pasos y alargar el onboarding frente a la meta de 3 minutos] → Pasos configurables y medición por paso para identificar cuellos de botella.
- [Que los pasos de ejemplo se lean como requisitos regulatorios] → Etiquetarlos «ejemplo no aprobado» en configuración, pruebas y documentación; los pasos reales los define Cumplimiento.
- [Eventos duplicados por reintentos del cliente distorsionan duración y conteos] → Deduplicación por onboarding, tipo y paso.
- [Atribución de gasto de adquisición sin fuente definida impide verificar CAC] → Tratarla como dependencia por confirmar con producto/marketing antes de implementar.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). Salvo OQ-19, no se responden aquí.

- OQ-19: **Decidida (2026-11-06)** — opción elegida: motor de pasos configurable. El contenido real de KYC/documentación sigue pendiente de Cumplimiento como dependencia (no es una pregunta abierta de diseño); no cambia el motor.
- OQ-20: abierta. ¿Qué frontera de eventos analíticos define oficialmente la duración de onboarding (timestamp de inicio/fin)? Valor provisional (propuesta, no aprobada): inicio = evento de inicio; fin = cierre por finalización exitosa.
- OQ-05: abierta. **Glosario de "activación":** ¿qué término(s) oficial(es) distinguen el estado de wallet `activo` (este cambio) del evento de activación del pagador (`payer-low-value-payment-confirmation`), y cuál de ellos alimenta el MAU? Debe resolverse entre producto y analítica. Glosario de trabajo: [GLOSSARY.md](../../../docs/GLOSSARY.md). Valor provisional (propuesta, no aprobada): MAU = pagadores distintos con al menos un evento de activación en el mes.
- OQ-21: abierta. Alcance del evento de cierre del flujo y criterio de abandono. Valor provisional (propuesta, no aprobada): cierre solo por finalización exitosa y abandono por inactividad configurable.
- OQ-22: abierta. Fuente y momento de captura del gasto de adquisición; definición de "usuario nuevo" para CAC. Sin valor provisional; bloquea la tarea 6.2.
- OQ-23: abierta. Nombres de los estados de wallet distintos de `activo`. Valor provisional (propuesta, no aprobada): `pendiente`.
- OQ-06: abierta. Criterio de pertenencia a la cohorte MVP Perú. Valor provisional (propuesta, no aprobada): asignarla al inicio del onboarding, con atributo configurable.
- OQ-07: abierta. Responsable del reporte consolidado de MAU y CAC. Sin valor provisional; no bloquea el desarrollo.

Supuestos (de la HU y la épica, sin resolver):

- Los requisitos reales de KYC y documentación los define Cumplimiento (dependencia externa tras la decisión OQ-19); este cambio **no** los inventa y solo entrega el motor configurable.
- El rango objetivo de MAU (1,000–2,000) y el objetivo de CAC (PEN 10) fueron definidos por el Product Owner.
- La fuente y el momento de captura del gasto de adquisición no están definidos en las fuentes; se asumen por acordar (OQ-22).
- Los nombres de los estados de la wallet distintos de `activo` no están definidos; se asumen por acordar con producto (OQ-23).
