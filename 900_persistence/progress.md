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
- [2026-07-13] Tracer Bullet `client_scaffold` **CERRADO (pasos 11-13):** integración e2e (TSK-25) contra `zlk client new` por subprocess (suite 43 passed, cubre CA-01..CA-08); `spec_verifier` auditó los 10 CA con veredicto CONFORME (`610_features/client_scaffold/verification.md`); el humano aprobó y mergeó el PR #1 a `main`. Actualizado `README.md` con secciones "Entorno de desarrollo" y "Uso del CLI". Decidida la siguiente feature del segundo Tracer Bullet: `ingest` (D-17, T-26).
- [2026-07-13] T-28 (Tracer Bullet `ingest`) iniciado: rama `feature/ingest` creada desde `main`, carpeta `610_features/ingest/` creada, paso 2 del flujo completado con `feature_contract.md` escrito por la sesión principal (materializa D-17, deja D-18 fuera de alcance). Paso 3 (`feature_definer`) pendiente.
- [2026-07-13] T-28 avanzado (pasos 3-9 completos, paso 10 al 42%): `definition.md` (8 HU), `ingest.ipynb` ejecutado y aprobado (gate paso 5, 3 decisiones ratificadas: sufijo `__<sha8>` en colisión, exit codes 0/1/2, duplicate=SKIP no-op), `spec.md` con 12 CA aprobada (gate paso 7, 3 defaults ratificados: extensiones case-insensitive, manifest con solo 4 campos, `ingested_at` timespec segundos), `plan.md` con 27 TSK y 12 casos aprobado (gate paso 9). Bucle TDD (paso 10): 5 de 12 casos cerrados (CA-08, CA-01, CA-02 caracterizado, CA-09, CA-05); código de producción en `app/src/zeroleak/ingest/core.py`; suite 49 passed. Sesión suspendida a pedido del humano tras el Caso 5.

---

