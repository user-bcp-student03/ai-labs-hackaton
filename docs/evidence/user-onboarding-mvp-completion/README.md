# Evidencias: `user-onboarding-mvp-completion` (HU-ONB, issue #28)

Diseño de referencia: [user-onboarding-mvp-completion-impact.md](../../architecture/user-onboarding-mvp-completion-impact.md). Cambio OpenSpec: `openspec/changes/user-onboarding-mvp-completion/`.

| Archivo | Contenido esperado | Responsable |
|---|---|---|
| `qe-test-evidence.md` | API: pruebas escritas antes de implementar y resultados por tarea 1.7 a 7.1 (pytest con SQLite real), 52 pruebas de HU-IDEM en verde antes y después, cobertura del código nuevo (meta 85% o más). Web: resultados de `ng test` por componente, servicio y guard; lista de accesibilidad WCAG 2.2 AA (teclado, foco, `aria-live`, 320 px, zoom 200%, contraste, lector de pantalla) y recorrido manual 7.1 contra la API real, con pasos «ejemplo no aprobado». Marca explícita de 6.2 (bloqueada por OQ-22) y 5.3 (pendiente de OQ-20) | QE |
| `implementation-log.md` | Tareas 2.1 a 7.1 realizadas (API y web) con commits y desviaciones del diseño; versiones de Angular y Node elegidas y verificadas; acuerdos de las tareas 1.1 a 1.6 (OQ-05, OQ-06, OQ-07, OQ-20 a OQ-23) y respuestas a Q-1 a Q-12 del diseño; estado de 6.2 | Desarrollo (API y web) |
| `security-risk-analysis.md` | Revisión de consultas parametrizadas, propiedad por `user_id`, validación y tamaños de entrada, patrones de configuración (ReDoS), mensajes sin eco de valores, token de analítica, ausencia de datos personales persistidos y en logs, datos `TEST-`, `X-Payer-Id` provisional, `angular-eslint` y dependencias de `web/`, riesgos R-1 a R-13 | Seguridad |

Acuerdos humanos que condicionan el cierre (se registran en `implementation-log.md`): Cumplimiento (pasos reales de KYC, 1.1), Analítica y Producto (frontera de duración OQ-20, cierre y cohorte OQ-21 y OQ-06, glosario OQ-05, estados de wallet OQ-23, fuente de gasto OQ-22, responsable del reporte consolidado OQ-07).

Los archivos se crean cuando existan los resultados; no se inventan evidencias.
