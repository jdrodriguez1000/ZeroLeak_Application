# Progress — Avance del Proyecto

Este archivo registra el avance del proyecto: lo realizado y lo próximo a realizar.
Consultándolo siempre sabemos el estado y avance actual del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por entrada registrada. -->
- [2026-07-12] Bootstrap del proyecto: persistencia, agentes de sesión, Git/GitHub, metodología y templates SDD+TDD.

---

## Estado actual
El proyecto **ZeroLeak** está en fase de **andamiaje metodológico** (aún no se construye producto).
Ya está definida la metodología de desarrollo (Notebook → SDD+TDD, Opción A sin bandas), los templates
de artefactos de feature, los protocolos de sesión y el enlace a GitHub. Falta crear los agentes de
desarrollo y arrancar el primer feature (Tracer Bullet).

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

## Lo próximo a realizar
- Crear los **9 agentes de desarrollo**: `feature_definer`, `notebook_writer`, `spec_writer`, `plan_builder`, `tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester`, `spec_verifier`.
- Crear estructura de carpetas: `src/zeroleak/`, `tests/`, `data_real/` (esta última en `.gitignore`), `600_features/`.
- Definir el **primer feature** (Tracer Bullet a nivel de proyecto).
- (Menor) Verificar que los agentes `.claude/agents/*.md` se registren como subagentes tras reiniciar Claude Code.
