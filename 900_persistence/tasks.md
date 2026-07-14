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
- T-21 → **Implementada** (Tracer Bullet `client_scaffold` CERRADO: 13/13 pasos del flujo, mergeado a `main` vía PR #1)
- T-22 → **Implementada** (bucle TDD de `client_scaffold`: 13/13 casos `refactored`, suite 39 passed)
- T-23 → **Implementada** (paso 11: prueba de integración TSK-25 sobre `zlk client new` por subprocess, suite 43 passed)
- T-24 → **Implementada** (renombrado a inglés de los 3 YAML de `input/`: `contract_data.yaml`, `business_rules.yaml`, `finance.yaml`)
- T-25 → **Implementada** (TSK-24: entorno `.venv` con Python 3.13 y tenant real `clients/COMPANY_DEMO` creado por la vía oficial)
- T-26 → **Implementada** (paso 12: verificación `spec_verifier`, veredicto CONFORME, `verification.md`; paso 13: PR #1 aprobado y mergeado por el humano)
- T-27 → **Implementada** (actualización de `README.md`: secciones "Entorno de desarrollo" y "Uso del CLI")
- T-28 → **No implementada** (segundo Tracer Bullet `ingest`; en curso — pasos 1-10 del flujo completos; falta paso 11 en adelante)
- T-29 → **Implementada** (paso 3 del Tracer Bullet `ingest`: `feature_definer` produjo `610_features/ingest/definition.md` con 8 HU)
- T-30 → **Implementada** (paso 4: `notebook_writer` produjo `ingest.ipynb`; ejecutado in-place por la sesión principal con `nbconvert`/`ipykernel`)
- T-31 → **Implementada** (paso 5: gate humano del notebook aprobado, 3 decisiones ratificadas: sufijo `__<sha8>`, exit codes 0/1/2, duplicate=SKIP)
- T-32 → **Implementada** (paso 6: `spec_writer` produjo `spec.md` con 12 CA-01…CA-12)
- T-33 → **Implementada** (paso 7: gate humano de la spec aprobado, 3 defaults ratificados: extensiones case-insensitive, manifest de 4 campos, `ingested_at` timespec segundos)
- T-34 → **Implementada** (paso 8: `plan_builder` produjo `plan.md` con 27 TSK y 12 casos)
- T-35 → **Implementada** (paso 9: gate humano del plan aprobado)
- T-36 → **Implementada** (paso 10, bucle TDD de `ingest` CERRADO: 12/12 casos, `stages.tdd.status="done"`, suite 64 passed)
- T-37 → **No implementada** (pasos 11-13 del flujo `ingest`: integración e2e TSK-25, `spec_verifier`, gate humano final, PR a `main`)

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
| T-21 | Construir Tracer Bullet `client_scaffold` (artefactos SDD+TDD completos: `feature_contract.md`, notebook, spec, plan, `state.json`, tests, código) | Implementada | 2026-07-13 | 13/13 pasos del flujo completados: `feature_contract.md`, `definition.md` (8 HU), `client_scaffold.ipynb`, `spec.md` (10 CA), `plan.md` (27 TSK, 13 casos), `state.json`, integración e2e (TSK-25), `verification.md` (CONFORME), PR #1 aprobado y mergeado por el humano a `main`; es la continuación de T-12 |
| T-22 | Bucle TDD del Tracer Bullet `client_scaffold`: ejecutar `tdd_tester`/`tdd_coder`/`tdd_refactor` sobre los 13 casos de `plan.md`/`state.json`, produciendo código en `app/src/zeroleak/core/scaffold.py` y tests en `app/tests/` | Implementada | 2026-07-13 | 13/13 casos `refactored`; código de producción en `app/src/zeroleak/core/scaffold.py` y `app/src/zeroleak/cli.py`; tests en `app/tests/conftest.py`, `test_scaffold.py`, `test_cli_client_new.py`; suite completa 39 passed; TSK-01…TSK-24, TSK-26, TSK-27 → Implementada; solo resta TSK-25 (integración) |
| T-23 | Paso 11 del flujo: prueba de integración TSK-25 (`integration_tester`) sobre `zlk client new` ejecutado por subprocess | Implementada | 2026-07-13 | creado `app/tests/integration/test_client_new_e2e.py`, ejecutado dentro del `.venv`/Python 3.13; suite total 43 passed; cubre CA-01..CA-08; TSK-25 marcada implementada en `plan.md` |
| T-24 | Renombrar a inglés los 3 YAML de `input/` del tenant (`contract_data.yaml`, `business_rules.yaml`, `finance.yaml`) | Implementada | 2026-07-13 | ajuste dirigido por el humano, posterior al cierre del bucle TDD; propagado a `scaffold.py`, tests, `spec.md`, `plan.md`, `state.json`, notebook, `system_design.md` y tenant `COMPANY_DEMO`; prosa en español sin cambios |
| T-25 | TSK-24 (humano): crear entorno con Python 3.13 y generar el tenant real `clients/COMPANY_DEMO` por la vía oficial | Implementada | 2026-07-13 | creado `.venv/` en la raíz del repo con `py -3.13`, `pip install -e ".[dev]"`; tenant generado con `zlk client new COMPANY_DEMO`; versionados `client.yaml` + `input/` (data/ gitignored por C-01); stageado, commit en el cierre de sesión |
| T-26 | Paso 12 (`spec_verifier`, `verification.md`) y paso 13 (gate humano `human_test` + `merge_to_main`) del Tracer Bullet `client_scaffold` | Implementada | 2026-07-13 | `spec_verifier` auditó los 10 CA con evidencia real y C-01 verificada, veredicto CONFORME (`610_features/client_scaffold/verification.md`); el humano aprobó y mergeó el PR #1 (`feature/client_scaffold`→`main`) en GitHub; `main` local sincronizado |
| T-27 | Actualizar `README.md` con secciones "Entorno de desarrollo" y "Uso del CLI", y corregir nota obsoleta sobre `zlk client new` | Implementada | 2026-07-13 | instrucciones de `.venv`/Python 3.13, `pip install -e ".[dev]"`, correr tests; comando `zlk client new`, patrón de nombres, tabla de exit codes 0/1/2/3; commit de cierre de sesión sobre `main` (actualización de documentación, no una feature) |
| T-28 | Construir el segundo Tracer Bullet: `zlk ingest <CLIENTE> <ruta>` (registro de archivos en capa bronze del tenant, dedupe por `sha256`) | No implementada | 2026-07-14 | alcance acordado con el humano (ver D-17): copia inmutable a bronze, hash sha256, entrada en `manifest.json` status `pending`, dedupe habilita Modo Incremental; no parsea contenido ("archivador notarial"); validación agnóstica de formato; allow-list MVP `.csv`/`.xlsx` (`.txt` fuera); entrada por archivo o carpeta con recorrido plano; **pasos 1-10 completos** (bucle TDD 12/12 casos, código en `app/src/zeroleak/ingest/core.py` y `cli.py`, suite 64 passed); falta paso 11 en adelante; continúa en T-36/T-37 |
| T-29 | Paso 3 del flujo `ingest`: invocar `feature_definer` para producir `610_features/ingest/definition.md` (historias HU-xx) a partir de `feature_contract.md` | Implementada | 2026-07-13 | producidas 8 historias HU-01…HU-08; decisión humana zanjada reflejada en HU-05: procesamiento parcial por ruta con reporte de éxitos/fallos, tenant inexistente como precondición global que aborta toda la invocación |
| T-30 | Paso 4 del flujo `ingest`: invocar `notebook_writer` para producir `610_features/ingest/ingest.ipynb` (spike con datos sintéticos) | Implementada | 2026-07-13 | el agente no pudo ejecutar el notebook (sin kernel); la sesión principal instaló `nbconvert`+`ipykernel` en el `.venv` del proyecto y ejecutó el notebook in-place, demostrando las 8 HU con evidencia visible |
| T-31 | Paso 5 del flujo `ingest`: gate humano sobre el notebook | Implementada | 2026-07-13 | notebook **APROBADO**; 3 decisiones ratificadas: (a) nombrado en bronze ante colisión de nombre con sufijo `__<sha8>`; (b) exit codes 0=éxito total/1=parcial o fallo por ruta/2=fallo global por tenant; (c) `duplicate` = no-op idempotente (SKIP), no cuenta como fallo |
| T-32 | Paso 6 del flujo `ingest`: invocar `spec_writer` para producir `610_features/ingest/spec.md` | Implementada | 2026-07-13 | producidos 12 criterios CA-01…CA-12, trazables a las 8 HU |
| T-33 | Paso 7 del flujo `ingest`: gate humano sobre la spec | Implementada | 2026-07-13 | spec **APROBADA**; 3 defaults ratificados: extensiones case-insensitive; manifest con solo `file`/`sha256`/`ingested_at`/`status` (ausencia verificable de `period`/`run_id`/`output`); `ingested_at` con `timespec` de segundos |
| T-34 | Paso 8 del flujo `ingest`: invocar `plan_builder` para producir `610_features/ingest/plan.md` | Implementada | 2026-07-13 | producidas 27 tareas TSK-01…TSK-27 y 12 casos de test, todos los CA cubiertos |
| T-35 | Paso 9 del flujo `ingest`: gate humano sobre el plan | Implementada | 2026-07-13 | plan **APROBADO**; creado `610_features/ingest/state.json` siguiendo el patrón de `client_scaffold` |
| T-36 | Paso 10 del flujo `ingest`: bucle TDD sobre los 12 casos de `plan.md`/`state.json` | Implementada | 2026-07-14 | **12/12 casos cerrados**, `stages.tdd.status="done"` en `state.json`. Bloque 1 (caso 1) y bloque 2 (casos 2-5) cerrados el 2026-07-13: Caso 1 CA-08 (tenant inexistente→`TenantNotFoundError`/exit 2), Caso 2 CA-01 (ingesta csv byte-a-byte+entrada pending), Caso 3 CA-02 (forma del manifest, caracterización: TSK-06 implementada, TSK-07 cancelada_suspendida), Caso 4 CA-09 (archivo vacío→fallo/exit 1), Caso 5 CA-05 (dedupe sha256→SKIP/exit 0, incl. intra-invocación). Bloque 3 (casos 6-9) y bloque 4 (casos 10-12) cerrados el 2026-07-14: Caso 6 CA-06 (colisión de nombre→sufijo `__<sha8>`, helper `_resolve_destination`), Caso 7 CA-03 (recorrido plano de carpeta, helper `_expand_paths`), Caso 8 CA-04 (argumentos mezclados, caracterización, TSK-17 cancelada_suspendida), Caso 9 CA-10 (delimitadores sin parseo, caracterización, TSK-19 cancelada_suspendida), Caso 10 CA-07 (procesamiento parcial: "la ruta no existe"/"extensión fuera de allow-list", refactor integral del core, TSK-26 implementada parcial), Caso 11 CA-11 (frontera `.gitignore` vía `git check-ignore`, caracterización), Caso 12 CA-12 (fachada CLI `zlk ingest`, TSK-27 implementada). Código en `app/src/zeroleak/ingest/core.py`, `__init__.py` y `app/src/zeroleak/cli.py`; tests en `app/tests/test_ingest.py` (ampliado) y `app/tests/test_cli_ingest.py` (nuevo); fixtures en `app/tests/conftest.py`. Suite total: 64 passed, sin regresiones |
| T-37 | Pasos 11-13 del flujo `ingest`: integración e2e (TSK-25, `integration_tester` sobre `zlk ingest` por subprocess), `spec_verifier` (`verification.md`), gate humano final (`human_test`) y PR hacia `main` (`merge_to_main`) | No implementada | 2026-07-14 | pendiente para la próxima sesión; continúa T-28 tras el cierre del bucle TDD (T-36) |
