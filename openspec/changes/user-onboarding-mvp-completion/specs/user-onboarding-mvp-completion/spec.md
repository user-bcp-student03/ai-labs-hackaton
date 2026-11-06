# Spec Delta

## Purpose

Define el comportamiento observable del onboarding guiado de la wallet del MVP en Perú: pasos visibles, validación bloqueante, activación del estado de la wallet, eventos de analítica y salida analítica para verificar duración de onboarding, MAU y CAC.

## ADDED Requirements

### Requirement: Secuencia de pasos y paso actual visibles
El flujo de onboarding MUST mostrar al usuario la secuencia de pasos requeridos y cuál es el paso actual en todo momento.

Origen: criterio 1 de la HU. Los pasos provienen de configuración (decisión OQ-19, 2026-11-06); los pasos reales de KYC/documentación los define Cumplimiento después.

#### Scenario: Los pasos provienen de configuración
- **WHEN** el flujo se inicia con una definición de pasos configurada
- **THEN** la secuencia, el orden y el paso actual mostrados corresponden exactamente a esa configuración y no a pasos fijados en el flujo

#### Scenario: Cambiar la configuración cambia los pasos sin cambiar el comportamiento
- **WHEN** se reemplaza la configuración por otra con distintos pasos u orden
- **THEN** el flujo muestra los nuevos pasos y mantiene el mismo comportamiento de paso actual, bloqueo, progreso, eventos y activación, sin cambios en el motor

#### Scenario: Los pasos de ejemplo no son requisitos regulatorios
- **WHEN** se usa una configuración de pasos para demostración o pruebas
- **THEN** está etiquetada «ejemplo no aprobado» y no se presenta como requisito de KYC ni regulatorio; los pasos reales los define Cumplimiento

#### Scenario: Se muestra la secuencia al iniciar
- **WHEN** el usuario inicia el onboarding
- **THEN** el flujo muestra todos los pasos requeridos y resalta el primer paso como paso actual

#### Scenario: El paso actual se actualiza al avanzar
- **WHEN** el usuario completa un paso y avanza al siguiente
- **THEN** el flujo mantiene visible la secuencia completa e indica el nuevo paso actual

#### Scenario: El paso actual sigue visible tras un error
- **WHEN** el usuario permanece en un paso por un error de validación
- **THEN** el flujo sigue mostrando la secuencia y ese mismo paso como paso actual

### Requirement: Validación bloqueante con mensaje accionable
El flujo MUST bloquear el avance al siguiente paso cuando falte información obligatoria o haya datos inválidos, y MUST mostrar un mensaje que indique cómo corregirlo.

Origen: criterio 2 de la HU. Los datos obligatorios, sus reglas de validez y los mensajes provienen de la configuración de pasos (decisión OQ-19, 2026-11-06).

#### Scenario: Las validaciones provienen de configuración
- **WHEN** un paso configurado define datos obligatorios, reglas de validez y mensajes
- **THEN** el flujo aplica exactamente esas reglas y muestra esos mensajes, sin reglas fijadas en el flujo

#### Scenario: Cambiar las reglas configuradas cambia la validación sin cambiar el comportamiento
- **WHEN** se modifica la regla de un dato en la configuración
- **THEN** la validación usa la nueva regla y el bloqueo de avance y el mensaje accionable siguen comportándose igual, sin cambios en el motor

#### Scenario: Falta información obligatoria
- **WHEN** el usuario intenta avanzar sin completar un dato obligatorio del paso actual
- **THEN** el flujo no avanza e indica qué dato falta y cómo completarlo

#### Scenario: Datos inválidos
- **WHEN** el usuario intenta avanzar con un dato que no cumple el formato o la regla del campo
- **THEN** el flujo no avanza e indica qué dato es inválido y cómo corregirlo

#### Scenario: Se corrige y se permite avanzar
- **WHEN** el usuario corrige el dato señalado y vuelve a intentar avanzar
- **THEN** el flujo permite avanzar al siguiente paso