## Estado actual
El proyecto **ZeroLeak** está construyendo su **segundo Tracer Bullet, `ingest` (T-28)**, sobre la rama
`feature/ingest` (creada desde `main`, que ya contiene el primer Tracer Bullet `client_scaffold` mergeado
vía PR #1). Del flujo de 13 pasos, los **pasos 1 a 9 están completos** y el **paso 10 (bucle TDD) va al
42% (5 de 12 casos)**. Artefactos existentes en `610_features/ingest/`: `feature_contract.md` (paso 2,
materializa D-17); `definition.md` con 8 historias HU-01…HU-08 (paso 3, `feature_definer`); `ingest.ipynb`
(paso 4, spike con datos sintéticos, ejecutado in-place tras instalar `nbconvert`+`ipykernel` en el `.venv`
porque el agente no tenía kernel); gate humano del notebook (paso 5) **aprobado**, ratificando 3 decisiones:
(a) nombrado en bronze ante colisión de nombre con sufijo `__<sha8>`; (b) exit codes `0`=éxito total,
`1`=parcial o fallo por ruta, `2`=fallo global por tenant inexistente; (c) `duplicate` = no-op idempotente
(SKIP), no cuenta como fallo; `spec.md` con 12 criterios CA-01…CA-12 (paso 6, `spec_writer`), trazables a
las HU; gate humano de la spec (paso 7) **aprobado**, ratificando 3 defaults: extensiones case-insensitive,
manifest con **solo** `file`/`sha256`/`ingested_at`/`status` (ausencia verificable de `period`/`run_id`/
`output`), `ingested_at` con `timespec` de segundos; `plan.md` con 27 tareas TSK-01…TSK-27 y 12 casos de
test (paso 8, `plan_builder`), gate humano (paso 9) **aprobado**; `state.json` creado siguiendo el patrón
de `client_scaffold`, con `current_stage="tdd"`. El **bucle TDD (paso 10)** completó **5 de los 12 casos**
definidos, organizados en bloques (bloque 1 = caso 1; bloque 2 = casos 2-5), todos en estado `refactored`
salvo el Caso 3 (`characterized`, sin ciclo RED/GREEN porque CA-02 ya quedó satisfecho como efecto
colateral del Caso 2 — TSK-06 `implementada` como test de caracterización/regresión, TSK-07 `cancelada_
suspendida` sin código nuevo): Caso 1 (CA-08, tenant inexistente → `TenantNotFoundError`/exit 2), Caso 2
(CA-01, ingesta csv byte-a-byte + entrada `pending`), Caso 3 (CA-02, forma exacta del manifest,
caracterización), Caso 4 (CA-09, archivo vacío → fallo por ruta/exit 1), Caso 5 (CA-05, dedupe por
`sha256` → SKIP/exit 0, incluyendo dedupe intra-invocación). Código de producción:
`app/src/zeroleak/ingest/core.py` (`ingest_paths`, `IngestResult`, `TenantNotFoundError`, helpers
`_resolve_tenant_paths`, `_validate_file`, `_hash_file`, `_build_manifest_entry`) y su `__init__.py`; tests
en `app/tests/test_ingest.py` y fixtures nuevas en `app/tests/conftest.py` (`ingestible_tenant`,
`read_manifest`). Suite total: **49 passed**, sin regresiones. El trabajo fue **suspendido a pedido del
humano** tras el Caso 5. El **próximo paso pendiente** es continuar el bucle TDD: **bloque 3 (casos 6-9)**
y **bloque 4 (casos 10-12)**, y luego los pasos 11-13 (integración TSK-25, `spec_verifier`, gate humano
final, PR hacia `main`). La carpeta `clients/MI_BUNUELO/` sigue siendo un tenant de prueba manual del
humano, sin versionar.

El proyecto **cerró su primer Tracer Bullet, `client_scaffold` (T-21)**, con los 13 pasos del
flujo completos: `feature/client_scaffold` fue mergeada a `main` vía PR #1, aprobado y mergeado por el
humano (paso 13). La rama local `main` ya está sincronizada (`git pull` ff-only) y contiene el comando
`zlk client new` funcional, verificado por integración (43 passed) y auditado como CONFORME por
`spec_verifier` (`610_features/client_scaffold/verification.md`). Además se actualizó `README.md` en `main`
con las secciones "Entorno de desarrollo" (creación/activación de `.venv` con `py -3.13`, instalación
editable, cómo correr tests) y "Uso del CLI" (comando `zlk client new`, patrón de nombres, tabla de exit
codes 0/1/2/3), y se corrigió la nota obsoleta que decía que el comando estaba "aún no implementado". Se
acordó con el humano el alcance del **segundo Tracer Bullet, `ingest`** (D-17): comando que registra
archivos del cliente en la capa bronze del tenant (copia inmutable, hash `sha256`, entrada en
`manifest.json` con status `pending`), con dedupe por `sha256` que habilita el Modo Incremental, sin
parsear contenido (principio "archivador notarial": el delimitador/estructura es problema del Contrato de
Datos en una etapa posterior), validación agnóstica de formato (tenant existe, archivo no vacío, extensión
en allow-list `.csv`/`.xlsx` únicamente — `.txt` explícitamente fuera), y entrada por archivo o carpeta con
recorrido plano (sin recursión) para evitar la inconsistencia de expansión de glob entre shells. Esta
feature aún no tiene rama ni artefactos creados; queda como **próxima prioridad (T-26)**. Antes de este
cierre, el flujo de `client_scaffold` había completado los pasos 1 a 10; carpeta
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
- **[2026-07-13]** **T-21 CERRADA (pasos 11-13, cierre del Tracer Bullet `client_scaffold`):** Paso 11 (TSK-25): `integration_tester` creó `app/tests/integration/test_client_new_e2e.py`, ejecutando `zlk client new` por subprocess dentro del `.venv` (Python 3.13); suite total **43 passed**, cubre CA-01..CA-08. Paso 12: `spec_verifier` auditó con mentalidad crítica los 10 CA contra la spec, con evidencia real de ejecución; C-01 "Datos en Bóveda" verificada; veredicto **CONFORME**; se creó `610_features/client_scaffold/verification.md`. Paso 13: el humano aprobó y **mergeó el PR #1** (`feature/client_scaffold` → `main`) en GitHub; `main` local sincronizado con `git pull` ff-only.
- **[2026-07-13]** **Actualizado `README.md`** (en `main`, tras el merge): agregada sección "Entorno de desarrollo" (crear/activar `.venv` con `py -3.13`, instalar con `pip install -e ".[dev]"`, correr tests) y sección "Uso del CLI" (comando `zlk client new`, patrón de nombres, tabla de exit codes 0/1/2/3); corregida la nota obsoleta que indicaba que `zlk client new` estaba "aún no implementada".
- **[2026-07-13]** **Decidido el alcance del segundo Tracer Bullet, `ingest` (D-17):** comando para registrar archivos del cliente en la capa bronze del tenant (copia fiel/inmutable a `clients/<CLIENTE>/data/bronze/`, hash `sha256`, entrada en `manifest.json` con status `pending`); dedupe por `sha256` (habilita Modo Incremental §10); principio "archivador notarial" — `ingest` no parsea contenido, el delimitador/estructura es problema del Contrato de Datos (YAML 1) en etapa posterior; validación agnóstica de formato (tenant existe, archivo no vacío, extensión en allow-list); allow-list MVP `.csv`/`.xlsx` únicamente, `.txt` explícitamente fuera; entrada por archivo o carpeta con recorrido plano (sin recursión), preferido sobre glob por inconsistencias de shell en PowerShell. Sin artefactos creados aún (T-26, `No implementada`).
- **[2026-07-13]** **T-28 avanzada (pasos 1-2 del flujo, Tracer Bullet `ingest`):** creada la rama `feature/ingest` desde `main`; creada la carpeta `610_features/ingest/`; la sesión principal escribió `feature_contract.md` materializando D-17 (comando `zlk ingest <CLIENTE> <ruta>...`, uno o varios argumentos de archivo/carpeta con recorrido plano, copia inmutable a bronze, `sha256`, entrada `manifest.json` status `pending`, dedupe habilita Modo Incremental, principio "archivador notarial", validación básica agnóstica de formato, allow-list MVP `.csv`/`.xlsx`, 6 criterios de aceptación a nivel feature) y dejando D-18 explícitamente fuera de alcance. Paso 3 (`feature_definer` → `definition.md`) queda pendiente para la próxima sesión.
- **[2026-07-13]** **T-28 avanzada (pasos 3-9 completos, Tracer Bullet `ingest`):** Paso 3: `feature_definer` produjo `610_features/ingest/definition.md` con 8 historias HU-01…HU-08. Decisión humana zanjada y reflejada en HU-05: procesamiento **parcial** por ruta con reporte de éxitos/fallos; tenant inexistente es precondición global que aborta toda la invocación. Paso 4: `notebook_writer` produjo `610_features/ingest/ingest.ipynb` (spike con datos sintéticos); como el agente no pudo ejecutarlo, la sesión principal instaló `nbconvert`+`ipykernel` en el `.venv` y ejecutó el notebook in-place, demostrando las 8 HU con evidencia visible. Paso 5 (gate humano): notebook **aprobado**, ratificando 3 decisiones: nombrado en bronze ante colisión con sufijo `__<sha8>`; exit codes 0/1/2 (éxito total/parcial-o-fallo-por-ruta/fallo global por tenant); `duplicate` = no-op idempotente (SKIP), no cuenta como fallo. Paso 6: `spec_writer` produjo `spec.md` con 12 criterios CA-01…CA-12 trazables a las HU. Paso 7 (gate humano): spec **aprobada**, ratificando 3 defaults: extensiones case-insensitive; manifest con solo `file`/`sha256`/`ingested_at`/`status` (ausencia verificable de `period`/`run_id`/`output`); `ingested_at` con `timespec` de segundos. Paso 8: `plan_builder` produjo `plan.md` con 27 tareas TSK-01…TSK-27 y 12 casos de test, todos los CA cubiertos. Paso 9 (gate humano): plan **aprobado**.
- **[2026-07-13]** **T-28 avanzada (paso 10, bucle TDD, 5/12 casos, Tracer Bullet `ingest`):** completado el bloque 1 (caso 1) y el bloque 2 (casos 2-5) del bucle `tdd_tester → tdd_coder → tdd_refactor`. Caso 1 (CA-08): tenant inexistente → `TenantNotFoundError`/exit 2. Caso 2 (CA-01): ingesta csv byte-a-byte + entrada `pending`. Caso 3 (CA-02): forma exacta del manifest; sin ciclo RED/GREEN (CA-02 ya satisfecho por el Caso 2); conservado como test de caracterización/regresión (TSK-06 `implementada`, TSK-07 `cancelada_suspendida`). Caso 4 (CA-09): archivo vacío → fallo por ruta, exit 1. Caso 5 (CA-05): dedupe por `sha256` (SKIP, exit 0), incluyendo dedupe intra-invocación. Creado el código de producción `app/src/zeroleak/ingest/core.py` (`ingest_paths`, `IngestResult`, `TenantNotFoundError`, helpers `_resolve_tenant_paths`, `_validate_file`, `_hash_file`, `_build_manifest_entry`) y su `__init__.py`; tests en `app/tests/test_ingest.py` y fixtures nuevas en `app/tests/conftest.py` (`ingestible_tenant`, `read_manifest`). Suite total: 49 passed, sin regresiones. Creado `610_features/ingest/state.json` siguiendo el patrón de `client_scaffold`. Trabajo **suspendido a pedido del humano** tras el Caso 5.

## Lo próximo a realizar
- **Prioridad inmediata:** continuar el bucle TDD (paso 10) del segundo Tracer Bullet, **`ingest`** (T-28): **bloque 3 (casos 6-9)** y **bloque 4 (casos 10-12)** de `plan.md`/`state.json`, sobre `app/src/zeroleak/ingest/core.py`.
- Tras cerrar el bucle TDD: pasos 11-13 del flujo — integración e2e (TSK-25, `integration_tester` sobre `zlk ingest` por subprocess), `spec_verifier` (`verification.md`), gate humano final (`human_test`) y apertura de PR hacia `main` (`merge_to_main`).
- (Menor) Terminar de verificar el registro completo de los agentes `.claude/agents/*.md` como subagentes tras reiniciar Claude Code (T-13); confirmar que persistan entre sesiones/reinicios.
- (Menor) Evaluar si se desean colores distintos para los agentes que hoy comparten color (ver nota en `lessons.md` L-04).
- (Nota) `clients/MI_BUNUELO/` es un tenant de prueba manual del humano (no es entregable); queda sin versionar en el working tree.
