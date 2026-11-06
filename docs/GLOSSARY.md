# Glosario de dominio — MVP de wallet en Perú

Glosario único de los términos usados en la [épica](epic/peru-wallet-mvp.sp.md), las [historias](stories/) y los cambios OpenSpec. Si un término de un artefacto contradice esta tabla, prevalece esta tabla y se corrige el artefacto.

> Estado: **borrador de trabajo para aprobación de Producto y Analítica**. Las definiciones marcadas con ⚠ dependen de una pregunta abierta en [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) y no están aprobadas.

Abreviaturas de cambios: **IDEM** = `payment-idempotency-protection`, **PAYER** = `payer-low-value-payment-confirmation`, **FAIL** = `payment-failure-reversal-handling`, **MERCH** = `merchant-qr-payment-status-visibility`, **RECON** = `ops-transaction-reconciliation`, **ONB** = `user-onboarding-mvp-completion`.

## 1. Términos ambiguos (leer primero)

### 1.1 «Activación» tiene dos significados distintos

| Significado | Nombre a usar | Qué es | Cuándo ocurre | Cambio dueño |
|---|---|---|---|---|
| A | **Wallet activa** / estado de wallet `activo` | Hecho del ciclo de vida de la cuenta | Una vez por usuario, al cerrar correctamente el onboarding | ONB |
| B | **Evento de activación del pagador** | Evento de analítica | Una vez por cada transacción exitosa del pagador | PAYER |

- Son hechos independientes: una wallet `activo` puede no haber emitido aún ningún evento de activación del pagador (todavía no pagó), y el evento de activación no cambia el estado de la wallet.
- ONB no emite el evento B y PAYER no cambia el estado de la wallet.
- Cuál de los dos (o cuál combinación) alimenta el MAU ⚠ queda en **OQ-05**. Los nombres de eventos y atributos de ambos cambios deben ser distintos.
- No usar «activación» sin calificar en artefactos nuevos.

### 1.2 «Reintento» y términos cercanos

| Término | Definición | Quién lo origina | Cambio dueño |
|---|---|---|---|
| **Reintentar** | Acción deliberada del pagador (o de soporte) tras un resultado fallido o expirado. Decidido (OQ-02, 2026-11-06): crea un **nuevo intento vinculado** al original, no reutiliza la clave | Persona | PAYER (pagador), IDEM (vínculo); FAIL (soporte, Fase 2: su redacción debe reconciliarse) |
| **Intento vinculado** («reintento de») | Nuevo intento creado por «reintentar», con nueva clave, nueva referencia de transacción y un vínculo «reintento de» hacia el intento original. El original conserva su estado y resultado | Persona (vía «reintentar») | IDEM (almacena el vínculo), PAYER (lo crea) |
| **Solicitud repetida** / **reintento duplicado** | Solicitud con una clave de idempotencia ya registrada (doble toque, pérdida de conexión, reenvío) | Cliente o sistema | IDEM |
| **Evento duplicado** (del proveedor) | Callback/evento del proveedor recibido más de una vez | Proveedor | MERCH |
| **Evento de analítica duplicado** | Evento de onboarding o de activación reportado más de una vez | Cliente o servicio | ONB, PAYER |

Son cuatro fenómenos distintos con mecanismos distintos, más el **intento vinculado**, que no es un duplicado: es un intento nuevo y legítimo, con su propia clave y su propia referencia, y puede generar como máximo un cobro. «Reintentar» (acción de la persona) crea un intento vinculado; «reintento duplicado» (solicitud repetida con la misma clave) devuelve el resultado original. Decidido en **OQ-02** (2026-11-06).

### 1.3 «Transacción» frente a «intento de pago»

| Término | Definición | Notas |
|---|---|---|
| **Intención de pago** | Propósito del pagador de transferir un monto a un destino (pagador + monto + destino). | Una intención puede originar varios intentos (p. ej., tras un fallo). |
| **Intento de pago** | Cada envío concreto de una intención; tiene referencia, estado y, como máximo, un resultado terminal. | Es el sujeto de los criterios de PAYER, IDEM y MERCH. |
| **Transacción** | Uso genérico de las historias de MERCH, FAIL y RECON: el intento de pago identificado por su referencia. | No implica por sí mismo movimiento de fondos. |
| **Transacción financiera** | Movimiento efectivo de fondos asociado a un intento. | IDEM garantiza como máximo una por clave de idempotencia. |

## 2. Pagos e idempotencia