### Requirement: Activación del estado de la wallet al finalizar el onboarding
Cuando el onboarding finalice correctamente, el sistema MUST cambiar el estado de la wallet a `activo`.

Origen: criterio 3 de la HU. Ver los escenarios sobre acceso, onboarding incompleto y alcance del término «activación».

#### Scenario: Onboarding finalizado correctamente
- **WHEN** el usuario completa todos los pasos requeridos y el flujo cierra correctamente
- **THEN** el estado de la wallet es `activo` y el usuario puede acceder al punto de entrada de pagos de bajo monto

#### Scenario: Onboarding incompleto
- **WHEN** el usuario abandona el flujo o queda con pasos requeridos pendientes
- **THEN** el estado de la wallet no es `activo` y el usuario no accede al punto de entrada de pagos de bajo monto

#### Scenario: La wallet no pasa a activo mientras el onboarding no finalice
- **WHEN** el onboarding no ha finalizado correctamente
- **THEN** la wallet MUST NOT pasar a `activo`

#### Scenario: Acceso al punto de entrada de pagos de bajo monto
- **WHEN** la wallet pasa a `activo` al finalizar el onboarding
- **THEN** el sistema MUST permitir al usuario acceder al punto de entrada de pagos de bajo monto

#### Scenario: Alcance del término «activación»
- **WHEN** se usa «activación» en el contexto del onboarding
- **THEN** significa el estado de la wallet `activo` y es distinta del «evento de activación del pagador» de `payer-low-value-payment-confirmation` (ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md) y OQ-05)

#### Scenario: Nombres de los demás estados de la wallet
- **WHEN** se requiere nombrar los estados de la wallet distintos de `activo`
- **THEN** sus nombres quedan pendientes de definición (OQ-23)

### Requirement: Eventos de analítica del onboarding
El sistema MUST registrar un evento de inicio de onboarding, un evento por cada paso finalizado y un evento de cierre del flujo, cada uno con marca de tiempo y con identificación de la cohorte MVP Perú.

Origen: criterio 4 de la HU. El escenario «Eventos sin duplicados» es agregado por análisis. Qué casos emiten el evento de cierre (solo finalización exitosa o también abandono) está en OQ-21; el criterio de pertenencia a la cohorte, en OQ-06.

#### Scenario: Registro del inicio
- **WHEN** el usuario inicia el onboarding
- **THEN** se registra un evento de inicio de onboarding con su marca de tiempo

#### Scenario: Registro de cada paso finalizado
- **WHEN** el usuario finaliza un paso
- **THEN** se registra un evento de finalización de ese paso, identificando el paso y su marca de tiempo

#### Scenario: Registro del cierre del flujo
- **WHEN** el flujo de onboarding se cierra
- **THEN** se registra un evento de cierre del flujo con su marca de tiempo; si el cierre por abandono o cancelación también emite este evento queda pendiente (OQ-21)

#### Scenario: Eventos sin duplicados
- **WHEN** el mismo paso o cierre se reporta más de una vez por reintento del cliente
- **THEN** la analítica conserva un único evento por paso y por cierre para ese onboarding

### Requirement: Datos para medir la duración de onboarding
Los eventos de analítica MUST permitir calcular la duración de onboarding por usuario y su mediana para la cohorte MVP Perú.

Origen: criterio 5 de la HU. Ver los escenarios sobre reporte periódico, frontera de eventos (OQ-20) y parámetros de referencia.

#### Scenario: Reporte periódico para verificar la reducción
- **WHEN** se entrega el reporte periódico de la mediana de duración
- **THEN** el sistema MUST entregar ese reporte de modo que pueda verificarse la reducción de 8 a 3 minutos dentro del trimestre posterior al lanzamiento

#### Scenario: Valores de referencia no garantizados
- **WHEN** el reporte muestra los valores 8 y 3 minutos
- **THEN** son parámetros de referencia del reporte, no resultados que el sistema garantice

#### Scenario: Cálculo de la mediana de la cohorte
- **WHEN** analítica consulta los eventos de onboarding de la cohorte MVP Perú de un periodo
- **THEN** puede obtener la duración por usuario y la mediana del periodo usando la frontera de eventos que se defina oficialmente

