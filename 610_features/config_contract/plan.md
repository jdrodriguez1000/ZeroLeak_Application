# Plan — config_contract

> Artefacto del paso 8 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate, paso 9) antes de arrancar el bucle.
>
> Base canónica: `spec.md` (CA-01 … CA-15, aprobada en el gate del paso 7, que materializa **D-23**), `definition.md` (HU-01 … HU-08), `feature_contract.md` (estrella polar y frontera D-21), `config_contract.ipynb` (spike aprobado, gate paso 5), `900_persistence/decisions.md` (D-21/D-22/D-23), `constraints.md` C-01. Patrón de referencia: la feature `ingest` ya construida (`ingest/core.py`, suite en `app/tests/`, fixtures en `conftest.py`).
>
> **Contexto técnico ya fijado por D-23 / gate (este plan lo honra, no lo reabre):**
> 1. **Core-only:** la feature expone únicamente `load_contract(path) -> Contract`; **no** hay fachada CLI `zlk contract validate` (D-23d) → **sin** tareas de `cli.py` ni de `integration_tester`.
> 2. **Idioma ES** de los campos (D-23a): `nombre`, `tipo`, `nulable`, `llave` bajo raíz `contract_data` → `columnas`.
> 3. **Enum cerrado de 6 tipos** (D-23b): `string`, `integer`, `float`, `date`, `datetime`, `boolean` (el spike prototipó 5; la spec **añade `datetime`**).
> 4. **Fail-fast** (D-23c): se reporta el **primer** error, **sin** agregación multi-error; nunca objeto a medio construir.
> 5. **Duplicados por cadena exacta** (D-23e): sin normalizar mayúsculas/espacios.
> 6. **Dos excepciones distinguibles por tipo:** `ContractParseError` (YAML roto) vs `ContractSchemaError` (esquema inválido).

## Enfoque Técnico

**Ubicación del módulo (decisión + justificación).** La feature es el **primer eslabón del eje de configuración** (`load_config`, §5; D-21/D-22) y habrá más tracer bullets por-YAML (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores), cada uno su propio módulo. Por coherencia con el patrón del paquete (cada dominio en su subpaquete: `ingest/`, `core/`, `vault/`, `finance/`, `report/`, `llm/`), se crea un **subpaquete nuevo `app/src/zeroleak/config/`** y la lógica de esta feature vive en **`config/contract.py`** (no en un `core.py` genérico, para dejar espacio a `config/business_rules.py`, `config/finance.py`, etc. sin colisionar). El `config/__init__.py` **reexporta** la superficie pública.

**Motor (core).** Toda la lógica vive en `app/src/zeroleak/config/contract.py`:

- `class TipoDato(str, Enum)` — enum **cerrado de 6 valores** (D-23b): `string`, `integer`, `float`, `date`, `datetime`, `boolean`.
- `class Columna(BaseModel)` — modelo Pydantic de una columna con los **cuatro** campos requeridos: `nombre: str`, `tipo: TipoDato`, `nulable: bool`, `llave: bool`.
- `class Contract(BaseModel)` — modelo con `columnas: list[Columna]` + dos `field_validator` sobre `columnas`:
  - **lista no vacía** (CA-11): mensaje estable `"la lista de columnas no puede estar vacía"`.
  - **sin nombres duplicados por cadena exacta** (CA-09/CA-10, D-23e): compara `nombre` sin normalizar; nombra el/los duplicado(s).
- `class ContractParseError(Exception)` — error de **parseo** (YAML sintácticamente roto).
- `class ContractSchemaError(Exception)` — error de **esquema** (YAML bien formado, contrato mal formado).
- `def load_contract(path) -> Contract` — **única puerta de entrada** (D-23d, HU-07). Orquesta:
  1. Lee el archivo indicado por `path` (única ruta que abre; frontera D-21, CA-12).
  2. `yaml.safe_load(...)`; ante `yaml.YAMLError` → `ContractParseError` con mensaje accionable (CA-07/CA-08).
  3. Toma la clave raíz `contract_data` → `columnas`; ausencia de la clave / YAML vacío se trata como **esquema** mal formado, no parseo (CA-11 y "clave ausente").
  4. `Contract.model_validate(...)`; ante `pydantic.ValidationError` → traduce a `ContractSchemaError` **extrayendo el primer error** (fail-fast, CA-14): sin lista agregada; el mensaje identifica campo/columna/valor según el caso.
  5. Devuelve el `Contract` tipado si todo es válido (CA-01/02/03).

