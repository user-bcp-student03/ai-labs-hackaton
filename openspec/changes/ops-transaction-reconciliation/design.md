# Design

## Context

- El repositorio es greenfield: no existe código de aplicación, ledger, integración con proveedores ni especificaciones previas (`openspec/specs/` vacío). Este diseño no referencia archivos existentes y no fija tecnología.
- Fuentes: HU [ops-transaction-reconciliation](../../../docs/stories/ops-transaction-reconciliation.sp.md) y épica [peru-wallet-mvp](../../../docs/epic/peru-wallet-mvp.sp.md).
- Restricciones de la épica: ecosistema multirriel (no asumir un único riel), estados de pago asíncronos, dependencia contractual de proveedores y riesgo de duplicidad por reintentos sin idempotencia.
- La capability `payment-idempotency` (cambio `payment-idempotency-protection`) es dueña de la clave de idempotencia, del registro de auditoría de duplicados y del marcado original/duplicado por intento. Esta conciliación solo **consume** ese marcado; el reporte y el resumen diario siguen siendo propiedad de este cambio.
- La HU indica que las herramientas de conciliación se definirán durante la implementación.
- Esta conciliación **consume** estados y referencias de otros cambios sin redefinirlos: estados terminales y referencia de `payer-low-value-payment-confirmation`, conjunto de estados MVP de `merchant-qr-payment-status-visibility` (OQ-24) y marcado de `payment-idempotency`. Terminología: [GLOSSARY.md](../../../docs/GLOSSARY.md).

## Goals / Non-Goals

**Goals:**

- Definir un modelo conceptual de conciliación diaria con tres fuentes: intención de pago, asiento de ledger y resultado del proveedor.
- Registrar descalces con referencia, tipo y estado de investigación, y exponerlos en reportes filtrables por fecha y canal.
- Producir un resumen diario de conciliados, no conciliados y resueltos.
- Distinguir en el reporte y el resumen los intentos originales de los reintentos duplicados, consumiendo el marcado de `payment-idempotency`.

**Non-Goals:**

- Definir o generar el marcado original/duplicado, la clave de idempotencia o el registro de auditoría de duplicados (propiedad de `payment-idempotency-protection`).
- Elegir herramientas, lenguaje, almacenamiento o scheduler (se decide en implementación).
- Corregir descalces automáticamente, ejecutar reversos o gestionar disputas.
- Definir el umbral máximo de descalce aceptable (pregunta abierta de la HU).
- Cubrir paridad total con todos los proveedores/bancos desde el día uno.

## Decisions

1. **Conciliación por lotes diarios, por canal de proveedor.** Se concilia un día calendario a la vez y por canal, lo que facilita el filtrado por fecha/canal y evita asumir un único riel. Alternativa descartada: conciliación en tiempo real, no pedida por la HU (se trata de salida *diaria*).
2. **Referencia de transacción como clave de cruce.** Se asume una referencia común (o mapeable) entre wallet y proveedor; su formato lo define la implementación. Alternativa: cruce por monto/fecha, descartado por ambigüedad y riesgo de falsos positivos.
3. **Catálogo de tipos de descalce (supuesto de trabajo, OQ-36).** Tipos mínimos ilustrativos: registro de wallet sin resultado del proveedor, resultado del proveedor sin registro de wallet, intención de pago exitosa sin asiento de ledger, y diferencia en datos comparados (p. ej. monto, o estado terminal de wallet distinto del resultado del proveedor, como un intento `expirado` en wallet confirmado después por el proveedor; ver OQ-10). El catálogo final se confirma con operaciones; la HU no lo enumera.
4. **Estados de investigación (supuesto de trabajo, OQ-36).** Se requiere al menos un estado inicial pendiente y un estado "resuelto" (necesario para el total de resueltos). Estados intermedios quedan a definir. Su relación con el estado de resolución de las acciones de soporte (`payment-failure-reversal-handling`) está en OQ-33.
5. **Resumen derivado del mismo conjunto de datos que el reporte**, para que totales y detalle sean consistentes bajo los mismos filtros.
6. **Sin evaluación de umbral.** El resumen solo informa totales; la comparación contra una tasa aceptable queda diferida hasta responder la pregunta abierta.
7. **Consumo del marcado original/duplicado, sin propiedad.** La conciliación lee el atributo de origen (con vínculo al intento original) que expone `payment-idempotency` y lo muestra en el reporte y el resumen; no lo recalcula, no lo infiere por heurísticas (monto/fecha) y no accede a la clave de idempotencia más allá del vínculo. Alternativa descartada: que conciliación detecte duplicados por sí misma (duplicaría y podría divergir del contrato de idempotencia). Un registro sin marcado se muestra como "sin marcado de origen" en lugar de asumirse original.
8. **Duplicados fuera del cruce y del total de transacciones.** Un reintento duplicado no es una transacción financiera adicional, por lo que no se cruza contra el proveedor ni cuenta en conciliados/no conciliados/resueltos; se lista en el reporte vinculado a su original y el resumen informa un total separado de reintentos duplicados, derivado del mismo conjunto de datos y filtros (decisión 5). Si se hallaran varias transacciones financieras asociadas a un mismo intento original, se trataría como descalce (tipo a confirmar en el catálogo, decisión 3).

## Risks / Trade-offs

- **Estados asíncronos**: un registro aún pendiente en el proveedor puede aparecer como descalce falso. Mitigación a definir (ventana de corte/espera, OQ-35); no se fija aquí porque no está en la HU.
- **Duplicidad por reintentos sin idempotencia**: puede producir descalces de más de un registro por intención. La prevención y el marcado dependen de `payment-idempotency`; esta conciliación solo los consume y los hace visibles. Si el marcado no está disponible o llega incompleto, los reintentos podrían confundirse con transacciones adicionales (mitigación: mostrar "sin marcado de origen", decisión 7).
- **Dependencia de terceros**: formatos y disponibilidad de los resultados del proveedor varían por canal; la paridad completa es no-objetivo.
- **Umbral indefinido**: sin tasa máxima aceptable no hay criterio objetivo de preparación para lanzamiento; se mantiene como pregunta abierta.
- **Supuestos sobre tipos y estados** (decisiones 3 y 4) pueden requerir ajustes al validarlos con operaciones.

## Open Questions

Registro único: [OPEN-QUESTIONS.md](../../../docs/OPEN-QUESTIONS.md). No se responden aquí.

- OQ-34: ¿cuál es la tasa máxima diaria de descalce aceptable para la preparación del lanzamiento del MVP? (de la HU; sin respuesta aquí.)
- OQ-35: hora de corte y zona horaria del día conciliado, y tratamiento de estados asíncronos pendientes.
- OQ-36: catálogo definitivo de tipos de descalce y estados de investigación.
- OQ-37: regla de conteo de "resueltos" frente a "no conciliados" en el resumen.
- OQ-09: canales exactos del MVP y referencia de transacción común para el cruce.
- OQ-14: forma exacta de exponer el marcado original/duplicado y día al que se asigna un reintento duplicado cuya solicitud original cae en otro día (a acordar con `payment-idempotency-protection`).
- OQ-24: conjunto de estados del comercio que la conciliación debe comparar.
- OQ-33: relación entre estado de investigación de descalce y estado de resolución de soporte.
