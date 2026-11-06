# Design

## Context

- El repositorio es **greenfield**: no existe código de aplicación, stack definido ni specs previas en `openspec/specs/`. Este diseño describe componentes lógicos; no se referencian archivos existentes.
- Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/payer-low-value-payment-confirmation/spec.md`.
- La idempotencia de pagos es propiedad de la capability `payment-idempotency` (cambio `payment-idempotency-protection`); este diseño la consume.
- Terminología (intento de pago, intención de pago, transacción, referencia, reintentar vs reintento duplicado, activación): ver [GLOSSARY.md](../../../docs/GLOSSARY.md). Preguntas abiertas: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).
- Precondición: el acceso al flujo exige wallet `activo`, garantizado por `user-onboarding-mvp-completion`.
- Restricciones de la épica ([peru-wallet-mvp](../../../docs/epic/peru-wallet-mvp.sp.md)): ecosistema multirriel (no asumir un único riel de extremo a extremo), límites por proveedor posiblemente menores al máximo regulatorio, expectativa de pagos inmediatos 24x7x365, riesgo de duplicidad por reintentos sin idempotencia y de pérdida de confianza por estados asíncronos poco claros.

## Goals / Non-Goals

**Goals:**

- Un único resultado terminal por intento, robusto ante estados asíncronos y señales repetidas.
- Reintentos que no generen cobros duplicados visibles para el pagador, apoyándose en la capability `payment-idempotency` (no se redefine aquí), con «reintentar» como nuevo intento vinculado y sin nuevo intento mientras el previo esté en proceso o incierto.
- Emisión confiable (una vez) del evento de activación y de los eventos de funnel.
- Reglas de monto y textos de estado configurables, sin valores fijados en código.

**Non-Goals:**

- Elegir tecnología, proveedor o gateway concreto.
- Diseñar conciliación, reversos/disputas o la vista del comercio (otros cambios).
- Definir la derivación de la clave de idempotencia, la devolución del resultado original o la auditoría de duplicados (capability `payment-idempotency`, cambio `payment-idempotency-protection`); este flujo solo genera y envía el identificador de intención (OQ-01).
- Cálculo de MAU/CAC.

## Decisions

1. **Máquina de estados del intento de pago.** Estados: `creado → en_proceso → {exitoso | fallido | expirado}`; los tres últimos son terminales e inmutables. Una transición desde un estado terminal se ignora y se registra. *Alternativa:* permitir sobrescribir el estado con la última señal del proveedor; descartada por violar el "resultado único".
2. **Consumo de `payment-idempotency` (decisión OQ-01, híbrida; Decidida 2026-11-06).** Este flujo genera un **identificador de intención** cuando se abre la pantalla de confirmación y lo envía a `payment-idempotency` en cada envío de esa confirmación (incluidas las repeticiones por doble toque o pérdida de conexión, que reutilizan el mismo identificador). Es lo único que este cambio posee sobre la clave: `payment-idempotency` deriva la clave a partir del identificador de intención más pagador, monto, destino y ventana de intento, y define la devolución del resultado original y la auditoría de duplicados (dueño: cambio `payment-idempotency-protection`). Este flujo no deriva, calcula ni almacena la clave ni implementa lógica de duplicados propia. Se conserva el requisito visible al usuario: ni una repetición de la misma confirmación ni un reintento deliberado crean cobros duplicados. *Alternativas descartadas:* clave propia generada al abrir la confirmación (duplicaba el contrato común y podía divergir) y clave solo derivada sin identificador (podía tratar como duplicado a dos pagos idénticos intencionales dentro de la misma ventana).
   - **Reintentar (decisión OQ-02; Decidida 2026-11-06).** "Reintentar" tras fallo o expiración crea un **nuevo intento vinculado** al original: el flujo genera un nuevo identificador de intención (por tanto, nueva clave en `payment-idempotency`), se asigna una nueva referencia de transacción y el nuevo intento guarda el vínculo «reintento de» hacia el original. El intento original conserva su estado terminal; su clave sigue devolviendo el resultado original. *Alternativa descartada:* reutilizar la clave, que devolvería el resultado original fallido en lugar de reintentar el pago.
   - **Verificación del intento previo (decisión OQ-03; Decidida 2026-11-06).** Antes de crear un nuevo intento (por «reintentar» o por un nuevo pago de la misma intención) el flujo consulta el estado del intento previo. Si está en proceso (estado no terminal: `creado` o `en_proceso`) o **incierto**, no se crea el nuevo intento ni se envía nada a `payment-idempotency`; si es terminal (`fallido` o `expirado`), se permite. «Incierto» no es un estado nuevo de la máquina: designa al intento sin resultado terminal cuyo estado no pudo confirmarse con el proveedor (incluida una consulta de verificación que no se completa; se trata como incierto, es decir, el bloqueo falla de forma segura). El bloqueo se levanta cuando el previo alcanza un estado terminal, incluida la expiración por tiempo máximo (OQ-17). *Alcance asumido (supuesto de análisis):* «intento previo» es el de la misma intención de pago (pagador, monto y destino); no bloquea pagos distintos del mismo pagador. Esta verificación es distinta de la idempotencia: una repetición con el mismo identificador de intención la resuelve `payment-idempotency` devolviendo el estado o resultado original; un intento **nuevo** (identificador nuevo) es lo que la verificación puede bloquear.
   - **Bloqueo visible al pagador.** Mientras dura el bloqueo, el pagador ve un mensaje accionable que indica que su pago anterior sigue en proceso o pendiente de confirmación y que debe esperar el resultado, con las acciones «ver estado del pago anterior» y «volver»; no se crea cobro, intento ni referencia nuevos. Los textos provienen de contenido configurable.
3. **Estado asíncrono.** El pagador ve un estado "en proceso" hasta recibir un estado final del proveedor o vencer un tiempo máximo de intento (valor por definir, configurable; OQ-17) que produce `expirado`. Una confirmación tardía sobre un intento expirado no crea un nuevo cobro ni cambia el resultado terminal ya entregado; se registra como discrepancia para tratamiento operativo posterior (consumida por `payment-failure-reversal-handling` y `ops-transaction-reconciliation`; qué se comunica al pagador queda en OQ-10).
4. **Reglas de monto por configuración.** Un componente de reglas por proveedor/canal resuelve el límite aplicable y se evalúa antes del envío. Los valores iniciales no se definen aquí (pregunta abierta).
5. **Textos de estados desde contenido configurable.** Los tres estados tienen identificadores estables; las etiquetas visibles se externalizan hasta que producto las defina.
6. **Eventos y reporte.** El evento de activación se emite en la transición a `exitoso`, deduplicado por referencia de transacción, con referencia, pagador, marca de tiempo y atributo de cohorte MVP Perú. Los eventos de funnel (inicio, confirmación final, resultado, abandono) se emiten desde el flujo de pago con el mismo atributo. El reporte de caída en checkout se deriva de esos eventos; su fórmula y la definición de abandono quedan en OQ-18, y el criterio de cohorte en OQ-06.
7. **Referencia de transacción.** Identifica al intento de pago y es la misma referencia que usan comercio (criterio 1 de su HU), soporte (criterio 4 de su HU) y conciliación (clave de cruce). Se asume asignada desde la creación del intento (OQ-04) para que esos consumidores puedan referenciar intentos aún no exitosos; al pagador se le muestra al llegar a `exitoso` y se persiste en el historial en la misma operación lógica que registra el estado terminal, para que lo mostrado y lo persistido coincidan.

## Risks / Trade-offs

- [Duplicidad financiera por reintentos] → Se delega en el contrato de `payment-idempotency` (identificador de intención enviado por este flujo) y en la verificación del intento previo (OQ-03); este flujo solo debe usarlos y mostrar al pagador el resultado original.
- [Bloqueo del pagador por un intento previo incierto] → La verificación (OQ-03) puede frustrar al pagador mientras el previo no es terminal; se mitiga con un mensaje accionable, con el tiempo máximo del intento (OQ-17) que lo lleva a `expirado` y con el alcance acotado a la misma intención de pago.
- [Reintento vinculado y métricas de funnel] → Cada reintento es un intento nuevo con su propia referencia; el vínculo «reintento de» permite agrupar intentos de una misma intención, y cómo se cuentan en caída/abandono lo define OQ-18.
- [Confirmación tardía tras expiración] → Estado terminal inmutable + registro de discrepancia; el tratamiento queda a cargo de operaciones/reversos (otros cambios).
- [Límites distintos por proveedor generan confusión al usuario] → Validar antes del envío con un mensaje que indica el límite aplicable.
- [Tiempo máximo corto expira pagos que luego se confirman; tiempo largo degrada la percepción de espera] → Valor configurable y ajustable con datos del funnel.
- [Dependencia de partners/gateways aún no habilitados contractualmente] → Aislar la integración tras una interfaz de proveedor; el diseño no asume un riel único.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md).

Decididas (2026-11-06; reflejadas en la decisión 2):

- OQ-01: **Decidida (2026-11-06)** — híbrida: este flujo genera y envía el identificador de intención al abrir la confirmación; `payment-idempotency` deriva la clave de él más pagador, monto, destino y ventana de intento.
- OQ-02: **Decidida (2026-11-06)** — "reintentar" crea un nuevo intento vinculado al original (nueva clave, nueva referencia, vínculo «reintento de»).
- OQ-03: **Decidida (2026-11-06)** — se conserva la verificación del intento previo y bloquea un nuevo intento mientras el previo esté en proceso o incierto.

Abiertas (no se responden aquí):

- OQ-10: ¿qué ocurre de cara al pagador y al historial cuando un intento expirado se confirma tarde?

Decididas el 2026-11-06 (registro: OPEN-QUESTIONS.md, sección 0):

- OQ-15: el tope de monto es el límite del proveedor/canal, cargado como configuración.
- OQ-04: la referencia de transacción se asigna al crear el intento.
- OQ-05: MAU = pagadores distintos con al menos un evento de activación del pagador en el mes.
- OQ-06: la cohorte MVP Perú se asigna al inicio del onboarding.
- OQ-16: etiquetas «Exitoso», «Fallido» y «Expirado» (contenido configurable).
- OQ-17: tiempo máximo del intento de 120 segundos (configurable).
- OQ-18: tasa de caída = intentos iniciados que no llegan a `exitoso` ÷ intentos iniciados; la definición de «abandono» sigue pendiente.

Supuestos (de la HU y la épica, sin resolver):

- Las etiquetas de los estados terminales visibles al usuario quedan por definir con producto (OQ-16).
- El rango objetivo de MAU (1,000–2,000) y el CAC (PEN 10) fueron definidos por el Product Owner.
- El tiempo máximo de un intento antes de expirar no está definido en las fuentes; se asume configurable (OQ-17).
- La definición exacta del evento de activación para MAU y del "abandono" en el funnel se asume por acordar con analítica/producto (OQ-05, OQ-18).
