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
- [D-17] Alcance del segundo Tracer Bullet `ingest`: registro en bronze con dedupe por `sha256`, sin parsear contenido, allow-list `.csv`/`.xlsx`, entrada archivo o carpeta con recorrido plano
- [D-18] 🔒 **RESUELTA** — Contrato de datos multi-archivo: un solo `contract_data.yaml` con lista `archivos[].{nombre, columnas}`
- [D-19] Gate humano del notebook `ingest` (paso 5): nombrado en bronze con sufijo `__<sha8>`, exit codes 0/1/2, `duplicate` = no-op (SKIP)
- [D-20] Gate humano de la spec `ingest` (paso 7): extensiones case-insensitive, manifest de 4 campos exactos, `ingested_at` con `timespec` de segundos
- [D-21] `load_config` se descompone en tracer bullets por-YAML; se empieza por `config_contract` (leer + validar `contract_data.yaml`)
- [D-22] Dos procesos distintos y separados: **cargar/validar** los YAML (motor, ahora) vs **crear** los YAML por entrevista con subagentes (autoría, futuro)
- [D-23] Gate humano del notebook `config_contract` (paso 5): idioma ES de campos, enum de 6 tipos, errores fail-fast, core-only sin CLI
- [D-24] Gate humano del paso 13 `config_contract`: pruebas en verde, PR #3 pendiente de merge; forma multi-archivo de D-18 resuelta

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

## [2026-07-13] D-17 — Alcance del segundo Tracer Bullet `ingest`
- **Contexto:** Tras cerrar `client_scaffold` (T-21), había que decidir el alcance del siguiente feature: el comando que registra los archivos que el cliente entrega en la capa bronze del tenant.
- **Decisión:** `ingest` copia el archivo de forma inmutable/fiel a `clients/<CLIENTE>/data/bronze/`, calcula `sha256` y registra una entrada en `manifest.json` con status `pending` (formato §11 de `system_design.md`). **Dedupe por `sha256`:** reenviar el mismo archivo (mismo contenido) no lo duplica ni reprocesa, habilitando el Modo Incremental (§10). **Principio de diseño clave:** `ingest` **no parsea el contenido** del archivo — solo copia bytes y hashea ("archivador notarial"); el delimitador (`,`/`;`/`|`) y la estructura son problema del YAML 1 "Contrato de Datos" en una etapa posterior (`load_data`/`validate`), no de `ingest`; bronze guarda el original intacto. **Validación básica agnóstica de formato:** (a) el tenant destino existe; (b) el archivo de entrada existe y no está vacío; (c) su extensión está en una allow-list. No se valida "es un CSV legible" para no acoplar a un formato. **Allow-list del MVP:** `.csv` y `.xlsx` únicamente; `.txt` queda explícitamente fuera. **Entrada del comando = archivo o carpeta:** si es archivo, ingiere ese uno; si es carpeta, hace recorrido **plano** (solo primer nivel, sin recursión) filtrando por la allow-list; puede aceptar varios argumentos. Se prefirió el patrón "ingerir carpeta" sobre comodines/glob porque en PowerShell los comandos nativos no reciben el glob expandido (inconsistencia de shell); ingerir carpeta es agnóstico del shell y encaja con el modelo "el cliente deja su entrega de la quincena en una carpeta".
- **Consecuencias:** Pendiente definir en el `feature_contract.md` de `ingest`: firma exacta del comando (`zlk ingest <CLIENTE> <ruta>`), qué metadatos del manifest se llenan ahora vs. después (period, run_id probablemente vacíos hasta el procesamiento posterior). Este es el segundo Tracer Bullet del proyecto (T-28), sin rama ni artefactos creados aún.