| Término | Definición | Cambio dueño | Notas |
|---|---|---|---|
| **Referencia de transacción** | Identificador único de un intento de pago. Lo muestran PAYER y MERCH, lo usa FAIL en sus registros y RECON como clave de cruce. | PAYER (se muestra), común | ⚠ Se asume asignada desde la creación del intento (**OQ-04**) para que MERCH, FAIL y RECON puedan referenciar intentos aún no exitosos. |
| **Clave de idempotencia** | Valor único que identifica un intento para detectar repeticiones. Decidido (OQ-01, 2026-11-06, híbrida): el servidor (IDEM) la deriva del **identificador de intención** más pagador, monto, destino y ventana de intento. | IDEM | El flujo del pagador no deriva ni calcula la clave. |
| **Identificador de intención** | Identificador que el flujo del pagador (PAYER) genera al abrir la pantalla de confirmación y envía a IDEM en cada envío de esa confirmación; se reutiliza en las repeticiones y se genera uno nuevo por cada intento nuevo. | PAYER (genera), IDEM (lo usa en la clave) | Decidido en **OQ-01**. Distingue pagos legítimos idénticos (misma clave sin él) de repeticiones del mismo envío. ⚠ Formato y comportamiento si falta: contrato por acordar entre PAYER e IDEM (PAYER 1.4). |
| **Ventana de intento** | Período que forma parte de la composición de la clave. | IDEM | ⚠ Duración en **OQ-12**. |
| **Ventana de retención** | Tiempo durante el cual una clave sigue vigente, por canal. | IDEM | ⚠ Valor en **OQ-11**. No confundir con la ventana de intento. |
| **Resultado original** | Resultado (o estado actual) del primer intento con una clave; es el que se devuelve a las solicitudes repetidas. | IDEM | Inmutable. |
| **Intento original** | Intento que originó una transacción financiera. | IDEM | Opuesto a «reintento duplicado». |
| **Marcado de origen** | Atributo `original` / `duplicado` (con vínculo al original) que IDEM expone por solicitud junto con la fecha de la solicitud y la fecha del original; RECON lo consume. | IDEM (genera), RECON (consume) | Decidido (**OQ-14**, 2026-11-06, diferir): IDEM expone tipo, vínculo y ambas fechas; la regla de asignación por día la decide conciliación en Fase 2. Un intento vinculado («reintento de») no es un duplicado. |
| **Registro de auditoría de duplicados** | Registro append-only de cada solicitud duplicada con identificador de solicitud, identificador de correlación y clave. | IDEM | ⚠ Conservación en **OQ-13**. |
| **Verificación del intento previo** | Consulta del estado del intento previo antes de permitir un nuevo intento. Decidido (OQ-03, 2026-11-06): **bloquea** el nuevo intento mientras el previo esté en proceso o incierto y lo **permite** cuando es terminal (fallido o expirado). Durante el bloqueo no se crea cobro, intento ni referencia nuevos. | PAYER | ⚠ «Intento previo» = el de la misma intención de pago (pagador, monto y destino): supuesto agregado por análisis en **OQ-38**. |

## 3. Estados

| Término | Definición | Cambio dueño | Notas |
|---|---|---|---|
| **Estados del intento** | `creado → en_proceso → {exitoso \| fallido \| expirado}`. | PAYER | Los tres últimos son terminales e inmutables. |
| **Resultado terminal** | Estado `exitoso`, `fallido` o `expirado`; exactamente uno por intento. | PAYER | ⚠ Etiquetas visibles en **OQ-16**; tiempo máximo antes de `expirado` en **OQ-17**. |
| **Estado MVP del comercio** | Estado de un intento QR dentro del conjunto habilitado para comercios. | MERCH | ⚠ Conjunto y relación con los estados del pagador en **OQ-24**. |
| **Estado incierto** | Pago sin resultado final confirmado por el proveedor o con información contradictoria. | FAIL | Nunca es elegible para reintento. ⚠ Fuente en **OQ-32**. No es un estado del intento, sino una clasificación de soporte. Ver también «Intento incierto». |
| **Intento incierto** | En PAYER (verificación del intento previo): intento **sin resultado terminal** cuyo estado **no pudo confirmarse con el proveedor**, incluida una verificación que no se completa. Bloquea un nuevo intento. | PAYER | **No es un estado nuevo** de la máquina de estados del intento (`creado → en_proceso → {exitoso \| fallido \| expirado}`). ⚠ Supuestos agregados por análisis: definición en **OQ-39** y tratamiento de la verificación que no se completa en **OQ-40**; alinear con el «estado incierto» de soporte (**OQ-32**), que es una clasificación distinta. |
| **Transferencia ejecutada** | Hay evidencia de que los fondos se movieron. | FAIL | ⚠ Fuente de la evidencia en **OQ-32**. |
| **Disputado** | Condición de soporte de un pago asociado a una disputa. | FAIL | No es un estado terminal del intento. ⚠ Categorías en **OQ-29**. |
| **Estado de wallet** | `activo` y un estado previo sin nombre definido. | ONB | ⚠ Nombres en **OQ-23**. |

## 4. Soporte y conciliación

