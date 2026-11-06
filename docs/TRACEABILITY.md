# Trazabilidad — épica → historia → criterio → requisito → tareas → preguntas abiertas

Matriz de cobertura del MVP de wallet en Perú. Fuentes aprobadas e inmutables: [épica](epic/peru-wallet-mvp.sp.md) y [historias](stories/). Los cambios OpenSpec están en [`openspec/changes/`](../openspec/changes/). Términos: [GLOSSARY.md](GLOSSARY.md). Preguntas: [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md).

> Gate: esta definición debe ser **revisada por una persona** antes de entregarla a Arquitectura. Las preguntas que **bloquean** (ver registro) deben tener respuesta o decisión explícita antes de iniciar el desarrollo del grupo de tareas afectado.

Abreviaturas de cambios: **IDEM** = [`payment-idempotency-protection`](../openspec/changes/payment-idempotency-protection/), **PAYER** = [`payer-low-value-payment-confirmation`](../openspec/changes/payer-low-value-payment-confirmation/), **FAIL** = [`payment-failure-reversal-handling`](../openspec/changes/payment-failure-reversal-handling/), **MERCH** = [`merchant-qr-payment-status-visibility`](../openspec/changes/merchant-qr-payment-status-visibility/), **RECON** = [`ops-transaction-reconciliation`](../openspec/changes/ops-transaction-reconciliation/), **ONB** = [`user-onboarding-mvp-completion`](../openspec/changes/user-onboarding-mvp-completion/). «Tareas» se refiere al grupo de `tasks.md` del cambio (p. ej., «2.1-2.3» = tareas 2.1 a 2.3).

## Alcance priorizado

La definición se prioriza en **dos fases**. Conteos recalculados contra los `tasks.md` y las specs vigentes de cada cambio (no son estimaciones).

| Fase | Cambio | Criterios de HU | Requisitos | Tareas |
|---|---|---|---|---|
| 1 | IDEM | 4 | 5 | 17 |
| 1 | ONB | 6 | 6 | 20 |
| 1 | PAYER | 6 | 9 | 27 |
| | **Subtotal Fase 1** | **16** | **20** | **64** |
| 2 (no priorizada) | MERCH | 4 | 4 | 16 |
| 2 (no priorizada) | FAIL | 4 | 5 | 15 |
| 2 (no priorizada) | RECON | 4 | 6 | 25 |
| | **Subtotal Fase 2** | **12** | **15** | **56** |
| | **Total** | **28** | **35** | **120** |

- **Fase 1 = 64 tareas** (IDEM 17 + ONB 20 + PAYER 27); de ellas, 17 son tareas de definiciones pendientes (grupo 1 de cada cambio: IDEM 4, ONB 7, PAYER 6). La cifra de «60 tareas» usada antes ya no es válida: IDEM sumó la 2.5, ONB la 1.7 y PAYER las 5.4 y 5.5.
- **Fase 2** (MERCH, FAIL, RECON) conserva sus artefactos, pero **no se prioriza**: sus preguntas no se reevalúan y deben reconciliarse con las decisiones del 2026-11-06 antes de priorizarlas (ver [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md), sección 0.1).
- Decisiones del 2026-11-06 que cambiaron el alcance: OQ-01 (híbrida), OQ-02 (nuevo intento vinculado), OQ-03 (verificación del intento previo que bloquea), OQ-14 (diferir) y OQ-19 (motor de pasos configurable).

## 1. Objetivos de la épica → historias