## [2026-07-13] D-18 — 🔒 RESUELTA: contrato de datos multi-archivo
- **Estado original:** **ABIERTO** — decisión aún **no tomada**. A resolver cuando se construya el feature del **Contrato de Datos / `load_config`** (posterior a `ingest`).
- **Contexto:** Surgió al discutir el alcance de `ingest` (ver [D-17]). El `contract_data.yaml` describe **tipos/estructuras de archivo** (p. ej. "Ventas POS", "Rappi", "Clientes"), no una lista fija de nombres; un mismo contrato puede aplicar a varios archivos físicos (p. ej. 3 meses de POS). Como `ingest` es un "archivador notarial" que ingiere **todo** lo que caiga en la carpeta (filtrado solo por la allow-list `.csv`/`.xlsx`, D-17), puede haber desajuste entre lo ingerido y lo que el contrato describe: p. ej. **3 contratos pero 5 archivos** en la carpeta de carga. Ese desajuste **no rompe `ingest`**; se resuelve en la etapa de validación: un archivo se audita solo si hay un contrato que lo describa, los extras se marcan como *no reconocidos / omitidos* y los tipos esperados que no llegaron como *faltantes*.
- **Pregunta abierta (original):** ¿**cómo** se empareja cada archivo físico ingerido con su tipo de contrato? Opciones evaluadas: (a) **patrón de nombre** declarado en el contrato (ej. `match: "ventas_pos_*.csv"`); (b) **declaración/mapeo explícito** por parte del DS; (c) **sniffing de columnas** (inferir el tipo por su estructura). El `system_design.md` (§5) aún no fija el mecanismo.
- **Relacionado:** [D-17] (alcance de `ingest`), [D-10] (manifiesto con hash de contenido), §5 y §11 de `700_architecture/system_design.md`. Contexto adicional: los `input/*.yaml` los llena **el DS a mano** en el onboarding (guiado por el Maestro de Sectores, §12), conceptualmente después de `client new` y antes de validar; `ingest` no requiere que estén llenos.
- **[Resolución 2026-07-15]** En el gate humano del paso 13 de `config_contract`, el humano preguntó qué hacer con más de un archivo de datos; se verificó que el motor actual (`load_contract`) **no lo soporta** (solo entiende `contract_data.columnas` = un solo archivo; la forma anidada falla con un mensaje engañoso "la lista de columnas no puede estar vacía"). **Decisión:** un **solo** archivo `contract_data.yaml` por cliente, pero en su interior describe la configuración esperada de **uno o varios** archivos físicos que se cargarán más adelante, con esta forma:
  ```yaml
  contract_data:
    archivos:
      - nombre: clientes.csv
        columnas:
          - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
      - nombre: ventas.csv
        columnas:
          - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
  ```
  El modelo `Contract` pasa de tener `columnas` a tener `archivos` (lista de objetos con `nombre` + `columnas`), reutilizando `Columna`, el enum `TipoDato` de 6 tipos, la detección de duplicados y las excepciones `ContractParseError`/`ContractSchemaError` ya construidas. **Plan de secuencia:** mergear primero el PR #3 tal como está (el tracer bullet actual es cimiento del multi-archivo) y construir el multi-archivo como el **siguiente** Tracer Bullet (T-57), con su propia spec y su propio ciclo TDD; esto también implica actualizar `600_template/contract_data.yaml` (T-58).

## [2026-07-13] D-19 — Gate humano del notebook `ingest` (paso 5): nombrado, exit codes y duplicate=SKIP
- **Contexto:** Al aprobar `ingest.ipynb` (spike ejecutado con datos sintéticos), quedaban abiertos tres puntos de comportamiento observable que la spec (paso 6) necesitaba fijar como contrato formal.
- **Decisión:** (a) Ante colisión de **nombre** con **contenido distinto** en bronze, el archivo se almacena con sufijo `__<sha8>` (8 primeros hex del sha256) sin sobrescribir el original. (b) Exit codes del comando: `0` = éxito total; `1` = procesamiento parcial o fallo por ruta (ver D-17, no aborta el resto); `2` = fallo global por tenant inexistente (precondición). (c) Un archivo cuyo `sha256` ya está en el manifest es **no-op idempotente** (`duplicate`/SKIP): no se copia, no genera entrada nueva, y **no cuenta como fallo** (no afecta el exit code).
- **Consecuencias:** Estos tres puntos quedaron materializados en `610_features/ingest/spec.md` (CA-05, CA-06, CA-08, CA-09, CA-12) y validados en el bucle TDD (Casos 1, 4, 5).

## [2026-07-13] D-20 — Gate humano de la spec `ingest` (paso 7): defaults de validación y manifest
- **Contexto:** Al aprobar `spec.md` (12 CA), quedaban tres defaults de implementación por fijar antes de pasar al plan (paso 8).
- **Decisión:** (a) La comparación de **extensión** contra la allow-list (`.csv`/`.xlsx`) es **case-insensitive** (`.CSV`/`.Csv` también son válidos). (b) La entrada del manifest contiene **exactamente** 4 campos: `file`, `sha256`, `ingested_at`, `status` — la **ausencia** de `period`, `run_id` y `output` es verificable y forma parte del contrato (no son placeholders vacíos, simplemente no existen en esta etapa). (c) `ingested_at` se serializa en ISO-8601 con `timespec="seconds"` (sin microsegundos).
- **Consecuencias:** Materializado en CA-02 (forma del manifest) y validado en el Caso 3 del bucle TDD (test de caracterización, ver `lessons.md` L-13).

