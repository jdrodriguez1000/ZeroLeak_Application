# Progress — Avance del Proyecto

Este archivo registra el avance del proyecto: lo realizado y lo próximo a realizar.
Consultándolo siempre sabemos el estado y avance actual del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por entrada registrada. -->
- [2026-07-12] Bootstrap del proyecto: persistencia, agentes de sesión, Git/GitHub, metodología y templates SDD+TDD.
- [2026-07-12] Diseño de arquitectura: `700_architecture/system_design.md` v0.2 de ZeroLeak (limpieza de artefactos de FODA, esquema Medallion por tenant, Data Health Score dual, mapa de costuras a SaaS).
- [2026-07-12] T-11 completada: esqueleto del motor (`pyproject.toml`, `src/zeroleak/` con 9 submódulos, `.gitignore` C-01, verificación de aislamiento de datos de cliente) y convención `610_features/` alineada en todo el repo.

---

## Estado actual
El proyecto **ZeroLeak** avanzó de diseño de arquitectura a **esqueleto de código del motor**.
Ya está definida la metodología de desarrollo (Notebook → SDD+TDD, Opción A sin bandas), los templates
de artefactos de feature, los protocolos de sesión, el enlace a GitHub, el **diseño de arquitectura del
motor** (`700_architecture/system_design.md` v0.2), y ahora el **esqueleto de código Python**
(`pyproject.toml` con comando `zlk`, paquete `zeroleak` en `src/` con submódulos `core/ingest/vault/
modules/finance/report/llm`) con el aislamiento C-01 verificado vía `.gitignore` sobre `clients/*/data/`.
Se adoptó la convención `610_features/` (en vez de `600_features/`) y se decidió que los tenants de
cliente se generarán dinámicamente con el comando `zlk client new` (patrón heredado de FODA), en vez de
crearse a mano o commitearse. El tenant de demostración se llamará `COMPANY_DEMO`. Falta crear los 9
agentes de desarrollo (T-10) y luego construir el primer Tracer Bullet: `zlk client new` (T-12).

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

## Lo próximo a realizar
- **Prioridad inmediata:** crear los **9 agentes de desarrollo (T-10)**: `feature_definer`, `notebook_writer`, `spec_writer`, `plan_builder`, `tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester`, `spec_verifier`.
- Construir el **primer Tracer Bullet (T-12)**: `zlk client new <NOMBRE_CLIENTE>`, respaldado por `create_client(name, clients_root)` en `src/zeroleak/core/scaffold.py`; usar `COMPANY_DEMO` como tenant de demostración con datos sintéticos.
- (Menor) Verificar que los agentes `.claude/agents/*.md` se registren como subagentes tras reiniciar Claude Code (T-13).