| Objetivo / riesgo de la épica | Historia(s) | Cambio(s) | Cómo se hace medible (instrumentación / reporte, no promesa) |
|---|---|---|---|
| O1. Caída en checkout de 30% a 8% | [Confirmación de pagos de bajo monto](stories/payer-low-value-payment-confirmation.sp.md) | PAYER | Eventos de funnel y reporte de conteos y tasa con línea base 30% y objetivo 8% como parámetros. Pendiente: fórmula (OQ-18), cohorte (OQ-06). |
| O2. Onboarding de 8 a 3 minutos | [Registro y activación](stories/user-onboarding-mvp-completion.sp.md) | ONB | Eventos con marca de tiempo y reporte mensual de mediana con base 8 y objetivo 3 como parámetros. Pendiente: frontera (OQ-20), cierre (OQ-21). |
| O3. MAU entre 1,000 y 2,000 (meses 1-3) | Confirmación de pagos; Registro y activación | PAYER, ONB | Evento de activación del pagador (conteo mensual de pagadores distintos) y conteo mensual de nuevos usuarios activos, con rango como parámetro. Pendiente: definición de MAU (OQ-05) y responsable del reporte (OQ-07). |
| O4. CAC de PEN 10 (meses 1-3) | Registro y activación | ONB | Salida mensual con gasto de adquisición atribuido en PEN y conteo de nuevos usuarios, con PEN 10 como parámetro. Pendiente: fuente (OQ-22) y responsable del reporte (OQ-07). |
| O5. MVP lanzado en un trimestre | Todas | Todos | Sin criterio de aceptación en las historias; es un objetivo de planificación (ver orden en la sección 5). |
| Riesgo: duplicidad por reintentos | [Idempotencia en pagos](stories/payment-idempotency-protection.sp.md) | IDEM (consumido por PAYER, FAIL, RECON) | Escenarios de resultado original, auditoría y marcado original/duplicado. Decididas el 2026-11-06: OQ-01, OQ-02 y OQ-14; PAYER añade la verificación del intento previo (OQ-03, decidida) cuyos supuestos se confirman en OQ-38 a OQ-40. |
| Riesgo: estados asíncronos poco claros | Confirmación de pagos; [Visibilidad QR](stories/merchant-qr-payment-status-visibility.sp.md) | PAYER (Fase 1), MERCH (Fase 2, no priorizada) | Resultado terminal único; estados del comercio; plazo de reflejo (OQ-28). Pendiente: OQ-24. |
| Riesgo: reversos y disputas sin regla uniforme | [Fallas y reversos](stories/payment-failure-reversal-handling.sp.md) | FAIL (Fase 2, no priorizada) | Códigos de motivo, ruta de atención y registro de acciones. Pendiente: OQ-29, OQ-30. |
| Alcance: monitoreo y conciliación | [Conciliación operativa](stories/ops-transaction-reconciliation.sp.md) | RECON (Fase 2, no priorizada) | Reporte y resumen diario. Pendiente: OQ-34 a OQ-37. |

## 2. Matriz criterio → requisito → tareas → preguntas

### 2.1 IDEM (Fase 1) — [Idempotencia en pagos](stories/payment-idempotency-protection.sp.md)