#### Scenario: Reporte periódico de duración
- **WHEN** se genera el reporte de duración de un mes
- **THEN** el reporte incluye, para la cohorte MVP Perú, el número de onboardings finalizados, la mediana de duración en minutos y su comparación con la línea base de 8 minutos y el objetivo de 3 minutos como parámetros configurables

#### Scenario: Frontera de eventos no definida
- **WHEN** la frontera oficial de eventos de duración aún no ha sido definida (OQ-20)
- **THEN** los eventos de inicio, de paso y de cierre se registran con marcas de tiempo, sin que el sistema fije por sí mismo qué par de eventos define la duración

#### Scenario: Frontera pendiente de definición oficial
- **WHEN** se consulta qué eventos definen el inicio y el fin de la duración
- **THEN** la frontera queda pendiente de definición oficial (OQ-20)

### Requirement: Salida analítica de nuevos usuarios activos y gasto de adquisición
La salida analítica de onboarding MUST incluir conteos mensuales de nuevos usuarios activos y la atribución de gasto de adquisición.

Origen: criterio 6 de la HU. Ver los escenarios sobre definiciones (OQ-05, OQ-22), alcance (OQ-07) y parámetros de referencia.

#### Scenario: Finalidad de verificación de MAU y CAC
- **WHEN** analítica usa la salida de onboarding en los primeros 3 meses posteriores al lanzamiento
- **THEN** la salida incluye lo necesario para verificar MAU entre 1,000 y 2,000 y CAC de PEN 10 por usuario nuevo

#### Scenario: Definición de «nuevo usuario activo»
- **WHEN** se cuenta un nuevo usuario activo en esta salida
- **THEN** significa wallet en estado `activo` (ver [GLOSSARY.md](../../../../../docs/GLOSSARY.md)); si el MAU se calcula con este conteo o con el evento de activación del pagador está en OQ-05

#### Scenario: Fuente del gasto y definición de usuario nuevo para CAC
- **WHEN** se calcula el CAC con la atribución de gasto
- **THEN** la fuente del gasto y la definición de «usuario nuevo» para CAC quedan pendientes (OQ-22)

#### Scenario: Reporte consolidado fuera de alcance
- **WHEN** se requiere el reporte consolidado que compara MAU y CAC con 1,000–2,000 y PEN 10
- **THEN** no pertenece a este cambio (OQ-07); los valores 1,000–2,000 y PEN 10 son parámetros de referencia de la salida, no resultados garantizados

#### Scenario: Conteo mensual de nuevos usuarios activos
- **WHEN** analítica consulta la salida de onboarding para un mes de los primeros 3 posteriores al lanzamiento
- **THEN** obtiene el conteo de nuevos usuarios activos de ese mes de la cohorte MVP Perú

#### Scenario: Atribución de gasto de adquisición
- **WHEN** analítica consulta la salida de onboarding para un mes de los primeros 3 posteriores al lanzamiento
- **THEN** obtiene la atribución de gasto de adquisición, en PEN, necesaria para calcular el CAC por usuario nuevo de ese mes (gasto atribuido dividido entre nuevos usuarios, según la definición de OQ-22)

#### Scenario: Campos de la salida mensual
- **WHEN** analítica consulta la salida de onboarding de un mes de los primeros 3 posteriores al lanzamiento
- **THEN** la salida contiene, por mes y cohorte MVP Perú, el conteo de nuevos usuarios activos, el gasto de adquisición atribuido en PEN y los parámetros de referencia 1,000–2,000 (MAU) y PEN 10 (CAC) configurables

#### Scenario: Mes sin gasto de adquisición disponible
- **WHEN** la fuente del gasto de adquisición no tiene datos para un mes consultado
- **THEN** la salida indica el gasto como no disponible y no lo informa como cero (escenario agregado por análisis)

#### Scenario: Usuario sin onboarding finalizado
- **WHEN** un usuario inició el onboarding pero no lo finalizó correctamente
- **THEN** no se cuenta como nuevo usuario activo en la salida analítica
