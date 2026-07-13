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
- T-21 → **No implementada** (Tracer Bullet `client_scaffold`; pasos 1-10 del flujo completados en rama `feature/client_scaffold`, incl. bucle TDD; restan pasos 11-13)
- T-22 → **Implementada** (bucle TDD de `client_scaffold`: 13/13 casos `refactored`, suite 39 passed)
- T-23 → **No implementada** (paso 11: prueba de integración TSK-25 sobre `zlk client new` por subprocess, requiere `.venv`/Python 3.13)
- T-24 → **Implementada** (renombrado a inglés de los 3 YAML de `input/`: `contract_data.yaml`, `business_rules.yaml`, `finance.yaml`)
- T-25 → **Implementada** (TSK-24: entorno `.venv` con Python 3.13 y tenant real `clients/COMPANY_DEMO` creado por la vía oficial)

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
| T-21 | Construir Tracer Bullet `client_scaffold` (artefactos SDD+TDD completos: `feature_contract.md`, notebook, spec, plan, `state.json`, tests, código) | No implementada | 2026-07-12 | pasos 1-10 del flujo completados en rama `feature/client_scaffold`: `feature_contract.md`, `definition.md` (8 HU), `client_scaffold.ipynb`, `spec.md` (10 CA), `plan.md` (27 TSK, 13 casos), `state.json` (`stages.tdd.status="done"`, 13/13 casos `refactored`); pendientes pasos 11-13 (`integration_tester`, `spec_verifier`, `human_test`, `merge_to_main`); es la continuación de T-12 |
| T-22 | Bucle TDD del Tracer Bullet `client_scaffold`: ejecutar `tdd_tester`/`tdd_coder`/`tdd_refactor` sobre los 13 casos de `plan.md`/`state.json`, produciendo código en `app/src/zeroleak/core/scaffold.py` y tests en `app/tests/` | Implementada | 2026-07-13 | 13/13 casos `refactored`; código de producción en `app/src/zeroleak/core/scaffold.py` y `app/src/zeroleak/cli.py`; tests en `app/tests/conftest.py`, `test_scaffold.py`, `test_cli_client_new.py`; suite completa 39 passed; TSK-01…TSK-24, TSK-26, TSK-27 → Implementada; solo resta TSK-25 (integración) |
| T-23 | Paso 11 del flujo: prueba de integración TSK-25 (`integration_tester`) sobre `zlk client new` ejecutado por subprocess | No implementada | 2026-07-13 | siguiente paso inmediato al retomar; requiere correr dentro del `.venv`/Python 3.13 (`requires-python>=3.13` en `pyproject.toml`) |
| T-24 | Renombrar a inglés los 3 YAML de `input/` del tenant (`contract_data.yaml`, `business_rules.yaml`, `finance.yaml`) | Implementada | 2026-07-13 | ajuste dirigido por el humano, posterior al cierre del bucle TDD; propagado a `scaffold.py`, tests, `spec.md`, `plan.md`, `state.json`, notebook, `system_design.md` y tenant `COMPANY_DEMO`; prosa en español sin cambios |
| T-25 | TSK-24 (humano): crear entorno con Python 3.13 y generar el tenant real `clients/COMPANY_DEMO` por la vía oficial | Implementada | 2026-07-13 | creado `.venv/` en la raíz del repo con `py -3.13`, `pip install -e ".[dev]"`; tenant generado con `zlk client new COMPANY_DEMO`; versionados `client.yaml` + `input/` (data/ gitignored por C-01); stageado, commit en el cierre de sesión |
