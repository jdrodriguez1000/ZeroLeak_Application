# Decisions — Decisiones del Proyecto

Registro de las decisiones tomadas durante la ejecución del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por decisión registrada. -->
- [D-01] Opción A: features sin bandas (bandas diferidas)
- [D-02] Flujo notebook-first antes de SDD+TDD
- [D-03] Vocabulario y set de agentes de desarrollo
- [D-04] PR escrito por el agente, merge por el humano
- [D-05] Selección de modelos por agente

---

## [2026-07-12] D-01 — Opción A: una feature = una construcción completa (sin bandas)
- **Contexto:** El modelo FODA usa "bandas" (celda = feature × banda: `tracer_bullet → stab_n`). Se evaluó si aplicaba a ZeroLeak.
- **Decisión:** Adoptar **Opción A (sin bandas)**. Una feature se construye completa en un ciclo. El modelo de bandas queda **disponible pero diferido**, a usar solo si una feature resulta demasiado grande. El primer feature será un **Tracer Bullet a nivel de proyecto**.
- **Consecuencias:** `feature_contract.md` sin sección de bandas; `state.json` sin campo `band`. Menor andamiaje (E4/NC-2).

## [2026-07-12] D-02 — Flujo notebook-first
- **Contexto:** Necesidad de validar el enfoque técnico antes de comprometer diseño con tests.
- **Decisión:** Prototipar cada feature en un `.ipynb` (spike) con **datos sintéticos**, aprobar con gate humano, y luego consolidar a `.py` con SDD+TDD. El notebook informa la spec pero **no la reemplaza**.
- **Consecuencias:** Nuevo paso `notebook_writer` (paso 4) + gate humano (paso 5). Template `notebook.md` creado.

## [2026-07-12] D-03 — Vocabulario y set de agentes de desarrollo
- **Contexto:** Se acordó el flujo de 13 pasos.
- **Decisión:** Agentes: `feature_definer`, `notebook_writer`, `spec_writer`, `plan_builder`, `tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester` (agente separado), `spec_verifier`. El `feature_contract.md` lo escribe la **sesión principal**, no `feature_definer`.
- **Consecuencias:** Templates y `state.json` alineados a estos nombres.

## [2026-07-12] D-04 — PR escrito por el agente, merge por el humano
- **Contexto:** Estrategia de integración a `main`.
- **Decisión:** Toda feature en su rama `feature/<n>`. Cuando `spec_verifier` emite CONFORME, la sesión principal abre el PR; el **humano prueba y mergea**. El harness nunca mergea por su cuenta.
- **Consecuencias:** Etapas terminales `human_test` y `merge_to_main` en `state.json`.

## [2026-07-12] D-05 — Selección de modelos por agente
- **Contexto:** Escalamiento proporcional a la complejidad (P6).
- **Decisión:** **Opus** para definición/spec/plan/verificación; **Sonnet** para ejecución (notebook, coder, refactor, integration, tester); **Haiku** para tareas ligeras (session-starter).
- **Consecuencias:** Documentado en el apéndice de `methodology.md`.