| Término | Definición | Cambio dueño | Notas |
|---|---|---|---|
| **Código de motivo** | Código interno legible por máquina de por qué un pago falló o expiró; incluye «no clasificado». | FAIL | Se conserva también el motivo original del proveedor. |
| **Ruta de atención** | Una de: elegible para **reintento**, **investigación** o **flujo de disputa**. | FAIL | |
| **Estado de resolución** | Estado de una acción de soporte sobre un pago. | FAIL | ⚠ Valores y relación con el estado de investigación en **OQ-33**. |
| **Estado de investigación** | Estado de un descalce en seguimiento de operaciones (inicial y «resuelto» como mínimo). | RECON | No es el «estado de resolución» de soporte, aunque pueden referirse al mismo caso (**OQ-33**). |
| **Canal de proveedor** | Canal/riel de proveedor del MVP sobre el que se concilia y filtra. | RECON | ⚠ Lista exacta en **OQ-09**. |
| **Día conciliado** | Día para el que se genera la salida de conciliación. | RECON | ⚠ Hora de corte y zona horaria en **OQ-35**. |
| **Descalce** | Registro no conciliado: tiene referencia, tipo y estado de investigación. | RECON | ⚠ Catálogo de tipos en **OQ-36**. |
| **Conciliado / No conciliado / Resuelto** | Totales del resumen diario. | RECON | ⚠ Regla de conteo de «resuelto» frente a «no conciliado» en **OQ-37**. |

## 5. Métricas y analítica

| Término | Definición | Cambio dueño | Notas |
|---|---|---|---|
| **Cohorte MVP Perú** | Usuarios sobre los que se miden los objetivos de la épica. Es la forma única de nombrarla en todos los artefactos. | ONB, PAYER | ⚠ Criterio de pertenencia en **OQ-06**. |
| **Caída en checkout** | Proporción de intentos iniciados que no concluyen en pago exitoso. Línea base 30%, objetivo 8%. | PAYER | ⚠ La fórmula y «abandono» son **OQ-18**. |
| **Duración de onboarding** | Tiempo entre los eventos de inicio y fin del onboarding. Mediana base 8 min, objetivo 3 min. | ONB | ⚠ Frontera de eventos en **OQ-20**; alcance del «cierre del flujo» en **OQ-21**. |
| **Cierre del flujo** | Evento que cierra el onboarding. | ONB | ⚠ Si incluye abandono: **OQ-21**. |
| **Nuevo usuario activo** | Para ONB, usuario cuya wallet pasó a `activo` en el mes. | ONB | ⚠ Uso para MAU y CAC en **OQ-05** y **OQ-22**. |
| **MAU** | Usuarios activos mensuales; rango objetivo 1,000–2,000 en los meses 1-3. | (métrica de la épica) | ⚠ Definición operativa en **OQ-05**; responsable del reporte en **OQ-07**. |
| **CAC** | Costo de adquisición por usuario nuevo; objetivo PEN 10 en los meses 1-3. | (métrica de la épica) | ⚠ Fuente del gasto y definición de «usuario nuevo» en **OQ-22**. |

## 6. Otros

| Término | Definición | Cambio dueño | Notas |
|---|---|---|---|
| **Punto de entrada de pagos de bajo monto** | Acceso a PAYER; solo disponible con wallet `activo`. | ONB (habilita), PAYER (lo usa) | |
| **Motor de pasos configurable** | Mecanismo del onboarding que toma de configuración la lista, el orden, los datos requeridos, las reglas de validez y los mensajes accionables de cada paso, de modo que cambiar los pasos no cambia el comportamiento del flujo. | ONB | Decidido en **OQ-19** (2026-11-06). Se construye sin conocer el contenido real de los pasos. |
| **KYC (pendiente de Cumplimiento)** | Requisitos de conocimiento del cliente y documentación del onboarding. El contenido real lo define Cumplimiento. | Cumplimiento (dependencia externa de ONB) | No bloquea el motor de pasos; se cargará como configuración cuando Cumplimiento lo defina. Ningún artefacto debe inventar estos requisitos. |
| **Ejemplo no aprobado** | Etiqueta de los pasos de configuración de ejemplo de ONB, y de cualquier valor o texto de muestra, usados solo para construir y probar. | ONB (y cualquier cambio con valores provisionales) | No es un requisito regulatorio ni un valor aprobado; equivale a «propuesta, no aprobada» y no debe presentarse como requisito. |
| **Callback / evento del proveedor** | Mensaje entrante del proveedor de adquirencia/gateway que informa un cambio de estado. | MERCH | ⚠ Garantías en **OQ-26**. |
| **Pago QR** | Pago de un cliente a un comercio mediante QR. | MERCH (visibilidad) | ⚠ Ningún cambio define su creación (**OQ-08**). |
