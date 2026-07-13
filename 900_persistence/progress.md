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
- [2026-07-12] T-21 en construcción: rama `feature/client_scaffold` creada; artefactos SDD generados hasta el paso 9 (`feature_contract.md`, `definition.md`, `client_scaffold.ipynb`, `spec.md`, `plan.md`, `state.json`), con dos gates humanos aprobados y ajustes del notebook a `COMPANY_DEMO`. Bucle TDD aún sin iniciar.
- [2026-07-13] T-21 avanzada (paso 10 completo): bucle TDD cerrado (13/13 casos `refactored`), código de producción en `app/src/zeroleak/core/scaffold.py` y `app/src/zeroleak/cli.py`, suite completa 39 passed; renombrados a inglés los 3 YAML de `input/` (`contract_data.yaml`, `business_rules.yaml`, `finance.yaml`); creado el tenant real `COMPANY_DEMO` (TSK-24) por la vía oficial; entorno `.venv/` con Python 3.13 configurado en la raíz del repo.

---

## Estado actual
El proyecto **ZeroLeak** está construyendo su primer Tracer Bullet, **`client_scaffold`** (T-21), en la
rama `feature/client_scaffold`. Se completaron los pasos 1 a 10 del flujo de 13 pasos: carpeta
`610_features/client_scaffold/` creada; `feature_contract.md` escrito por la sesión principal; `definition.md`
con 8 historias (HU-01…HU-08) producido por `feature_definer`; `client_scaffold.ipynb` (spike con datos
sintéticos) producido por `notebook_writer`, aprobado en gate humano (paso 5); `spec.md` con
10 criterios (CA-01…CA-10) producido por `spec_writer`, materializando el regex aprobado
`^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$`, aprobado explícitamente en gate humano (paso 7); `plan.md` con
27 tareas (TSK-01…TSK-27) y 13 casos de test trazables a los CA, producido por `plan_builder` y aprobado
en gate humano (paso 9). El **bucle TDD (paso 10) fue completado en esta sesión**: los 13 casos definidos
en `plan.md`/`state.json` quedaron en estado `refactored` (`stages.tdd.status = "done"` en `state.json`).
Código de producción final: `app/src/zeroleak/core/scaffold.py` (core `create_client(name, clients_root) ->
Path`, validación `NAME_PATTERN`, excepciones `ClientNameError`/`TenantExistsError`, atomicidad vía
staging+rename, placeholders YAML, `manifest.json`, guarda de no idempotencia) y `app/src/zeroleak/cli.py`
(fachada `zlk client new`, resuelve `clients_root` desde la variable de entorno `ZEROLEAK_CLIENTS_ROOT`,
traduce excepciones a exit codes 0/2/3); tests en `app/tests/conftest.py`, `app/tests/test_scaffold.py` y
`app/tests/test_cli_client_new.py`. Los casos 1, 8, 9 y 10 tuvieron fase ROJA clásica; los casos 2-7 y
11-13 pasaron de inmediato al escribirse (porque su código de producción ya había quedado cubierto al
implementar la estructura completa del tenant en el Caso 2), y en cada uno `tdd_tester` provocó
temporalmente el defecto para confirmar honestamente que el test fallaba, revirtiendo sin dejar rastro
(verificación razonada). Tareas TSK-01 a TSK-24, TSK-26 y TSK-27 quedaron `Implementada`; solo resta
**TSK-25** (prueba de integración, paso 11). Tras el cierre del bucle TDD se hizo un ajuste dirigido por el
humano: los 3 YAML de `input/` se renombraron a inglés (`contrato_datos.yaml`→`contract_data.yaml`,
`reglas_negocio.yaml`→`business_rules.yaml`, `finanzas.yaml`→`finance.yaml`, incl. la clave interna del
YAML y el comentario guía), propagado a `scaffold.py`, los tests, `spec.md`, `plan.md`, `state.json`,
`client_scaffold.ipynb`, `system_design.md` y el tenant `COMPANY_DEMO` (regenerado). TSK-24 (tarea del
humano) se ejecutó con asistencia: se creó el tenant de demostración real `clients/COMPANY_DEMO` por la
vía oficial (`zlk client new COMPANY_DEMO`), versionando solo `client.yaml` + `input/` (con `data/`
gitignored por C-01); queda stageado, pendiente de commit del cierre de sesión. También se descubrió y
resolvió una fricción de entorno: el `pyproject.toml` (en la raíz del repo) declara `requires-python
>=3.13`, pero el `python` del PATH del usuario es 3.12.10; se usó `py -3.13` y se creó un ambiente virtual
`.venv/` en la raíz con el paquete instalado en modo editable (`pip install -e ".[dev]"`), ya cubierto por
`.gitignore`. La suite completa corre en **39 passed**, verificado tanto con `py -3.13` como dentro del
`.venv`. El **próximo paso del flujo es el paso 11**: prueba de integración TSK-25 (`integration_tester`),
ejecutando el comando instalado `zlk client new` por subprocess (requiere correr en el venv / Python
3.13); luego paso 12 (`spec_verifier`), gate humano (`human_test`) y `merge_to_main` (PR hacia `main`).
Antes de esta feature, el proyecto ya había avanzado de diseño de
arquitectura y esqueleto de código a **agentes de desarrollo listos**, con el código reubicado bajo una
carpeta `app/` dedicada. Ya está definida la
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
- **[2026-07-12]** **T-21 avanzada (pasos 1-9 del flujo):** creada la rama `feature/client_scaffold` (renombrada desde `feature/1` a pedido del humano) y la carpeta `610_features/client_scaffold/`. Paso 2: la sesión principal escribió `feature_contract.md`. Paso 3: `feature_definer` produjo `definition.md` con 8 historias HU-01…HU-08. Paso 4: `notebook_writer` produjo `client_scaffold.ipynb` (spike con datos sintéticos). Paso 5 (gate humano): aprobado, con decisiones de permitir acentos/ñ en el regex de nombre y usar placeholders YAML con claves vacías + comentarios guía. Paso 6: `spec_writer` produjo `spec.md` con 10 criterios CA-01…CA-10, regex aprobado `^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$`. Paso 7 (gate humano): la spec fue aprobada explícitamente (se corrigió un intento de aprobación implícita, señalado por el humano), con decisiones adicionales sobre exit codes (0/2/3) y YAMLs de `input/` con placeholder mínimo genérico. Paso 8: `plan_builder` produjo `plan.md` con 27 tareas TSK-01…TSK-27 y 13 casos de test trazables a los CA. Paso 9 (gate humano): plan aprobado. Se creó `state.json` (etapas hasta `plan_builder` en `done` con gates aprobados, sin campo `band`, `current_stage="tdd"`, 13 casos en `stages.tdd.cases[]` en estado `pending`). Tras revisión del humano, se ajustó el notebook: armonizado para usar `COMPANY_DEMO` en vez de `SANDUCHERIA` (Celda 10 reestructurada para evitar colisión `TenantExistsError`) y alineada la validación a la regla aprobada (acentos/ñ válidos; ejemplos inválidos con cirílico y emoji). Notebook re-ejecutado con `nbconvert`: exit 0, 0 celdas con error, JSON válido, validación verificada por codepoint y por ejecución. El bucle TDD (paso 10) aún no se inició.
- **[2026-07-13]** **T-21 avanzada (paso 10 completo, bucle TDD):** ejecutado el bucle `tdd_tester → tdd_coder → tdd_refactor` sobre los 13 casos de `plan.md`/`state.json`. Casos 1, 8, 9, 10 con fase ROJA clásica (comportamiento nuevo); Casos 2-7 y 11-13 con tests que pasaron de inmediato al escribirse (código de producción ya cubierto desde el Caso 2), verificados con "verificación razonada honesta" (se provocó temporalmente el defecto, se confirmó el fallo, se revirtió sin dejar rastro en el diff). Producción final: `app/src/zeroleak/core/scaffold.py` (`create_client`, `NAME_PATTERN`, `ClientNameError`, `TenantExistsError`, atomicidad staging+rename, placeholders YAML, manifest, guarda de no idempotencia) y `app/src/zeroleak/cli.py` (`main`, `_parse_client_new_name`, `_dispatch_client_new`, `_clients_root` vía `ZEROLEAK_CLIENTS_ROOT`, exit codes 0/2/3). Tests nuevos: `app/tests/conftest.py`, `app/tests/test_scaffold.py`, `app/tests/test_cli_client_new.py`. `state.json`: los 13 casos quedaron en `refactored`, `stages.tdd.status="done"`. TSK-01 a TSK-24, TSK-26, TSK-27 → `Implementada`; solo queda TSK-25 (integración, paso 11) `No implementada`.
- **[2026-07-13]** **Renombrado a inglés de los 3 YAML de `input/`** (ajuste dirigido por el humano, posterior al cierre de los 13 casos): `contrato_datos.yaml`→`contract_data.yaml`, `reglas_negocio.yaml`→`business_rules.yaml`, `finanzas.yaml`→`finance.yaml` (archivo, clave interna del YAML y comentario guía); propagado a `scaffold.py`, `test_scaffold.py`, `spec.md`, `plan.md`, `state.json`, `client_scaffold.ipynb`, `system_design.md` y el tenant `COMPANY_DEMO` (regenerado). La prosa descriptiva en español se mantuvo sin cambios.
- **[2026-07-13]** **TSK-24 ejecutada (con asistencia):** creado un ambiente virtual `.venv/` en la raíz del repo con `py -3.13` (Python del PATH del usuario es 3.12.10; `pyproject.toml`, en la raíz, declara `requires-python>=3.13`), paquete instalado en modo editable con dev deps (`pip install -e ".[dev]"`); generado el tenant de demostración real `clients/COMPANY_DEMO` por la vía oficial (`zlk client new COMPANY_DEMO` / `zeroleak.cli:main`), versionando `client.yaml` + `input/` (data/ excluido por C-01/`.gitignore`), stageado para el commit de cierre de sesión. Suite completa verificada: **39 passed**, tanto con `py -3.13` directo como dentro del `.venv`.

## Lo próximo a realizar
- **Prioridad inmediata:** continuar T-21 con el **paso 11** del flujo: prueba de integración **TSK-25** (`integration_tester`), ejecutando el comando instalado `zlk client new` por subprocess (debe correrse dentro del `.venv` / con Python 3.13, dado el `requires-python>=3.13` del `pyproject.toml`).
- Tras la integración, continuar el flujo de 13 pasos: paso 12 `spec_verifier` (produce `verification.md`), gate humano de prueba (`human_test`) y `merge_to_main` (PR de `feature/client_scaffold` hacia `main`, aprobado y mergeado por el humano; el agente nunca mergea).
- (Menor) Terminar de verificar el registro completo de los agentes `.claude/agents/*.md` como subagentes tras reiniciar Claude Code (T-13); confirmar que persistan entre sesiones/reinicios.
- (Menor) Evaluar si se desean colores distintos para los agentes que hoy comparten color (ver nota en `lessons.md` L-04).