| Criterio | Requisito (capability `payment-idempotency`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Clave única por pagador, monto, destino y ventana | Clave de idempotencia por intento de pago | 2.1 (1.3 verifica el registro de decisiones) | OQ-01 (decidida, híbrida), OQ-12 |
| 2. Solicitud repetida devuelve el resultado original | Solicitud repetida devuelve el resultado original | 2.2, 2.3, 2.5 (2.4 agregada por análisis) | OQ-02 (decidida, nuevo intento vinculado) |
| 3. Duplicados registrados con identificadores de solicitud y correlación | Registro de auditoría de solicitudes duplicadas | 3.1, 3.2 | OQ-13 |
| 4. Conciliación distingue originales de duplicados | Distinción de originales y duplicados para conciliación | 5.1-5.3 | OQ-14 (decidida, diferir) |
| (agregado por análisis, deriva de OQ-11) | Retención de claves configurable por canal | 4.1, 4.2 | OQ-11 |
| Verificación transversal de los criterios 1 a 4 | Todos los requisitos de `payment-idempotency` | 6.1 | — |

### 2.2 PAYER (Fase 1) — [Confirmación de pagos de bajo monto](stories/payer-low-value-payment-confirmation.sp.md)

| Criterio | Requisito (capability `payer-low-value-payment-confirmation`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Destino y monto antes de confirmar | Resumen previo a la confirmación final | 3.1-3.3 | — |
| 2. Un único resultado terminal por intento | Resultado terminal único por intento | 4.1-4.4 | OQ-17 |
| 3. Referencia mostrada y persistida en el historial | Referencia de transacción en pagos exitosos | 6.1-6.3 | OQ-04 |
| 4. Siguiente acción sin cobros duplicados | Siguiente acción tras fallo o expiración | 5.1-5.3 (1.4 y 1.5 acuerdan el contrato y registran las decisiones) | OQ-01, OQ-02 (decididas), OQ-10 |
| 4. (ampliación; agregado por análisis a partir de OQ-03) | Verificación del intento previo antes de un nuevo intento | 5.4, 5.5 | OQ-03 (decidida), OQ-38, OQ-39, OQ-40 (agregadas por análisis), OQ-17 |
| (agregado por análisis, contexto de la HU) | Validación de monto antes del envío | 2.1-2.3 | OQ-15 |
| (agregado por análisis, supuesto de la HU) | Etiquetas de estados terminales pendientes de definición | 1.2, 4.3 | OQ-16 |
| 5. Caída en checkout 30% → 8% (cohorte MVP Perú) | Instrumentación del funnel de checkout (escenarios «Eventos de funnel registrados», «Reporte de caída en checkout», «Fórmula de la tasa pendiente de definición») | 7.2, 7.3 | OQ-06, OQ-18 |
| 6. Evento de activación para MAU 1,000–2,000 | Evento de activación del pagador (escenario «Conteo mensual de pagadores activos») | 7.1, 7.3 | OQ-05, OQ-07 |
| 5. Caída en checkout 30% → 8% (cohorte MVP Perú) | Instrumentación del funnel de checkout (escenarios «Eventos de funnel registrados», «Reporte de caída en checkout», «Fórmula de la tasa pendiente de definición») | 7.2, 7.3 | OQ-06, OQ-18 |
| 6. Evento de activación para MAU 1,000–2,000 | Evento de activación del pagador (escenario «Conteo mensual de pagadores activos») | 7.1, 7.3 | OQ-05, OQ-07 |

### 2.3 ONB (Fase 1) — [Registro y activación del MVP de wallet](stories/user-onboarding-mvp-completion.sp.md)

| Criterio | Requisito (capability `user-onboarding-mvp-completion`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Pasos y paso actual visibles | Secuencia de pasos y paso actual visibles | 1.7 (contrato de configuración), 2.1, 2.2 | OQ-19 (decidida, motor configurable; KYC real pendiente de Cumplimiento) |
| 2. Bloqueo y mensaje accionable | Validación bloqueante con mensaje accionable | 3.1, 3.2 | OQ-19 (decidida) |
| 3. Wallet `activo` y acceso a pagos | Activación del estado de la wallet al finalizar el onboarding | 4.1, 4.2 | OQ-23 |
| 4. Eventos de inicio, paso y cierre | Eventos de analítica del onboarding | 5.1, 5.2 | OQ-06, OQ-21 |
| 5. Mediana 8 → 3 minutos | Datos para medir la duración de onboarding (escenarios «Cálculo de la mediana de la cohorte», «Reporte periódico de duración», «Frontera de eventos no definida») | 5.3 | OQ-20 |
| 6. Nuevos usuarios activos y gasto para MAU y CAC | Salida analítica de nuevos usuarios activos y gasto de adquisición (escenarios «Conteo mensual…», «Atribución…», «Campos de la salida mensual») | 6.1-6.3 (6.2 **bloqueada por OQ-22**) | OQ-05, OQ-07, OQ-22 |
| Verificación transversal (recorrido con pasos «ejemplo no aprobado») | Todos los requisitos de `user-onboarding-mvp-completion` | 7.1 | — |

### 2.4 MERCH (Fase 2, no priorizada) — [Visibilidad del estado de pagos QR](stories/merchant-qr-payment-status-visibility.sp.md)

| Criterio | Requisito (capability `merchant-qr-payment-status`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Intento QR con referencia única | Referencia única por intento de pago QR | 1.1, 3.1 | OQ-04, OQ-08 |
| 2. Estado actual dentro del conjunto MVP | Estado actual dentro del conjunto de estados MVP | 1.2, 1.3 | OQ-24 |
| 3. Vista actualizada por callbacks | Actualización del estado por eventos del proveedor | 2.1-2.4, 3.3 | OQ-25, OQ-26, OQ-28 |
| 4. Filtro por fecha y referencia | Consulta filtrada del historial de estados | 3.2, 3.4 | OQ-27 |

### 2.5 FAIL (Fase 2, no priorizada) — [Manejo de fallas de pago y reversos](stories/payment-failure-reversal-handling.sp.md)

| Criterio | Requisito (capability `payment-failure-support-routing`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Código de motivo legible por máquina | Código de motivo legible por máquina para pagos fallidos y expirados | 1.1-1.3 | OQ-31 |
| 2. Elegibilidad: reintento, investigación o disputa | Ruta de atención visible en la vista de soporte | 2.1, 2.2 | OQ-29, OQ-32 |
| 3. Falla técnica vs transferencia ejecutada | Ruta de ayuda al usuario diferenciada por tipo de escenario | 3.1, 3.2 | OQ-30, OQ-32 |
| 4. Acciones con referencia y estado de resolución | Registro de acciones de soporte | 4.1, 4.2 | OQ-33 |
| (agregado por análisis, riesgo de la épica) | Reintento sin duplicidad financiera | 2.3, 2.4 | OQ-02 (decidida el 2026-11-06; el texto de FAIL aún la marca bloqueante: reconciliar antes de priorizar) |

### 2.6 RECON (Fase 2, no priorizada) — [Conciliación operativa de transacciones](stories/ops-transaction-reconciliation.sp.md)

| Criterio | Requisito (capability `transaction-reconciliation`) | Tareas | Preguntas |
|---|---|---|---|
| 1. Wallet vs resultado del proveedor por canal | Conciliación diaria de transacciones por canal | 2.1-2.3 | OQ-09, OQ-35 |
| 2. Descalce con referencia, tipo y estado de investigación | Marcado de descalces | 4.1, 4.2 | OQ-36 |
| 3. Filtro por fecha y canal | Filtrado de reportes de conciliación | 5.1 | OQ-35 |
| 4. Resumen diario conciliados / no conciliados / resueltos | Resumen diario de conciliación | 5.3 | OQ-37 |
| (IDEM criterio 4, consumido) | Distinción de originales y reintentos duplicados en reporte y resumen | 3.1-3.3, 5.2, 5.4 | OQ-14 (decidida, diferir: la regla de asignación por día la decide RECON en Fase 2; el texto de la spec aún la marca pendiente) |

## 3. Resumen de cobertura

| Medida | Resultado |
|---|---|
| Criterios de aceptación de las 6 historias | 28 (IDEM 4, PAYER 6, ONB 6, MERCH 4, FAIL 4, RECON 4) |
| Criterios con al menos un requisito y escenario WHEN/THEN | 28 de 28 |
| Requisitos totales en las specs | 35 (IDEM 5, PAYER 9, ONB 6, MERCH 4, FAIL 5, RECON 6) |
| Requisitos que trazan a un criterio de una HU | 29 |
| Requisitos «agregado por análisis» | 6 (ver sección 4) |
| Criterios cuantitativos expresados como instrumentación/reporte | 4 de 4 (O1 a O4), con parámetros configurables |
| Criterios cuantitativos verificables **solo** con decisión pendiente | O1 (OQ-18), O2 (OQ-20), O3 (OQ-05, OQ-07), O4 (OQ-22, OQ-07) |
| Tareas en los `tasks.md` | 120 (Fase 1: 64 = IDEM 17, ONB 20, PAYER 27; Fase 2: 56 = MERCH 16, FAIL 15, RECON 25) |
| Capacidades definidas en más de un cambio | 0 (idempotencia: IDEM; reporte de conciliación: RECON; «activación»: dos significados separados en el [glosario](GLOSSARY.md)) |

Notas de cobertura:

- Las specs **no garantizan** que se alcancen 8%, 3 min, 1,000–2,000 MAU ni PEN 10: solo exigen que los datos y reportes necesarios existan. La verificación consolidada de MAU y CAC no tiene responsable (OQ-07).
- Ningún cambio define cómo el cliente crea el pago QR (OQ-08, Fase 2); MERCH asume que el intento existe.
- La verificación del intento previo (OQ-03) y los reintentos vinculados (OQ-02) se especifican solo en el flujo del pagador y en IDEM; su aplicación al pago QR depende de OQ-08.

## 4. Requisitos y tareas agregados por análisis

Elementos que no provienen de un criterio de aceptación de una HU. Se conservan etiquetados «agregado por análisis» en los artefactos.

### 4.1 Requisitos

| Cambio | Requisito | Justificación |
|---|---|---|
| IDEM | Retención de claves configurable por canal | Deriva de la pregunta abierta de la HU (OQ-11). |
| PAYER | Validación de monto antes del envío | Contexto de la HU y restricción de límites por proveedor de la épica (OQ-15). |
| PAYER | Etiquetas de estados terminales pendientes de definición | Supuesto de la HU (OQ-16). |
| PAYER | Verificación del intento previo antes de un nuevo intento | Materializa la decisión OQ-03 (2026-11-06); el alcance («misma intención de pago»), el significado de «incierto» y el tratamiento de la verificación que no se completa son supuestos de análisis (OQ-38, OQ-39, OQ-40). |
| FAIL | Reintento sin duplicidad financiera | Riesgo de duplicidad de la épica; es solo consumo del contrato de IDEM (OQ-02). |
| RECON | Alcance de la evaluación del descalce | Evita fijar un umbral no aprobado (OQ-34). |

### 4.2 Escenarios

| Cambio | Escenario | Justificación |
|---|---|---|
| IDEM | Repetición mientras el intento sigue en proceso; Mismo comportamiento en cualquier riel; Una sola transacción por clave | Precisan el criterio 2 y el riesgo multirriel. |
| IDEM | Identificador de intención generado al abrir la confirmación; Pago legítimo idéntico con otra intención no es duplicado; Mismo identificador de intención repetido es duplicado; Reintentar tras fallo o expiración crea un nuevo intento vinculado; La clave original sigue devolviendo el resultado original; Vínculo reintento-original almacenado; Datos expuestos por solicitud; Día de reporte del duplicado no asignado aquí; Reintento vinculado distinguido del duplicado | Materializan las decisiones del 2026-11-06 (OQ-01, OQ-02, OQ-14); no provienen de un criterio de la HU. |
| PAYER | No se permite confirmar sin datos del destino; Estado pendiente antes del resultado; Pago expirado | Precisan los criterios 1, 2 y 4. |
| PAYER | Identificador de intención al abrir la confirmación; Reintentar crea un nuevo intento vinculado; La clave original conserva el resultado original; Repetición de la misma confirmación | Materializan las decisiones OQ-01 y OQ-02 en el flujo del pagador. |
| PAYER | Alcance y definición de incierto | **Agregado por análisis**: fija el alcance del «intento previo» y el significado de «incierto» (OQ-38, OQ-39). |
| PAYER | Previo en proceso bloquea el nuevo intento; Previo incierto bloquea el nuevo intento; Previo terminal permite el nuevo intento; Mensaje accionable durante el bloqueo; Fin del bloqueo al llegar a un estado terminal; Repetición de la misma confirmación no es un nuevo intento | Materializan la decisión OQ-03; el tratamiento de la consulta que no se completa como incierto es un supuesto (OQ-40). |
| PAYER | Conteo mensual de pagadores activos; Reporte de caída en checkout; Fórmula de la tasa pendiente de definición | Expresan los criterios 5 y 6 como salida medible (no agregan comportamiento nuevo). |
| ONB | Los pasos provienen de configuración; Cambiar la configuración cambia los pasos sin cambiar el comportamiento; Los pasos de ejemplo no son requisitos regulatorios; Las validaciones provienen de configuración; Cambiar las reglas configuradas cambia la validación sin cambiar el comportamiento | Materializan la decisión OQ-19 (motor de pasos configurable). |
| ONB | Eventos sin duplicados; Mes sin gasto de adquisición disponible | Protegen los criterios 4, 5 y 6. |
| ONB | Reporte periódico de duración; Campos de la salida mensual | Expresan los criterios 5 y 6 como salida medible. |
| MERCH | Aislamiento entre comercios; Estado fuera del conjunto habilitado; Evento duplicado; Evento fuera de orden; Evento para transacción desconocida | Seguridad y riesgos de terceros de la épica. |
| MERCH | Plazo de reflejo en la vista | Hace medible el criterio 3 (OQ-28). |
| FAIL | Motivo de origen no reconocido; Pago elegible para investigación (estado incierto) | Evitan perder casos u ofrecer reintento ante incertidumbre. |
| RECON | Registros con datos diferentes; Intención de pago sin asiento de ledger; Salida disponible por cada día conciliado; Registro sin marcado de origen; Varias transacciones financieras para un mismo intento original | Derivan del criterio 1, del enunciado de la HU y de las decisiones 3 y 8 del diseño. |

### 4.3 Tareas

| Cambio | Tareas agregadas por análisis |
|---|---|
| IDEM | 1.3 (verificación del registro de decisiones OQ-01, OQ-02 y OQ-14), 1.4 (OQ-13), 2.4, 2.5 (reintento vinculado, OQ-02), 4.1, 4.2 |
| PAYER | 1.4 (contrato del identificador de intención, derivada de OQ-01), 1.5 (decisiones OQ-01 a OQ-03 y condiciones de «incierto»), 1.6 (OQ-10, OQ-04), grupo 2 completo (validación de monto), 5.4 y 5.5 (verificación del intento previo, OQ-03) |
| ONB | 1.5 (OQ-21, OQ-06), 1.6 (OQ-07), 1.7 (contrato de configuración de pasos con ejemplo no aprobado, decisión OQ-19), 5.2 |
| MERCH (Fase 2) | 2.1, 2.3, 2.4, 3.1 (aislamiento), grupo 5 completo |
| FAIL (Fase 2) | 1.x (código «no clasificado»), 2.3, 2.4, grupo 6 completo |
| RECON (Fase 2) | 1.6, 1.7, 2.4, 2.5, 3.3, 3.4, 5.5 |

## 5. Dependencias entre cambios y orden recomendado

### 5.1 Tabla de dependencias

| Cambio | Depende de | Fuerza | Qué consume |
|---|---|---|---|
| IDEM | — | — | Base del conjunto. Decisiones OQ-01, OQ-02 y OQ-14 ya tomadas (2026-11-06); OQ-11 a OQ-13 son valores configurables con propuesta provisional. |
| ONB | — (KYC real: dependencia externa de Cumplimiento, OQ-19) | — | Habilita el estado `activo`. El motor de pasos configurable no depende del KYC real. |
| PAYER | IDEM | Fuerte | Clave (derivada a partir del identificador de intención que PAYER envía), resultado original, vínculo de reintento y auditoría de duplicados. |
| PAYER | ONB | Fuerte (precondición) | Wallet `activo` para acceder al flujo. |
| FAIL (Fase 2) | IDEM | Fuerte | Contrato de reintento sin duplicidad financiera (reconciliar con OQ-02, decidida). |
| FAIL (Fase 2) | PAYER | Fuerte | Estados terminales fallido/expirado, referencia y confirmación tardía. |
| MERCH (Fase 2) | Proveedores externos; creación del intento QR (OQ-08) | Fuerte (externa) | Callbacks/eventos del proveedor. |
| MERCH (Fase 2) | IDEM | Opcional | Registro de duplicados e identificadores de correlación. |
| MERCH (Fase 2) | PAYER | Coherencia | Estados del comercio correlacionables con estados del pagador (OQ-24). |
| RECON (Fase 2) | IDEM | Fuerte | Marcado original/duplicado, vínculo al original y ambas fechas (OQ-14, decidida: la regla de día la define RECON). |
| RECON (Fase 2) | PAYER | Fuerte | Estados terminales y referencia. |
| RECON (Fase 2) | MERCH | Fuerte | Estados del comercio (conjunto MVP). |
| RECON (Fase 2) | FAIL | Relación (no dependencia) | Ruta de investigación vs estado de investigación del descalce (OQ-33). |

### 5.2 Orden recomendado de implementación

#### Fase 1 (alcance priorizado: 64 tareas)

| Orden | Cambio | Razón | Preguntas que aún necesitan respuesta **antes** |
|---|---|---|---|
| 1 | IDEM (17 tareas) | Contrato base que consume PAYER (y luego FAIL y RECON); sin él las pruebas de duplicidad de PAYER no pueden cerrarse. Sus decisiones OQ-01, OQ-02 y OQ-14 ya están tomadas. | Ninguna para iniciar. Antes de cerrar: aprobar los valores de OQ-11 y OQ-12 (tarea 1.1) y OQ-13 (tarea 1.4), hoy con propuesta provisional no aprobada. Para cerrar 5.3 hace falta la confirmación del formato por parte de RECON (Fase 2). |
| 1 (en paralelo con IDEM) | ONB (20 tareas) | Independiente de IDEM; habilita `activo`, precondición de PAYER. Con el motor de pasos configurable (OQ-19) avanza sin esperar el KYC real, que sigue siendo dependencia externa de Cumplimiento. | **OQ-22 antes de la tarea 6.2** (única que bloquea). Antes de cerrar: OQ-20 (tarea 5.3), OQ-05 (glosario aprobado, tareas 1.3 y 6.3), OQ-21, OQ-06, OQ-23 y OQ-07 (tareas 1.4 a 1.6). Los pasos reales de KYC los define Cumplimiento: sin ellos no hay recorrido real de usuarios (2.x, 3.x y 7.1 se prueban con pasos «ejemplo no aprobado»). |
| 2 | PAYER (27 tareas) | Es el flujo que genera los estados terminales y la referencia que consumen FAIL y RECON; requiere el contrato de IDEM (identificador de intención, clave, vínculo de reintento) y la precondición `activo` de ONB. Puede iniciar cuando IDEM tenga acordado el contrato de entrada (tarea 1.4). | Ninguna para iniciar. Antes de cerrar 5.4 y 5.5: confirmar **OQ-38, OQ-39 y OQ-40** (agregadas por análisis); OQ-17 (fija cuánto puede durar el bloqueo por un previo incierto); OQ-15 y OQ-16 (configurables); OQ-04 y OQ-10 (tarea 1.6); OQ-05, OQ-06 y OQ-18 para verificar 7.1 a 7.3. |

#### Fase 2 (no priorizada; después de la Fase 1)

Antes de priorizar, reconciliar FAIL con OQ-01/OQ-02 y RECON con OQ-14 (ver [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md), sección 0.1).

| Orden | Cambio | Razón | Preguntas a resolver **antes** |
|---|---|---|---|
| 3 | MERCH (16 tareas) | Puede iniciar en paralelo a PAYER con proveedor simulado, pero sus estados deben cerrarse coherentes con los de PAYER; RECON los necesita. | OQ-08, OQ-24, OQ-25, OQ-26 |
| 4 | FAIL (15 tareas) | Clasifica resultados de PAYER y reutiliza el contrato de IDEM; la ruta de disputa se habilita al final. | OQ-29, OQ-30, OQ-32 (OQ-02 ya decidida: reconciliar su texto) |
| 5 | RECON (25 tareas) | Consume estados de PAYER y MERCH y el marcado de IDEM; al final se concilia lo que los demás ya producen. | OQ-09, OQ-35, OQ-36, OQ-37 (OQ-14 decidida: RECON define la regla de asignación por día) |

Las preguntas de analítica de la épica (OQ-05, OQ-06, OQ-07, OQ-18, OQ-20, OQ-21) no bloquean el orden anterior, pero deben cerrarse antes del lanzamiento para poder verificar los objetivos O1 a O4. Las decisiones del 2026-11-06 (OQ-01, OQ-02, OQ-03, OQ-14, OQ-19) ya no figuran como bloqueos.
