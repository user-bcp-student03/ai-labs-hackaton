---
name: python-clean-architecture
description: 'Diseña, analiza o refactoriza aplicaciones Python aplicando Clean Architecture. Úsala para definir límites de capas, dependencias, casos de uso, puertos y adaptadores, o para revisar una arquitectura existente sin asumir requisitos faltantes.'
---

# Skill: Clean Architecture para Python

## 1) Metadata
- **Skill ID:** python-clean-architecture
- **Version:** 0.1.0
- **Purpose:** Producir una propuesta o revisión arquitectónica clara y verificable para aplicaciones Python, preservando el comportamiento y evitando complejidad innecesaria.
- **Audience (roles):** Tech Lead, Backend, QA, arquitectura.
- **When to use:** Al iniciar un servicio o funcionalidad Python, revisar límites de módulos, planear una refactorización o evaluar si una implementación respeta Clean Architecture.
- **When NOT to use:** Para cambios triviales que no alteran límites ni responsabilidades, o para reemplazar un análisis funcional, de seguridad o de rendimiento especializado.
- **Sensitive inputs:** No incluyas datos personales reales, credenciales, secretos, tokens ni URLs internas no autorizadas.
- **Expected output:** Un documento Markdown con la estructura indicada en la sección Output.

## 2) Inputs
Solicita o utiliza la información disponible con este formato:

- **Business context (brief):** problema o necesidad que motiva el cambio.
- **Feature request / user story:** comportamiento que debe soportar el sistema.
- **Expected impact:** resultado esperado, si existe.
- **Scope (in/out):** módulos, funcionalidades y límites afectados.
- **Known technical constraints:** versión de Python, framework, persistencia, integraciones y convenciones obligatorias.
- **Known risks:** compatibilidad, seguridad, concurrencia, disponibilidad, rendimiento y riesgos de migración.
- **Dependencies:** servicios externos, librerías existentes, equipos y módulos relacionados.
- **Team Definition of Done (DoD):** pruebas, documentación, revisión y evidencia requeridas.
- **Current architecture (if available):** estructura de carpetas, flujo actual y responsabilidades conocidas.

Si falta información que cambie las decisiones de diseño, no la inventes: registra la pregunta en **Preguntas abiertas** y presenta como provisional cualquier recomendación afectada. Si la respuesta es necesaria para evitar una decisión irreversible, pregunta al usuario antes de continuar.

## 3) Output
Devuelve Markdown conciso, siguiendo estas secciones:

1. **Summary**
2. **Scope**
   - Dentro del alcance
   - Fuera del alcance
3. **Propuesta de arquitectura**
   - Capas y responsabilidades
   - Flujo de dependencias y datos
   - Puertos, adaptadores y composición de dependencias
4. **Decisiones técnicas**
   - Decisiones recomendadas
   - Alternativas relevantes y consecuencias
5. **Riesgos y mitigaciones**
6. **Acceptance criteria (measurable)**
7. **Plan de validación**
   - Pruebas unitarias de dominio y casos de uso
   - Pruebas de adaptadores e integración
   - Compatibilidad del contrato y regresión
   - Evidencia requerida
8. **Plan de implementación**
   - Pasos incrementales ordenados por dependencia
   - Migración y compatibilidad, cuando apliquen
9. **Preguntas abiertas**

Si el usuario solicita únicamente un diagnóstico o un resumen, conserva la misma numeración y deja fuera el detalle que no aplique, indicando brevemente por qué.

## 4) Constraints
- Aplica la regla de dependencias: el código de políticas internas no debe depender de frameworks, bases de datos, transporte HTTP ni detalles externos.
- Mantén el dominio y los casos de uso independientes de FastAPI, Django, Flask, ORM, SDKs y mecanismos de entrega; no impongas una estructura de carpetas si la escala del proyecto no la justifica.
- Modela necesidades externas mediante interfaces/protocolos definidos hacia el interior y adaptadores concretos hacia el exterior. Inyecta implementaciones en el punto de composición de la aplicación.
- Mantén una responsabilidad clara por módulo. Evita servicios genéricos, capas vacías, abstracciones especulativas y duplicación.
- Separa reglas de negocio, orquestación de casos de uso, transporte, persistencia y configuración cuando sus responsabilidades o motivos de cambio sean distintos.
- Conserva contratos, endpoints y comportamiento existente salvo que el alcance aprobado indique lo contrario; identifica los cambios incompatibles antes de proponerlos.
- No inventes requisitos, mediciones, estructura existente ni restricciones. Declara supuestos explícitamente y lleva las incógnitas a **Preguntas abiertas**.
- No agregues dependencias, patrones, capas o migraciones sin justificar el beneficio y el costo.
- No introduzcas secretos ni recomiendes registrar credenciales, tokens o datos sensibles.
- Mantén la propuesta incremental, comprobable y proporcional al tamaño del sistema.

## 5) Validation Rules
La propuesta es válida si:
- Identifica responsabilidades y límites de las capas relevantes para el alcance.
- Explica la dirección de las dependencias y muestra que los detalles externos dependen de abstracciones internas, no al revés.
- Describe cómo se componen las implementaciones concretas sin acoplar los casos de uso a un framework o proveedor.
- Incluye criterios de aceptación observables y un plan de pruebas por límite arquitectónico.
- Considera contratos y comportamiento existentes, así como riesgos de migración cuando corresponda.
- No presenta como hechos los datos faltantes ni incluye decisiones incompatibles con restricciones conocidas.
- Justifica cualquier abstracción o dependencia nueva y evita complejidad sin valor demostrado.

## 6) Evidence
Adjunta o referencia, cuando aplique:
- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Diagrama o mapa de dependencias actualizado, si el cambio altera límites.
- Resultados de pruebas y verificaciones de contratos ejecutadas; distingue claramente las pruebas propuestas de las realmente ejecutadas.
