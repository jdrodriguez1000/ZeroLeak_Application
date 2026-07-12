# Constraints — Restricciones del Proyecto

Registro de las restricciones para llevar a cabo el proyecto
(técnicas, de negocio, legales, de tiempo, de recursos, etc.).

---

## Índice
<!-- Mantener actualizado. Un enlace por restricción registrada. -->
- [C-01] 🔒 Datos en Bóveda (inviolable) — aislamiento ahora vía `.gitignore` sobre `clients/*/data/` (Medallion por tenant)
- [C-02] ZeroLeak solo diagnostica, no limpia datos
- [C-03] Integración a `main` solo vía PR con merge humano

---

## [2026-07-12] C-01 — 🔒 "Datos en Bóveda" (INVIOLABLE)
- **Tipo:** técnica / legal (privacidad, NDA)
- **Descripción:** El LLM y los agentes de IA solo trabajan con **datos sintéticos** ("matrices de mentiras", 3–5 filas falsas). **Ningún dato real del cliente** entra a notebooks que el LLM vea, ni se envía a servidores de IA. El motor (`validador.py`) corre **100% local**. Técnica **Drop & Detach**: crear columnas bandera (1/0), eliminar columnas de texto original (email, nombre, teléfono) y calcular sobre los unos y ceros para eliminar la PII de raíz.
- **Origen / motivo:** Documento fuente `Salud de datos.docx` (sección Estrategia de Seguridad). Blindaje legal frente a NDAs y leyes de protección de datos.
- **Impacto:** Todo agente/artefacto lo respeta; su cumplimiento se verifica en `verification.md`.
- **[2026-07-12] Actualización de implementación (ver `decisions.md` D-09, D-11):** el aislamiento del indexador ya no se basa en un `data_real/` global, sino en la estructura por **tenant** (`clients/<CLIENTE>/`) con capas Medallion; la regla de `.gitignore` aplica sobre **`clients/*/data/`** (bronze/silver/gold), mientras que `clients/<CLIENTE>/input/` (config del cliente) sí se versiona.

## [2026-07-12] C-02 — ZeroLeak solo diagnostica, no limpia
- **Tipo:** negocio / alcance
- **Descripción:** ZeroLeak **audita y traduce a dinero** los errores de datos; **no limpia ni corrige** los datos del cliente. Entrega el diagnóstico y los CSVs de errores "masticados" para que el equipo del cliente los resuelva.
- **Origen / motivo:** Decisión de posicionamiento (BI/Auditoría, no herramienta de TI) del documento fuente.
- **Impacto:** Define el `out of scope` recurrente de las features.

## [2026-07-12] C-03 — Integración a `main` solo vía PR con merge humano
- **Tipo:** proceso / técnica
- **Descripción:** El harness puede llegar hasta abrir el PR; la **aprobación y el merge a `main` los hace el humano**.
- **Origen / motivo:** Estrategia de control de versiones acordada (ver `CLAUDE.md` y `decisions.md` D-04).
- **Impacto:** Etapas terminales `human_test` / `merge_to_main`.
