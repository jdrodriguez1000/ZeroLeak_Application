# Progress — Avance del Proyecto

Este archivo registra el avance del proyecto: lo realizado y lo próximo a realizar.
Consultándolo siempre sabemos el estado y avance actual del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por entrada registrada. -->
- [2026-07-12] Bootstrap del proyecto: persistencia, agentes de sesión, Git/GitHub, metodología y templates SDD+TDD.
- [2026-07-12] Diseño de arquitectura: `700_architecture/system_design.md` v0.2 de ZeroLeak (limpieza de artefactos de FODA, esquema Medallion por tenant, Data Health Score dual, mapa de costuras a SaaS).

---

## Estado actual
El proyecto **ZeroLeak** avanzó de andamiaje metodológico a **diseño de arquitectura (v0.2)**.
Ya está definida la metodología de desarrollo (Notebook → SDD+TDD, Opción A sin bandas), los templates
de artefactos de feature, los protocolos de sesión, el enlace a GitHub, y ahora también el **diseño de
arquitectura del motor** (`700_architecture/system_design.md`): script Python local con capas Medallion
(bronze/silver/gold) por tenant de cliente, manifiesto de procesamiento idempotente, Data Health Score
dual (financiero/operativo) y un mapa de costuras explícito para evolucionar de Servicio local a SaaS sin
reescribir el núcleo. Falta alinear la estructura de carpetas de código (T-11) a este diseño, crear los
agentes de desarrollo y arrancar el primer feature (Tracer Bullet).

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

## Lo próximo a realizar
- Actualizar **T-11** (estructura de carpetas) para alinearla al `system_design.md` v0.2: `src/zeroleak/` con submódulos `core/ingest/vault/modules/finance/report/llm`; `clients/<CLIENTE>/input/` + `clients/<CLIENTE>/data/{bronze,silver,gold}/`; `config/sectors/`; `data_synthetic/`; regla `.gitignore` para `clients/*/data/`.
- Crear los **9 agentes de desarrollo**: `feature_definer`, `notebook_writer`, `spec_writer`, `plan_builder`, `tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester`, `spec_verifier`.
- Definir el **primer feature** (Tracer Bullet a nivel de proyecto), ya informado por `system_design.md` v0.2.
- (Menor) Verificar que los agentes `.claude/agents/*.md` se registren como subagentes tras reiniciar Claude Code.
