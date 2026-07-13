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
- [D-06] Alcance del diseño: motor local con mapa de costuras a SaaS (no plataforma SaaS completa ahora)
- [D-07] Data Health Score: soportar ambos métodos (Financiero y Operativo), seleccionables
- [D-08] Caso guía: sanduchería, manteniendo el motor agnóstico de sector
- [D-09] Esquema de datos del cliente en capas Medallion (bronze/silver/gold) por tenant
- [D-10] Manifiesto de procesamiento (`manifest.json`) con hash de contenido, idempotente
- [D-11] Rename `config/` → `input/`; aislamiento de C-01 vía `.gitignore` sobre `clients/*/data/`
- [D-12] Comando de consola `zlk` (paquete Python `zeroleak`)
- [D-13] Tenants de cliente generados dinámicamente con `zlk client new`, nunca a mano ni commiteados
- [D-14] Convención de carpeta de features: `610_features/` (no `600_features/`)
- [D-15] Refactor estructural: código movido a `app/` (`config/`, `data_synthetic/`, `src/`, `tests/`); `clients/` permanece en la raíz
- [D-16] Nombres de los 3 YAML de `input/` en inglés (`contract_data.yaml`, `business_rules.yaml`, `finance.yaml`)

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
- **[Revisión 2026-07-12]** `feature_definer` se implementa con **Sonnet** (no Opus) y `notebook_writer` con **Opus** (no Sonnet), por decisión del humano al crear cada agente. El apéndice de `methodology.md` queda alineado. Las reglas generales (Opus para definición, Sonnet para ejecución) se mantienen como guía; estas dos son excepciones explícitas vigentes.

## [2026-07-12] D-06 — Alcance del diseño: motor local con mapa de costuras a SaaS
- **Contexto:** Al diseñar `system_design.md` había que decidir si documentar una plataforma SaaS completa o solo el script local de la Fase Servicio.
- **Decisión:** ZeroLeak nace como **script Python local** (Fase Servicio, "Datos en Bóveda"), pero el diseño documenta explícitamente el **mapa de costuras** para evolucionar a SaaSw y luego a SaaS (motor diseñado "como una API"; CLI es la primera fachada) sin reescribir el núcleo.
- **Consecuencias:** `system_design.md` v0.2 incluye principio rector Servicio→SaaS y RBAC de 6 roles como diseño futuro (no implementado en MVP).

## [2026-07-12] D-07 — Data Health Score: soportar ambos métodos
- **Contexto:** No todos los clientes entregan su facturación real al motor.
- **Decisión:** El motor soporta **ambos métodos** de cálculo del Data Health Score (Financiero y Operativo ponderado), seleccionables según si el cliente entrega su facturación.
- **Consecuencias:** El diseño de módulos de scoring debe contemplar ambas rutas de cálculo, no solo una.

## [2026-07-12] D-08 — Caso guía: sanduchería, motor agnóstico de sector
- **Contexto:** El documento fuente usa una sanduchería (POS + Rappi + WhatsApp) como ejemplo recurrente.
- **Decisión:** Se adopta la sanduchería como **caso guía ilustrativo** del MVP (nicho Retail Moderno), pero el motor se mantiene **agnóstico de sector** vía el Maestro de Sectores (YAML).
- **Consecuencias:** Ejemplos y datos sintéticos del diseño usan el caso sanduchería; el core no debe acoplarse a ese sector.

## [2026-07-12] D-09 — Esquema de datos del cliente en capas Medallion por tenant
- **Contexto:** Se necesitaba definir cómo se organizan físicamente los datos de cada cliente, evitando el `data_real/` global y las carpetas por-periodo confusas planteadas antes.
- **Decisión:** Cada cliente es un **tenant** (`clients/<CLIENTE>/`) con datos organizados en capas **Medallion** (bronze/silver/gold). **Silver se mantiene como capa física** persistida (no colapsada en memoria), para que el aislamiento de C-01 sea auditable.
- **Consecuencias:** Reemplaza el diseño previo de `data_real/` global; T-11 debe crear `clients/<CLIENTE>/data/{bronze,silver,gold}/`.

## [2026-07-12] D-10 — Manifiesto de procesamiento idempotente
- **Contexto:** El motor debe saber qué archivos de un cliente ya procesó, en modo histórico e incremental/quincenal.
- **Decisión:** Cada tenant tiene un `manifest.json` con **hash de contenido** y estado `pending`/`processed` por archivo. El periodo pasa a ser **metadato**, no una carpeta física.
- **Consecuencias:** El core de ingesta debe leer/escribir el manifiesto antes y después de cada corrida.

## [2026-07-12] D-11 — Rename `config/`→`input/` y aislamiento de C-01 vía `.gitignore` por tenant
- **Contexto:** Definir cómo el cliente entrega sus insumos de configuración y cómo se aísla la PII real de git/indexador (C-01).
- **Decisión:** La carpeta de configuración por cliente pasa de `config/` a **`input/`**. El aislamiento de C-01 se logra con `.gitignore` sobre **`clients/*/data/`**, en vez de un `data_real/` global.
- **Consecuencias:** T-11 debe crear la regla `.gitignore` correspondiente; toda referencia previa a `data_real/` en `progress.md`/`tasks.md` queda superada por esta convención basada en tenant.

