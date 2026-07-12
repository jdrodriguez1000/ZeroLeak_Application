# Progress — Avance del Proyecto

Este archivo registra el avance del proyecto: lo realizado y lo próximo a realizar.
Consultándolo siempre sabemos el estado y avance actual del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por entrada registrada. -->
- [2026-07-12] Bootstrap del proyecto: persistencia, agentes de sesión, Git/GitHub, metodología y templates SDD+TDD.
- [2026-07-12] Diseño de arquitectura: `700_architecture/system_design.md` v0.2 de ZeroLeak (limpieza de artefactos de FODA, esquema Medallion por tenant, Data Health Score dual, mapa de costuras a SaaS).
- [2026-07-12] T-11 completada: esqueleto del motor (`pyproject.toml`, `src/zeroleak/` con 9 submódulos, `.gitignore` C-01, verificación de aislamiento de datos de cliente) y convención `610_features/` alineada en todo el repo.
- [2026-07-12] T-10 completada: creados los 9 agentes de desarrollo en `.claude/agents/` (feature-definer, notebook-writer, spec-writer, plan-builder, tdd-tester, tdd-coder, tdd-refactor, integration-tester, spec-verifier); revisión de D-05 (excepciones de modelo) y `spec_verifier` con mentalidad crítica no negociable.
- [2026-07-12] Refactor estructural a carpeta `app/` (config/data_synthetic/src/tests movidos, `clients/` permanece en raíz) y análisis (sin artefactos) del Tracer Bullet `client_scaffold` (T-12).
- [2026-07-12] Confirmado nombre/ubicación del primer feature (`610_features/client_scaffold/`) y aclarado el formato de `state.json` sin campo `band`, alineado a las 13 etapas del flujo (T-21, aún sin artefactos creados).

---

## Estado actual
El proyecto **ZeroLeak** avanzó de diseño de arquitectura y esqueleto de código a **agentes de desarrollo
listos**, y ahora el código fue reubicado bajo una carpeta `app/` dedicada. Ya está definida la
metodología de desarrollo (Notebook → SDD+TDD, Opción A sin bandas), los templates de artefactos de
feature, los protocolos de sesión, el enlace a GitHub, el **diseño de arquitectura del motor**
(`700_architecture/system_design.md` v0.2), el **esqueleto de código Python** (`pyproject.toml` con
comando `zlk`, paquete `zeroleak` en `app/src/` con submódulos `core/ingest/vault/modules/finance/report/
llm`) con el aislamiento C-01 verificado vía `.gitignore` sobre `clients/*/data/`, la convención
`610_features/` (en vez de `600_features/`), y los **9 agentes de desarrollo** creados en
`.claude/agents/` (feature-definer, notebook-writer, spec-writer, plan-builder, tdd-tester, tdd-coder,
tdd-refactor, integration-tester, spec-verifier), cada uno con su modelo/color asignado según D-05 (y sus
dos excepciones explícitas). Se decidió que los tenants de cliente se generarán dinámicamente con el
comando `zlk client new` (patrón heredado de FODA), en vez de crearse a mano o commitearse. El tenant de
demostración se llamará `COMPANY_DEMO`. Se realizó el **refactor a `app/`** (D-15): `config/`,
`data_synthetic/`, `src/` y `tests/` ahora viven en `app/`, mientras `clients/` permanece en la raíz del
repo (data de runtime del tenant, fuera del código empaquetado); todas las referencias del repo
(`pyproject.toml`, agentes, templates, `README.md`, `system_design.md`, `methodology.md`) quedaron
alineadas y verificadas (`import zeroleak` OK, `pytest` resuelve `app/tests`). También se analizó (sin
crear artefactos aún) el diseño del primer Tracer Bullet `client_scaffold` (T-12): comando `zlk client new
<NOMBRE_CLIENTE>`, core `create_client(name, clients_root) -> Path` en `app/src/zeroleak/core/scaffold.py`,
alcance mínimo (solo estructura del tenant, sin datos sintéticos ni plantillas YAML), sin idempotencia por
`--force`, con validación estricta de nombre. Falta verificar que los 9 agentes queden registrados como
subagentes invocables tras reiniciar Claude Code (T-13) y construir el Tracer Bullet `client_scaffold`
(T-12) con sus artefactos SDD+TDD completos. Se ejecutó el protocolo de inicio de sesión, confirmando que
el bootstrap metodológico/arquitectónico está completo y que la tarea prioritaria es **T-21**: construir
el feature `client_scaffold` en `610_features/client_scaffold/` (código en
`app/src/zeroleak/core/scaffold.py`, tests en `app/tests/`). Se resolvió una duda del humano sobre el
`state.json` de cada feature: comparando con el `state.json` del proyecto hermano FODA (que usa campo
`band`), se confirmó que en ZeroLeak cada feature tendrá su propio `state.json` en
`610_features/<feature>/state.json`, **sin campo `band`** (D-01, Opción A) y con las etapas del flujo de
13 pasos (incluye `feature_contract` con owner `main_session`, `notebook_writer`, `human_test`,
`merge_to_main`, que no existían en FODA), conservando la granularidad de evidencia TDD (`red_evidence`,
`green_evidence`, `refactor_note`, `cases[]`). Aún no se creó la carpeta del feature ni la rama
`feature/1`; queda pendiente para la próxima sesión.