**Política fail-fast (CA-14).** Pydantic por defecto **agrega** todos los errores en un único `ValidationError`. Para honrar D-23c (reportar el **primer** error, sin lista agregada), `load_contract` toma `e.errors()[0]` y construye un `ContractSchemaError` con **un solo** error claro (campo/columna/valor), en vez de propagar la cadena multi-error de Pydantic. Esa traducción es la pieza de producción específica de CA-14.

**Dependencias.** `pydantic>=2.7` y `pyyaml>=6.0` **ya están declaradas** en `pyproject.toml` — **no** se añade ninguna dependencia nueva.

**Fuera de alcance de este plan (frontera y core-only).** No se toca `cli.py` (no hay `zlk contract validate`, D-23d); no hay pruebas de integración por subprocess (`integration_tester`) porque no hay comando instalado; no se lee ni referencia ningún archivo bajo `data/bronze/` ni datos reales (D-21, CA-12).

## Archivos Afectados
- `app/src/zeroleak/config/__init__.py` — **crear** (subpaquete nuevo; reexporta `load_contract`, `Contract`, `Columna`, `TipoDato`, `ContractParseError`, `ContractSchemaError`).
- `app/src/zeroleak/config/contract.py` — **crear** (enum, modelos, validadores, excepciones y `load_contract`).
- `app/tests/conftest.py` — **modificar** (fixtures sintéticas nuevas: helper que escribe un `contract_data.yaml` sintético en `tmp_path` a partir de columnas/parametrización, y helpers de contratos válido/inválido; todo sintético, C-01).
- `app/tests/test_config_contract.py` — **crear** (unit tests del core `load_contract`, casos 1 … 15).

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición: un solo responsable, un solo entregable, codificar ≠ testear (test-first, la tarea de test antecede a la de código). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`. **Estado** ∈ `no_implementada | implementada | cancelada_suspendida`; el responsable es el único que actualiza el estado de su tarea (Single Writer Rule). Se crean todas en `no_implementada`.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Fixtures sintéticas para `config_contract`: helper `write_contract_yaml(dir, texto)` / factory que materializa un `contract_data.yaml` sintético en `tmp_path` a partir de una lista de columnas ficticias (`test_id`, `correo`, `monto`…), más contratos válido e inválidos reutilizables. Todo sintético, sin PII, nunca bajo `clients/*/data/` (C-01). | Adiciones a `app/tests/conftest.py` | tdd_tester | implementada | CA-15 (andamiaje), CA-01 |
| TSK-02 | Test: dado un YAML válido con N columnas, `load_contract` devuelve un `Contract` con `len(columnas) == N` y en el **mismo orden** declarado. | Test "valido-n-columnas-orden" en `test_config_contract.py` | tdd_tester | implementada | CA-01 |
| TSK-03 | Core mínimo: subpaquete `config/`, enum `TipoDato`, modelos `Columna`/`Contract`, excepciones, y `load_contract(path) -> Contract` que lee, parsea con `yaml.safe_load`, toma `contract_data.columnas`, valida con Pydantic y devuelve el `Contract` (camino feliz, count + orden). Reexport en `config/__init__.py`. | `config/contract.py` + `config/__init__.py` (camino feliz) | tdd_coder | implementada | CA-01 |
| TSK-04 | Test: para cada columna del YAML válido, la columna resultante expone `nombre`, `tipo`, `nulable` y `llave` **iguales** a lo declarado (p. ej. `test_id`/`integer`/`false`/`true`). | Test "fidelidad-de-campos" en `test_config_contract.py` | tdd_tester | implementada | CA-02 |
| TSK-05 | Fidelidad de campos de `Columna`: asegurar que los cuatro campos se mapean 1:1 desde el YAML (sin coerción no deseada); ajustar el modelo si el test lo exige. | Ajuste de `Columna` en `config/contract.py` | tdd_coder | cancelada_suspendida | CA-02 |
| TSK-06 | Test: un YAML con los **6 tipos** soportados (`string`, `integer`, `float`, `date`, `datetime`, `boolean`), uno por columna, se acepta y cada `tipo` se mapea a su valor de enum correspondiente. | Test "seis-tipos-enum" en `test_config_contract.py` | tdd_tester | implementada | CA-03 |
| TSK-07 | Enum `TipoDato` con **exactamente 6** valores (añade `datetime` respecto al spike, D-23b); cada valor aceptado y mapeado. | Enum de 6 valores en `config/contract.py` | tdd_coder | cancelada_suspendida | CA-03 |
| TSK-08 | Test: un YAML donde una columna **omite `tipo`** lanza `ContractSchemaError`; el mensaje identifica el campo faltante (`tipo`) y la columna afectada (índice/posición); no se retorna objeto. | Test "campo-tipo-faltante" en `test_config_contract.py` | tdd_tester | implementada | CA-04 |
| TSK-09 | Traducción `pydantic.ValidationError → ContractSchemaError` que preserva campo y columna (índice) del error de campo requerido faltante; no se retorna objeto. | Manejo de esquema en `load_contract` (`config/contract.py`) | tdd_coder | implementada | CA-04 |
| TSK-10 | Test: un YAML donde una columna omite `nombre`, `nulable` o `llave` lanza `ContractSchemaError` indicando el campo faltante y la columna; no se retorna objeto. | Test "otros-campos-faltantes" en `test_config_contract.py` | tdd_tester | implementada | CA-05 |
| TSK-11 | Asegurar que la traducción a `ContractSchemaError` cubre `nombre`/`nulable`/`llave` faltantes (campos requeridos del modelo), identificando campo y columna. | Ajuste de manejo de esquema en `config/contract.py` | tdd_coder | cancelada_suspendida | CA-05 |
| TSK-12 | Test: un YAML con `tipo: numero_magico` (fuera del enum) lanza `ContractSchemaError`; el mensaje identifica el **valor inválido**, la **columna**, y enumera los **6** valores permitidos. | Test "tipo-fuera-de-enum" en `test_config_contract.py` | tdd_tester | implementada | CA-06 |
| TSK-13 | Asegurar que el error de enum (`tipo` inválido) se traduce a `ContractSchemaError` con valor inválido, columna y lista de permitidos; ajustar el mensaje/traducción si el test lo exige. | Ajuste de manejo de esquema (enum) en `config/contract.py` | tdd_coder | implementada | CA-06 |
| TSK-14 | Test: un YAML con `columnas: []` (lista vacía) lanza `ContractSchemaError` con el mensaje `"la lista de columnas no puede estar vacía"`; no se retorna objeto. | Test "lista-vacia" en `test_config_contract.py` | tdd_tester | implementada | CA-11 |
| TSK-15 | `field_validator` de `Contract.columnas` que rechaza la lista vacía con mensaje estable `"la lista de columnas no puede estar vacía"`; incluye el caso de clave `contract_data`/`columnas` ausente o YAML vacío como esquema mal formado. | Validador "lista no vacía" en `config/contract.py` | tdd_coder | implementada | CA-11 |
| TSK-16 | Test: un YAML con dos columnas de `nombre` **idéntico** (cadena exacta, p. ej. `test_id` y `test_id`) lanza `ContractSchemaError` que **nombra el duplicado**; no se retorna objeto. | Test "duplicados-exactos" en `test_config_contract.py` | tdd_tester | implementada | CA-09 |
| TSK-17 | `field_validator` de `Contract.columnas` que detecta nombres duplicados por **cadena exacta** (sin normalizar mayúsculas/espacios, D-23e) y rechaza nombrando el/los duplicado(s). | Validador "sin duplicados" en `config/contract.py` | tdd_coder | implementada | CA-09 |
| TSK-18 | Test: un YAML con dos columnas cuyos `nombre` difieren solo en mayúsculas o espacios (`test_id` vs `Test_ID`) **no** se considera duplicado y no falla por esa causa (comparación exacta, D-23e). | Test "no-duplicado-por-caso/espacio" en `test_config_contract.py` | tdd_tester | implementada | CA-10 |
| TSK-19 | Test: un archivo con sintaxis YAML inválida (indentación rota) lanza `ContractParseError`, **no** `ContractSchemaError`; los dos tipos son distinguibles por tipo de excepción. | Test "yaml-roto-parse-error" en `test_config_contract.py` | tdd_tester | implementada | CA-07 |
| TSK-20 | En `load_contract`, capturar `yaml.YAMLError` del parseo y lanzar `ContractParseError` (antes de validar esquema), garantizando la distinción por tipo frente a `ContractSchemaError`. | Rama de parseo en `load_contract` (`config/contract.py`) | tdd_coder | implementada | CA-07 |
| TSK-21 | Test: el mensaje de `ContractParseError` es claro y accionable (referencia explícita a que el YAML es sintácticamente inválido). | Test "parse-error-mensaje-accionable" en `test_config_contract.py` | tdd_tester | implementada | CA-08 |
| TSK-22 | Componer el mensaje de `ContractParseError` de forma accionable (indica sintaxis YAML inválida, con detalle del parser); ajustar si el test lo exige. | Mensaje de `ContractParseError` en `config/contract.py` | tdd_coder | implementada | CA-08 |
| TSK-23 | Test: un YAML que viola **más de una** regla a la vez (p. ej. campo faltante Y columnas duplicadas) produce **una única** excepción (`ContractSchemaError`) con **un** primer error; no hay lista agregada de errores (fail-fast, D-23c). | Test "fail-fast-un-solo-error" en `test_config_contract.py` | tdd_tester | implementada | CA-14 |
| TSK-24 | Fail-fast en `load_contract`: al traducir `ValidationError`, tomar **solo el primer** error (`errors()[0]`) para construir `ContractSchemaError`, sin agregar la cadena multi-error de Pydantic. | Lógica fail-fast en `config/contract.py` | tdd_coder | cancelada_suspendida (sin entregable de código: CA-14 ya satisfecho por el fail-fast de TSK-09, `_mensaje_esquema` ya toma `exc.errors()[0]`; confirmado por inspección en paso 10/Caso 12, patrón de caracterización TSK-05/07/11) | CA-14 |
| TSK-25 | Test (frontera D-21): instrumentando la apertura de archivos (espía de `open`), `load_contract` sobre cualquier fixture (válido o inválido) abre **únicamente** el propio `contract_data.yaml`; **ninguna** ruta bajo `data/bronze/`. | Test "frontera-no-toca-bronze" en `test_config_contract.py` | tdd_tester | implementada | CA-12 |
| TSK-26 | Test (API core-only): `load_contract` es invocable **directamente** como función Python (sin argv/subprocess/CLI); su firma es `load_contract(path) -> Contract` y **no** existe un comando `zlk contract validate` (D-23d). | Test "core-invocable-sin-cli" en `test_config_contract.py` | tdd_tester | implementada | CA-13 |
| TSK-27 | Test (cumplimiento C-01): auditar que todos los fixtures usados (válidos e inválidos) son YAMLs **sintéticos**, sin PII, y ninguno reside bajo `clients/*/data/`. | Test "fixtures-sinteticos-sin-pii" en `test_config_contract.py` | tdd_tester | implementada | CA-15 |
| TSK-28 | Refactor de `config/contract.py` y `config/__init__.py` manteniendo verde: helpers cohesivos para la traducción de errores (campo/columna/valor), constantes de mensajes estables, docstrings con referencia a CA, tipado con generics de builtin (patrón del proyecto). | `config/contract.py` refactorizado | tdd_refactor | no_implementada | CA-01 … CA-14 (calidad) |

## Dependencias y Contratos
- **Consume:** `contract_data.yaml` (YAML 1 de 4, §5) — hoy un placeholder generado por `client_scaffold`; esta feature asume que **ya existe** con contenido (D-22, no lo crea). `pydantic>=2.7` y `pyyaml>=6.0` (ya en `pyproject.toml`; **sin** dependencia nueva). `constraints.md` C-01 (datos sintéticos).
- **Produce:** superficie pública `load_contract`, `Contract`, `Columna`, `TipoDato`, `ContractParseError`, `ContractSchemaError` bajo `zeroleak.config`. Objeto `Contract` **en memoria** (no se escribe a disco).
- **Habilita:** `load_data` (etapa posterior) — comparará el CSV real de bronze contra un contrato **ya validado**; y el ensamblado final de `ClientConfig`/`ClientContext` (posterior, D-21).
- **Frontera (D-21):** **no** abre, lee ni referencia ningún archivo bajo `data/bronze/` ni datos reales (CA-12); **no** empareja archivo físico ↔ contrato (D-18, abierto).

## Estrategia de Test
- **Unit (`test_config_contract.py`):** camino feliz (count+orden, fidelidad de campos, 6 tipos→enum); errores de esquema (campo faltante `tipo` y demás, tipo fuera de enum con lista de permitidos, lista vacía, duplicados exactos); no-duplicado por caso/espacio; error de parseo (YAML roto, distinto por tipo, mensaje accionable); fail-fast (una sola excepción ante múltiples violaciones); frontera (espía de `open`, nunca bronze); API core-only (invocable sin CLI, firma); y cumplimiento C-01 (fixtures sintéticos).
- **Integración:** **ninguna** en esta feature. Es **core-only** (D-23d): no hay comando instalado que ejecutar por subprocess, así que **no** hay tareas de `integration_tester`. La cobertura end-to-end se logra invocando `load_contract` directamente.
- **Fixtures / datos de prueba:** **sintéticos** (Regla "Datos en Bóveda", C-01). Los YAML se escriben en `tmp_path` (o cadenas inline) con columnas ficticias (`test_id`, `correo`, `monto`, `fecha_alta`, `activo`), reflejando las "matrices de mentiras" del spike. Ningún fixture reside bajo `clients/*/data/` ni contiene PII.

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Deben coincidir con `stages.tdd.cases[]` del `state.json` de la feature. Cada caso agrupa sus tareas de test y de código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | YAML válido con N columnas → `Contract` con `len(columnas) == N` en el mismo orden declarado. | TSK-01, TSK-02, TSK-03 | CA-01 |
| 2 | Cada columna expone `nombre`/`tipo`/`nulable`/`llave` iguales a lo declarado. | TSK-04, TSK-05 | CA-02 |
| 3 | YAML con los 6 tipos (`string`,`integer`,`float`,`date`,`datetime`,`boolean`), uno por columna, se acepta y cada `tipo` mapea a su enum. | TSK-06, TSK-07 | CA-03 |
| 4 | Columna que omite `tipo` → `ContractSchemaError` que identifica el campo faltante y la columna (índice); sin objeto. | TSK-08, TSK-09 | CA-04 |
| 5 | Columna que omite `nombre`/`nulable`/`llave` → `ContractSchemaError` indicando campo y columna; sin objeto. | TSK-10, TSK-11 | CA-05 |
| 6 | `tipo: numero_magico` (fuera del enum) → `ContractSchemaError` con valor inválido, columna y los 6 valores permitidos. | TSK-12, TSK-13 | CA-06 |
| 7 | `columnas: []` (lista vacía) → `ContractSchemaError` "la lista de columnas no puede estar vacía"; sin objeto. | TSK-14, TSK-15 | CA-11 |
| 8 | Dos columnas de `nombre` idéntico (cadena exacta) → `ContractSchemaError` que nombra el duplicado; sin objeto. | TSK-16, TSK-17 | CA-09 |
| 9 | Dos `nombre` que difieren solo en mayúsculas/espacios (`test_id` vs `Test_ID`) → **no** es duplicado, no falla por esa causa. | TSK-18 | CA-10 |
| 10 | YAML sintácticamente roto → `ContractParseError`, no `ContractSchemaError`; distinguibles por tipo. | TSK-19, TSK-20 | CA-07 |
| 11 | El mensaje de `ContractParseError` es claro y accionable (sintaxis YAML inválida). | TSK-21, TSK-22 | CA-08 |
| 12 | YAML que viola > 1 regla (campo faltante Y duplicados) → **una única** excepción, un primer error, sin lista agregada (fail-fast). | TSK-23, TSK-24 | CA-14 |
| 13 | Instrumentando `open`, `load_contract` abre solo el propio `contract_data.yaml`; ninguna ruta bajo `data/bronze/`. | TSK-25 | CA-12 |
| 14 | `load_contract` invocable directamente (sin argv/subprocess/CLI), firma `load_contract(path) -> Contract`; no existe `zlk contract validate`. | TSK-26 | CA-13 |
| 15 | Todos los fixtures son YAMLs sintéticos, sin PII, ninguno bajo `clients/*/data/`. | TSK-27 | CA-15 |

> **Refactor:** TSK-28 (`tdd_refactor`) se ejecuta manteniendo verde tras consolidar el core (típicamente hacia los últimos casos). **Sin** fase `integration_tester` (core-only, D-23d).
>
> **Nota sobre caracterización (patrón de `ingest`):** varios casos (9/CA-10, 12/CA-14 parcial, 13/CA-12, 14/CA-13, 15/CA-15) pueden resultar **caracterización** en vez de RED clásico si el core construido en casos previos ya los satisface como efecto colateral del diseño Pydantic (enum cerrado, comparación exacta, `load_contract` que solo abre el `path`). En ese caso el `tdd_tester` mantiene el test como regresión, reporta el hallazgo con honestidad y el `tdd_coder` marca su tarea de código pareja `cancelada_suspendida` (sin entregable) — igual que se hizo en `ingest` (Casos 3/8/9/11). CA-14 sí espera código real (extracción del primer error, TSK-24).

## Verificación de Cobertura (todo CA-xx tiene ≥ 1 TSK-xx)
| CA | Cubierto por |
|---|---|
| CA-01 | TSK-01, TSK-02, TSK-03, TSK-28 |
| CA-02 | TSK-04, TSK-05 |
| CA-03 | TSK-06, TSK-07 |
| CA-04 | TSK-08, TSK-09 |
| CA-05 | TSK-10, TSK-11 |
| CA-06 | TSK-12, TSK-13 |
| CA-07 | TSK-19, TSK-20 |
| CA-08 | TSK-21, TSK-22 |
| CA-09 | TSK-16, TSK-17 |
| CA-10 | TSK-18 |
| CA-11 | TSK-14, TSK-15 |
| CA-12 | TSK-25 |
| CA-13 | TSK-26 |
| CA-14 | TSK-23, TSK-24 |
| CA-15 | TSK-01, TSK-27 |

## Riesgos Técnicos / Decisiones a Validar en el Gate (paso 9)
- **Ubicación `config/contract.py` (subpaquete nuevo).** Se crea `app/src/zeroleak/config/` como hogar del eje de configuración (D-21/D-22), con la lógica en `contract.py` (no en un `core.py` genérico) para dejar espacio a los futuros tracer bullets por-YAML. **A validar** que ésta es la estructura deseada frente a, p. ej., alojar todo en `config/core.py`.
- **Fail-fast vs agregación de Pydantic (CA-14).** Pydantic **agrega** todos los errores en un `ValidationError`; el plan honra D-23c tomando **solo el primer** error (`errors()[0]`) al traducir a `ContractSchemaError`. El orden del "primer" error lo determina Pydantic (los `field_validator` de `columnas` corren **tras** validar cada `Columna`, como notó el spike): ante campo faltante Y duplicados, el error reportado será el de la columna. El test de CA-14 verifica **cardinalidad** (una sola excepción, sin lista agregada), no el texto exacto del error elegido. **A confirmar** que ese criterio es suficiente.
- **Clave raíz / `columnas` ausente = esquema, no parseo (spec §Casos límite).** Un YAML vacío o sin `contract_data`/`columnas` se trata como `ContractSchemaError` (contrato mal formado), no `ContractParseError`. El spike lo resolvía con `(crudo or {}).get("contract_data") or {}` → lista vacía → validador de "lista no vacía". Se mantiene ese criterio; **a validar** que el mensaje resultante es suficientemente claro para ese caso límite (podría no ser literalmente "lista vacía" si la clave falta).
- **Identificación de "columna afectada" por índice (CA-04/05/06).** Pydantic reporta la ubicación como `columnas.<índice>.<campo>` (0-based). El plan asume que **índice/posición** satisface "en qué columna"; no se numera desde 1 ni se usa el `nombre` (que puede faltar). **A confirmar** que el índice 0-based de Pydantic es aceptable como identificador de columna.
- **Mensaje accionable de `ContractParseError` (CA-08).** El test verifica que el mensaje **referencia** sintaxis YAML inválida (p. ej. contiene "YAML"), no un string frágil exacto; se compone envolviendo el detalle del `yaml.YAMLError`. **A validar** el nivel de detalle esperado.
- **Sin CLI ni integración (core-only, D-23d).** No hay tareas de `cli.py` ni de `integration_tester`; la observabilidad end-to-end se cubre invocando `load_contract` directamente (CA-13). Si en el futuro se decide exponer `zlk contract validate`, será otra feature/tarea; **el humano debe notar** esta ausencia deliberada.

---

**Siguiente paso:** gate humano (paso 9) para aprobar/rechazar este plan. **No** se arranca el bucle TDD (paso 10: `tdd_tester → tdd_coder → tdd_refactor`) hasta la aprobación.