## [2026-07-12] D-12 — Comando de consola `zlk`
- **Contexto:** Al construir el esqueleto del motor (T-11) había que fijar el nombre del comando de consola que expone el paquete `zeroleak`.
- **Decisión:** El comando de consola es **`zlk`** (entry point `zlk = "zeroleak.cli:main"` en `pyproject.toml`); el paquete Python instalable sigue llamándose `zeroleak`. Uso típico: `zlk client new <NOMBRE_CLIENTE>`.
- **Consecuencias:** Toda referencia futura al CLI en docs/agentes debe usar `zlk`, no `zeroleak`.

## [2026-07-12] D-13 — Tenants de cliente generados dinámicamente, nunca a mano ni commiteados
- **Contexto:** Había que decidir cómo nacen las carpetas `clients/<CLIENTE>/` (bronze/silver/gold, input, manifest.json).
- **Decisión:** Los tenants **no se crean a mano ni se commitean**; se generan con el comando `zlk client new`, respaldado por un core `create_client(name, clients_root)` en `src/zeroleak/core/scaffold.py` (patrón heredado del proyecto hermano FODA, donde `client_scaffold` fue el primer feature fundacional). El tenant de demostración se llamará **`COMPANY_DEMO`** (no "SANDUCHERIA"), y operará sobre datos sintéticos. Este será el primer Tracer Bullet (T-12).
- **Consecuencias:** Ningún tenant debe versionarse en git; `.gitignore` sobre `clients/*/data/` (D-11) protege los datos, pero la carpeta del tenant en sí solo debe existir en el filesystem local tras ejecutar el comando.

## [2026-07-12] D-14 — Convención de carpeta de features: `610_features/`
- **Contexto:** Se necesitaba una carpeta para alojar los features construidos (uno por carpeta, artefactos directos por D-01 sin bandas), y `600_features` colisionaba en numeración con `600_template/` ya existente.
- **Decisión:** Se adopta **`610_features/`** como carpeta de features construidos; `600_template/` sigue siendo la carpeta de plantillas.
- **Consecuencias:** Se corrigieron todas las referencias rezagadas a `600_features` en `905_guideline/methodology.md`, `900_persistence/tasks.md` y `700_architecture/system_design.md`; se creó `610_features/README.md` como índice del folder.

## [2026-07-12] D-15 — Refactor estructural: código movido a `app/`; `clients/` permanece en la raíz
- **Contexto:** El repo tenía `config/`, `data_synthetic/`, `src/` y `tests/` sueltos en la raíz, mezclados con las carpetas de andamiaje SDD+TDD (`900_persistence`, `700_architecture`, etc.) y con `clients/` (data de runtime del tenant). Se buscaba una separación más clara entre "código del motor" y "andamiaje del proyecto/runtime".
- **Decisión:** Mover con `git mv` las carpetas `config/`, `data_synthetic/`, `src/` y `tests/` a `app/config/`, `app/data_synthetic/`, `app/src/` y `app/tests/`. La carpeta `clients/` **no** se mueve: permanece en la raíz del repo, hermana de `app/`, porque es data de runtime del tenant (no código empaquetado) y sigue bajo la regla `.gitignore clients/*/data/` de C-01. El core de scaffold (`create_client`) siempre recibe `clients_root` como parámetro explícito, en vez de asumir una ruta fija relativa a `app/`.
- **Consecuencias:** Actualizadas todas las referencias del repo: `pyproject.toml` (`packages = ["app/src/zeroleak"]`, `testpaths = ["app/tests"]`, `pythonpath = ["app/src"]`), los 9 agentes de desarrollo en `.claude/agents/`, templates (`600_template/plan.md`, `notebook.md`), `README.md`, `610_features/README.md`, `905_guideline/methodology.md` y el árbol + prosa de `700_architecture/system_design.md`. Verificado: `import zeroleak` funciona y `pytest` resuelve `testpaths: app/tests`. Toda mención futura a rutas de código debe usar el prefijo `app/`, mientras que las rutas de tenants siguen siendo `clients/<CLIENTE>/...` sin ese prefijo.

## [2026-07-13] D-16 — Nombres de los 3 YAML de `input/` en inglés
- **Contexto:** Tras cerrar el bucle TDD de `client_scaffold` (13/13 casos), los 3 YAML de `input/` del tenant se llamaban en español (`contrato_datos.yaml`, `reglas_negocio.yaml`, `finanzas.yaml`).
- **Decisión:** Renombrarlos a inglés: `contract_data.yaml`, `business_rules.yaml`, `finance.yaml` (archivo, clave interna del YAML y comentario guía). La prosa descriptiva del proyecto se mantiene en español; solo los nombres de archivo/clave técnica cambian a inglés.
- **Consecuencias:** Propagado a `app/src/zeroleak/core/scaffold.py`, `app/tests/test_scaffold.py`, `610_features/client_scaffold/spec.md`, `plan.md`, `state.json`, `client_scaffold.ipynb`, `700_architecture/system_design.md` y el tenant real `clients/COMPANY_DEMO` (regenerado). Toda mención futura a estos archivos en código/artefactos debe usar los nombres en inglés.