## Lo realizado
- **[2026-07-12]** Creada carpeta `900_persistence` con los 6 archivos de persistencia (con índice cada uno).
- **[2026-07-12]** Creados subagentes `session-starter` (haiku/azul) y `session-closer` (sonnet/verde, con Bash).
- **[2026-07-12]** Creado `CLAUDE.md` con protocolos obligatorios de inicio/cierre de sesión y control de versiones.
- **[2026-07-12]** Enlazado Git a GitHub (rama `main`), con `.gitignore` y `.gitattributes`; commits iniciales subidos.
- **[2026-07-12]** `905_guideline/principles.md` dejado agnóstico (sin referencias a FODA).
- **[2026-07-12]** Analizado el documento fuente `980_documents/Salud de datos.docx`.
- **[2026-07-12]** Definido el flujo de desarrollo de **13 pasos** (Notebook → SDD+TDD, **Opción A sin bandas**).
- **[2026-07-12]** Alineados los templates de `600_template/` (incluye `notebook.md` nuevo); trazabilidad HU→CA→TSK→matriz.
- **[2026-07-12]** Reescrita `905_guideline/methodology.md` completa para ZeroLeak (incl. sección de seguridad "Datos en Bóveda").
- **[2026-07-12]** Detectado y **eliminado** contenido de `700_architecture/` (`system_design.md` y `sdd_tdd_workflow.md`) que pertenecía al proyecto hermano FODA, no a ZeroLeak.
- **[2026-07-12]** Releído el documento fuente `980_documents/Salud de datos.docx` para aterrizar el dominio de ZeroLeak (4 categorías de error, modelo de 4 YAMLs, traducción financiera, Data Health Score, Data ROI Dashboard).
- **[2026-07-12]** Creado `700_architecture/system_design.md` v0.2 propio de ZeroLeak (16 secciones): principio rector Servicio→SaaS, dominio, esquema de datos Medallion por tenant, manifiesto de procesamiento, RBAC futuro, alcance MVP (Retail Moderno, caso guía sanduchería).
- **[2026-07-12]** Acordadas con el humano las decisiones de diseño de la arquitectura (ver `decisions.md` D-06…D-11): alcance motor-local-con-mapa-a-SaaS, Data Health Score dual, caso guía sanduchería, esquema Medallion por tenant, manifiesto de procesamiento, rename `config/`→`input/`.
- **[2026-07-12]** **T-11 completada:** creado `pyproject.toml` (paquete `zeroleak`, comando de consola `zlk`, Python 3.13+, hatchling, src-layout, pytest configurado); creado `src/zeroleak/` con `__init__.py`, `cli.py` (placeholder) y submódulos `core/ingest/vault/modules/{identity,structure,relational,category}/finance/report/llm` con docstrings referenciando su sección de `system_design.md`; creados `.gitkeep` en `config/sectors/`, `data_synthetic/`, `tests/`; creado `README.md` del proyecto; `.gitignore` ampliado con sección Python y la regla C-01 `clients/*/data/`. Verificado: import OK de los 9 submódulos y `git check-ignore` confirma el aislamiento de datos de cliente (C-01 blindado); no quedaron tenants commiteados.
- **[2026-07-12]** Adoptada la convención `610_features/` (en vez de `600_features/`, para no colisionar con `600_template/`); creado `610_features/README.md` y corregidas todas las referencias rezagadas a `600_features` en `methodology.md`, `tasks.md` y `system_design.md`.
- **[2026-07-12]** Decidido con el humano (ver `decisions.md` D-12…D-14): el comando de consola es `zlk` (paquete `zeroleak`); los tenants de cliente se generan dinámicamente con `zlk client new` (core `create_client()` en `src/zeroleak/core/scaffold.py`, patrón heredado de FODA) y no se commitean ni crean a mano; el tenant de demostración se llama `COMPANY_DEMO`.
- **[2026-07-12]** **T-10 completada:** creados los 9 agentes de desarrollo en `.claude/agents/` (`feature-definer.md`, `notebook-writer.md`, `spec-writer.md`, `plan-builder.md`, `tdd-tester.md`, `tdd-coder.md`, `tdd-refactor.md`, `integration-tester.md`, `spec-verifier.md`), cada uno con frontmatter (name, description, tools, model, color) y cuerpo alineado al flujo de 13 pasos, las plantillas de `600_template/`, "Datos en Bóveda" y la trazabilidad HU→CA→TSK. Modelos: `feature-definer` (sonnet, verde) y `notebook-writer` (opus, cyan) como excepciones explícitas a D-05, decididas por el humano; `spec-writer`/`plan-builder`/`spec-verifier` en opus; `tdd-tester`/`tdd-coder`/`tdd-refactor`/`integration-tester` en sonnet. `spec-verifier` recibió una sección de "mentalidad crítica" no negociable (escéptico por defecto, ejecuta y lee la evidencia él mismo, un CA-xx sin evidencia basta para NO CONFORME). Se actualizó D-05 (revisión) y el apéndice de selección de modelos en `905_guideline/methodology.md`. Los 9 agentes aparecieron como agent types disponibles en la sesión (evidencia parcial de T-13).
- **[2026-07-12]** **Refactor a `app/` (T-20, D-15):** movidas con `git mv` las carpetas `config/`, `data_synthetic/`, `src/` y `tests/` a `app/config/`, `app/data_synthetic/`, `app/src/` y `app/tests/`; `clients/` permanece en la raíz (data de runtime del tenant, fuera del código empaquetado, sigue bajo la regla C-01 de `.gitignore`). Actualizadas todas las referencias: `pyproject.toml` (`packages = ["app/src/zeroleak"]`, `testpaths = ["app/tests"]`, `pythonpath = ["app/src"]`), los 9 agentes de desarrollo, templates (`600_template/plan.md`, `notebook.md`), `README.md`, `610_features/README.md`, `905_guideline/methodology.md` y el árbol + prosa de `700_architecture/system_design.md`. Se corrigió además un bug de doble prefijo `app/app/tests/` → `app/tests/` (introducido por un `sed`) en 10 lugares (agentes tdd-*, integration-tester, plan-builder, template `plan.md`, `methodology.md`, `610_features/README.md`). Verificado: `import zeroleak` OK y `pytest` resuelve `testpaths: app/tests`.
- **[2026-07-12]** **Análisis del Tracer Bullet `client_scaffold` (T-12), sin crear artefactos:** acordadas con el humano las decisiones de diseño que alimentarán el futuro `feature_contract.md`: comando `zlk client new <NOMBRE_CLIENTE>`; core `create_client(name: str, clients_root: Path) -> Path` en `app/src/zeroleak/core/scaffold.py`, retorna el `Path` del tenant creado; `clients/` en la raíz del repo (hermano de `app/`), el core recibe `clients_root` siempre explícito (permite tests con `tmp_path`, respetando C-01); alcance mínimo del bullet: solo crea la estructura del tenant, sin sembrar datos sintéticos, `input/` vacío, sin plantillas YAML; estructura materializada: `clients/COMPANY_DEMO/{client.yaml (stub: name + sector_id:null), input/ (vacío), data/{bronze,silver,gold}/ (vacías), manifest.json}`; `manifest.json` inicial como esqueleto explícito `{"client": "<name>", "schema_version": 1, "files": []}`; idempotencia: si el tenant ya existe, falla con error claro, sin `--force` en el bullet; validación de nombre: rechazar (no normalizar) lo que no cumpla `^[A-Z0-9_]+$` y bloquear path traversal (`..`, `/`, `\`); nombre de carpeta de la feature: `610_features/client_scaffold/`.
- **[2026-07-12]** Ejecutado el protocolo de inicio de sesión (`session-starter`): confirmado que el bootstrap metodológico/arquitectónico del proyecto está completo y que la próxima tarea prioritaria es **T-21** (Tracer Bullet `client_scaffold`). Confirmado con el humano el nombre y ubicación del primer feature: `client_scaffold` en `610_features/client_scaffold/` (siguiendo `610_features/README.md`); código en `app/src/zeroleak/core/scaffold.py`, tests en `app/tests/`. Resuelta una duda del humano sobre `state.json`: comparado el `state.json` del proyecto hermano FODA (con campo `band`, organizado por bandas) contra `600_template/state.json`; confirmado que cada feature de ZeroLeak tendrá su `state.json` en `610_features/<feature>/state.json` **sin campo `band`** (D-01) y con las etapas del flujo de 13 pasos (incluye `feature_contract` con owner `main_session`, `notebook_writer`, `human_test`, `merge_to_main`, ausentes en FODA), conservando la granularidad de evidencia TDD (`red_evidence`, `green_evidence`, `refactor_note`, `cases[]`). No se creó todavía la carpeta del feature ni la rama `feature/1`.

## Lo próximo a realizar
- **Prioridad inmediata:** construir el Tracer Bullet **`client_scaffold`** (T-21, continuación de T-12) con sus artefactos SDD+TDD completos en `610_features/client_scaffold/` (`feature_contract.md`, notebook, spec, plan, `state.json` sin campo `band`, tests, código), usando el diseño ya acordado: `zlk client new <NOMBRE_CLIENTE>` respaldado por `create_client(name, clients_root)` en `app/src/zeroleak/core/scaffold.py`; usar `COMPANY_DEMO` como tenant de demostración. Incluye crear la rama `feature/1` (aún no creada).
- (Menor) Terminar de verificar el registro completo de los agentes `.claude/agents/*.md` como subagentes tras reiniciar Claude Code (T-13); confirmar que persistan entre sesiones/reinicios.
- (Menor) Evaluar si se desean colores distintos para los agentes que hoy comparten color (ver nota en `lessons.md` L-04).
- (Pendiente de versionado) Confirmar tras el push que el refactor a `app/` quedó correctamente reflejado en GitHub (rama `main`).
