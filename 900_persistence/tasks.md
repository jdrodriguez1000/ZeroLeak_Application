# Tasks — Tareas del Proyecto

Registro de las tareas realizadas y por realizar del proyecto.

**Estados posibles:**
- `Implementada` — la tarea fue completada.
- `No implementada` — la tarea está definida pero aún no se ejecuta.
- `Cancelada/Pendiente` — la tarea fue cancelada o queda en espera.

---

## Índice
<!-- Mantener actualizado. Resumen de tareas por ID y estado. -->
- T-01…T-09 → **Implementada** (bootstrap metodológico)
- T-10, T-12, T-13 → **No implementada** (agentes de desarrollo, primer feature, verificación de subagentes)
- T-11 → **No implementada** (estructura de código; alcance actualizado al diseño v0.2)
- T-14…T-16 → **Implementada** (limpieza de `700_architecture/` y diseño de arquitectura v0.2)

---

## Tareas

| ID | Tarea | Estado | Fecha | Notas |
|----|-------|--------|-------|-------|
| T-01 | Crear `900_persistence` con los 6 archivos (con índice) | Implementada | 2026-07-12 | |
| T-02 | Crear subagentes `session-starter` y `session-closer` | Implementada | 2026-07-12 | haiku/azul y sonnet/verde |
| T-03 | Crear `CLAUDE.md` con protocolos de inicio/cierre | Implementada | 2026-07-12 | |
| T-04 | Enlazar Git + GitHub (`.gitignore`, `.gitattributes`) | Implementada | 2026-07-12 | rama main, commits subidos |
| T-05 | Dejar `principles.md` agnóstico (sin FODA) | Implementada | 2026-07-12 | |
| T-06 | Analizar `Salud de datos.docx` | Implementada | 2026-07-12 | |
| T-07 | Definir flujo de 13 pasos (Opción A, sin bandas) | Implementada | 2026-07-12 | |
| T-08 | Alinear templates de `600_template/` (+`notebook.md`) | Implementada | 2026-07-12 | trazabilidad HU→CA→TSK→matriz |
| T-09 | Reescribir `methodology.md` para ZeroLeak | Implementada | 2026-07-12 | incl. "Datos en Bóveda" |
| T-10 | Crear los 9 agentes de desarrollo | No implementada | 2026-07-12 | feature_definer … spec_verifier |
| T-11 | Crear estructura de carpetas de código alineada a `system_design.md` v0.2 | No implementada | 2026-07-12 | `src/zeroleak/` (core/ingest/vault/modules/finance/report/llm), `clients/<CLIENTE>/input/` + `data/{bronze,silver,gold}/`, `config/sectors/`, `data_synthetic/`, `tests/`, `600_features/`; regla `.gitignore` `clients/*/data/` (reemplaza el `data_real/` global previsto) |
| T-12 | Definir el primer feature (Tracer Bullet) | No implementada | 2026-07-12 | ahora informado por `system_design.md` v0.2 |
| T-13 | Verificar registro de subagentes tras reiniciar Claude Code | No implementada | 2026-07-12 | el harness no los tomó esta sesión |
| T-14 | Eliminar de `700_architecture/` los artefactos ajenos (`system_design.md`, `sdd_tdd_workflow.md`) que pertenecían al proyecto FODA | Implementada | 2026-07-12 | archivos sin trackear, eliminados sin pérdida en git |
| T-15 | Releer `Salud de datos.docx` para aterrizar el dominio de ZeroLeak previo al diseño | Implementada | 2026-07-12 | insumo directo para `system_design.md` |
| T-16 | Crear `700_architecture/system_design.md` v0.2 propio de ZeroLeak | Implementada | 2026-07-12 | 16 secciones; incorpora decisiones D-06…D-11 |
