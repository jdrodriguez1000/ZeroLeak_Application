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
- T-10 → **Implementada** (9 agentes de desarrollo creados en `.claude/agents/`)
- T-12 → **No implementada** (primer Tracer Bullet `zlk client new`, desbloqueada; diseño acordado, continúa en T-21)
- T-13 → **No implementada** (verificación de registro de subagentes, evidencia parcial)
- T-11 → **Implementada** (esqueleto de código del motor, alineado al diseño v0.2)
- T-14…T-16 → **Implementada** (limpieza de `700_architecture/` y diseño de arquitectura v0.2)
- T-17, T-18 → **Implementada** (convención `610_features/` alineada en todo el repo; verificación de aislamiento C-01)
- T-19 → **Implementada** (revisión de D-05: excepciones de modelo para `feature-definer` y `notebook-writer`)
- T-20 → **Implementada** (refactor estructural: `config/`, `data_synthetic/`, `src/`, `tests/` movidos a `app/`)
- T-21 → **No implementada** (construir artefactos SDD+TDD completos del Tracer Bullet `client_scaffold`; solo se hizo el análisis/diseño)

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
| T-10 | Crear los 9 agentes de desarrollo | Implementada | 2026-07-12 | `.claude/agents/`: feature-definer.md, notebook-writer.md, spec-writer.md, plan-builder.md, tdd-tester.md, tdd-coder.md, tdd-refactor.md, integration-tester.md, spec-verifier.md; cada uno con frontmatter (name/description/tools/model/color); `spec-verifier` con sección de "mentalidad crítica" no negociable |
| T-11 | Crear estructura de carpetas de código alineada a `system_design.md` v0.2 | Implementada | 2026-07-12 | `pyproject.toml` (paquete `zeroleak`, comando `zlk`), `src/zeroleak/` (core/ingest/vault/modules{identity,structure,relational,category}/finance/report/llm), `.gitkeep` en `config/sectors/`, `data_synthetic/`, `tests/`; `.gitignore` con regla C-01 `clients/*/data/`; `README.md` del proyecto; verificado import de los 9 submódulos y `git check-ignore` sobre datos de cliente |
| T-12 | Construir el primer Tracer Bullet: `zlk client new <NOMBRE_CLIENTE>` (core `create_client()` en `app/src/zeroleak/core/scaffold.py`) | No implementada | 2026-07-12 | tenant de demostración: `COMPANY_DEMO`; requiere T-10 (agentes de desarrollo) primero; diseño/decisiones ya acordados con el humano (ver `progress.md`); construcción de artefactos continúa en T-21 |
| T-13 | Verificar registro de subagentes tras reiniciar Claude Code | No implementada | 2026-07-12 | evidencia parcial: los 9 agentes aparecieron como agent types disponibles en la sesión; falta confirmar persistencia tras reinicio completo |
| T-14 | Eliminar de `700_architecture/` los artefactos ajenos (`system_design.md`, `sdd_tdd_workflow.md`) que pertenecían al proyecto FODA | Implementada | 2026-07-12 | archivos sin trackear, eliminados sin pérdida en git |
| T-15 | Releer `Salud de datos.docx` para aterrizar el dominio de ZeroLeak previo al diseño | Implementada | 2026-07-12 | insumo directo para `system_design.md` |
| T-16 | Crear `700_architecture/system_design.md` v0.2 propio de ZeroLeak | Implementada | 2026-07-12 | 16 secciones; incorpora decisiones D-06…D-11 |
| T-17 | Adoptar convención `610_features/` (en vez de `600_features/`) y corregir referencias rezagadas | Implementada | 2026-07-12 | `610_features/README.md` creado; referencias corregidas en `methodology.md`, `tasks.md`, `system_design.md`; grep final sin rezagos |
| T-18 | Verificar aislamiento de datos de cliente (C-01) en el esqueleto del motor | Implementada | 2026-07-12 | `git check-ignore` confirma que `clients/*/data/` queda ignorado; carpeta de prueba `clients/` borrada tras verificar, sin tenants commiteados |
| T-19 | Revisar D-05 con excepciones de modelo para `feature-definer` (sonnet) y `notebook-writer` (opus) | Implementada | 2026-07-12 | actualizado `decisions.md` D-05 y apéndice de `905_guideline/methodology.md` |
| T-20 | Refactor estructural: mover `config/`, `data_synthetic/`, `src/`, `tests/` a `app/` | Implementada | 2026-07-12 | `git mv`; `clients/` permanece en raíz (D-15); actualizadas referencias en `pyproject.toml`, 9 agentes, templates, `README.md`, `610_features/README.md`, `methodology.md`, `system_design.md`; corregido bug de doble prefijo `app/app/tests/` en 10 lugares; verificado `import zeroleak` y `pytest testpaths: app/tests` |
| T-21 | Construir Tracer Bullet `client_scaffold` (artefactos SDD+TDD completos: `feature_contract.md`, notebook, spec, plan, `state.json`, tests, código) | No implementada | 2026-07-12 | diseño ya acordado con el humano (ver `decisions.md` D-15/notas T-12); confirmado nombre/ubicación `610_features/client_scaffold/` y formato de `state.json` (sin campo `band`, con las 13 etapas del flujo); pendiente crear la carpeta del feature, la rama `feature/1` y ejecutar el flujo de 13 pasos; es la continuación de T-12 |