## [2026-07-14] D-21 — `load_config` se descompone en tracer bullets por-YAML; se empieza por `config_contract`
- **Contexto:** Cerrado y mergeado el segundo Tracer Bullet `ingest` (PR #2), se discutió cuál es la siguiente feature. Por orden de dependencias del pipeline (§4 de `system_design.md`), la etapa más temprana aún sin construir es `load_config` (leer + validar los 4 YAMLs de configuración). `ingest` la "saltó" a propósito porque es archivador notarial y no parsea contenido, pero todo lo aguas abajo (`load_data`, `vault`, módulos, `finance`) depende de la configuración cargada. El humano preguntó primero por la feature de mayor valor y luego por la siguiente por pura disciplina de dependencias; se acordó que, sin el filtro de "valor", la siguiente feature es `load_config`.
- **Decisión:** (a) **No** construir `load_config` como un feature monolítico, sino **descomponerlo en tracer bullets por-YAML**, porque los 4 YAMLs tienen naturalezas, esquemas y cadencias de cambio distintas (§5): Contrato de Datos (por archivo, dueño cliente), Reglas de Negocio (por sector/caso), Variables Financieras (por cliente), Maestro de Sectores (IP de ZeroLeak, global). (b) **Empezar por `config_contract`** = leer + validar `contract_data.yaml` con Pydantic, por ser el más autocontenido, el más concreto de validar, y el que habilita directamente a `load_data`. (c) **Frontera de alcance de `config_contract`:** valida que el contrato esté **bien formado en sí mismo** (lista de columnas, cada una con nombre/tipo/nulabilidad/llave); **NO** lo compara contra ningún CSV real de bronze — eso es responsabilidad de `load_data` (etapa posterior). Mantener esa línea nítida es lo que mantiene delgado al tracer bullet. (d) **Ensamblaje pendiente de no olvidar:** los N features por-YAML leen cada archivo por separado, pero ninguno arma el objeto único de config (`ClientConfig`/`ClientContext`) ni reconcilia las referencias cruzadas (`sector_id` de finanzas → Maestro de Sectores; reglas → columnas del contrato); tener presente desde ya un paso final pequeño de integración (o plegarlo en el último YAML). (e) El **Maestro de Sectores (YAML 4)** no se autorea por cliente: es IP interna de ZeroLeak. (f) Se desarrolla contra **YAMLs sintéticos de ejemplo** (C-01: el LLM solo ve datos sintéticos).
- **Consecuencias:** Próximo Tracer Bullet = `config_contract` (T-43), rama `feature/config_contract` desde `main`; `feature_contract.md` lo escribe la sesión principal (pasos 1-2 del flujo). Relacionado con [D-18] (punto abierto de emparejamiento archivo→contrato), que se revisitará al construir esta tanda de features. Complementa a [D-22].

## [2026-07-14] D-22 — Dos procesos separados: cargar/validar los YAML (ahora) vs crearlos por entrevista con subagentes (futuro)
- **Contexto:** El humano propuso crear uno o varios subagentes que **entrevisten a los stakeholders** con las preguntas correctas y cuyo resultado final sea **construir los 4 archivos YAML**. Se analizó la viabilidad y se detectó que "crear el YAML" y "cargar/validar el YAML" son dos procesos distintos y complementarios.
- **Decisión:** Separar explícitamente las dos responsabilidades y **secuenciarlas**: (a) el **lector/validador** (código del motor, determinista, Pydantic) que lee y valida un YAML — se construye **ahora** (empezando por `config_contract`, D-21), asumiendo que los YAML *ya existen* (como si un entrevistador los hubiera entregado); (b) el **entrevistador/autor** (subagente[s] de Claude) que elicita de los stakeholders y **redacta** los YAML — se difiere al **futuro**. Se construye el lector **primero** para que el entrevistador tenga después un esquema-objetivo y un juez de su propio trabajo (lazo cerrado: borrador → validar → repreguntar). **Guardarraíl C-01:** entrevistar sobre estructura/reglas/multiplicadores es **autoría de configuración** (`input/` es versionable, §7), no PII; el entrevistador **nunca** ingiere datos reales del cliente. Cada número financiero capturado es un **borrador para aprobación humana** (anticuerpo contra la "alucinación de costos" del premortem §16). Probablemente serán **3 entrevistas de cliente** (contrato/reglas/finanzas) + el Maestro de Sectores autoreado internamente; se empezará por **un** entrevistador (el del contrato) cuando llegue el momento.
- **Consecuencias:** La feature de creación por entrevista queda como trabajo **futuro** (T-44, No implementada). Su naturaleza —subagente de tiempo-de-desarrollo (`.claude/agents/`) vs capacidad de producto en el módulo `llm/` (§13)— queda por decidir al construirla. Prioridad actual = el lector/validador (D-21). Complementa a [D-21].

## [2026-07-14] D-23 — Gate humano del notebook `config_contract` (paso 5): idioma, enum de tipos, política de errores y core-only
- **Contexto:** Ejecutado y aprobado el spike `config_contract.ipynb` (paso 4, `notebook_writer`, con YAMLs sintéticos), se resolvieron con el humano los 3 puntos abiertos que la `definition.md` había delegado a la spec, más el idioma de los campos. Dato de terreno: el placeholder real de `contract_data.yaml` en el tenant (`client_scaffold`) está prácticamente vacío (solo la clave raíz `contract_data:` + comentario "completar"), por lo que **la clave raíz `contract_data` queda confirmada** pero los nombres internos de campos son terreno libre; `system_design.md` §5 describe el YAML 1 en español (columnas, tipos, nulos, llaves).
- **Decisión:** (a) **Idioma ES para campos**, por coherencia con todo el proyecto: raíz `contract_data.columnas`, y cada columna con `nombre`, `tipo`, `nulable`, `llave` (nada en inglés como `nullable`). (b) **Enum cerrado de 6 tipos:** `string, integer, float, date, datetime, boolean`. Racional: los decimales (`10.326`, `0.038`) los cubre `float` — la precisión monetaria exacta será tema de `finance.yaml` más adelante, no de la estructura; se distinguen explícitamente `date` (solo fecha) y `datetime` (fecha con hora) porque el cliente puede entregar ambos. (c) **Política de errores fail-fast:** se reporta el **primer** error claro y accionable, **sin agregación multi-error** (es config de tenant, no input masivo; agregar se puede añadir después si duele). (d) **Core-only, sin fachada CLI:** la feature expone solo `load_contract(path) -> Contract`; no se expone `zlk contract validate ...` en esta etapa (el consumidor real será `load_data`, que llama al core directo). HU-07 ya está redactada de forma neutral, así que core-only la cumple. (e) **Columnas duplicadas por nombre** se comparan como **cadena exacta**, sin normalizar mayúsculas/espacios (se mantiene el supuesto de la `definition.md`).
- **Consecuencias:** Estas 5 resoluciones son el insumo directo de `spec_writer` (paso 6), que las materializa en criterios `CA-xx` verificables enlazados a las HU. La distinción parseo vs esquema del spike (`ContractParseError` vs `ContractSchemaError`) sigue vigente para HU-04. Complementa a [D-21] y [D-22].
- **[Ratificación 2026-07-14]** Al llegar al paso 11 del flujo (`integration_tester`), el humano pidió lanzarlo; se le señaló que ejecutar una prueba de integración/CLI contradice (d) core-only. El humano decidió **mantener** `integration_tester` en `skipped`, confirmando (d) sin cambios. CA-13 (invocabilidad sin CLI) queda cubierto como caracterización dentro del bucle TDD (Caso 14), no por una prueba de integración separada.

## [2026-07-15] D-24 — Gate humano del paso 13 `config_contract`: pruebas en verde y forma multi-archivo de D-18
- **Contexto:** El humano ejecutó el gate humano del paso 13 (`human_test`) del Tracer Bullet `config_contract`: Prueba 0 (suite completa) y Prueba 1 (`pruebas_humanas.py`).
- **Decisión:** (a) Ambas pruebas quedaron en **verde** (88 passed; 7/7 OK), los 15 CA de la spec se mantienen cumplidos; el PR #3 queda **pendiente de aprobación y merge por el humano** (el agente no mergea, C-03). (b) Durante el gate se detectó un **bug no cubierto por ningún test** (ver `tasks.md` T-56: `AttributeError` en vez de `ContractSchemaError` cuando `contract_data:` tiene valor nulo); se decide **no bloquear** el merge del PR #3 por este bug (no corresponde a ningún CA de la spec) y resolverlo con su propio ciclo TDD después. (c) Se resolvió [D-18] (ver su entrada actualizada) con la forma multi-archivo `contract_data.archivos[]`, y se acordó que esa forma se construye como el **siguiente** Tracer Bullet (T-57), no como un ajuste del PR #3 actual.
- **Consecuencias:** Creados en esta sesión (pendientes de versionar) `600_template/contract_data.yaml` (plantilla comentada del esquema de un solo archivo, vigente hoy) y `610_features/config_contract/cargar_contrato.py` (cargador para probar un `contract_data.yaml` real escrito por el humano; fue este script el que destapó el bug de T-56). Complementa a [D-18], [D-21], [D-23].
