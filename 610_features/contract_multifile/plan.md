# Plan — contract_multifile

> Artefacto del paso 8 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate, paso 9) antes de arrancar el bucle.
>
> Base canónica: `spec.md` (**CA-01 … CA-28** + catálogo de mensajes **M-01 … M-13**, aprobada en el gate del paso 7 → **D-26**), `definition.md` (HU-01 … HU-12), `feature_contract.md` (frontera), `contract_multifile.ipynb` (spike ejecutado, gate paso 5 → **D-25**), `900_persistence/decisions.md` (**D-26**, **D-25**, **D-18**, **D-23**, D-21, D-22), `lessons.md` (**L-17**, **L-13/L-14**, **L-10**, L-16), `constraints.md` C-01. Cimiento: la feature `config_contract` ya en `main` (PR #3).
>
> **Contexto ya fijado por la spec / D-26 (este plan lo honra, no lo reabre):**
> 1. **Los textos M-01 … M-13 son contrato literal.** Los tests los fijan tal cual (igualdad exacta), no por subcadena.
> 2. **Core-only (D-23d):** firma real `load_contract(path) -> Contract`. El parámetro `estilo` del spike **no** existe en producción. Sin fachada CLI → **sin** tareas de `cli.py` ni de `integration_tester`.
> 3. **Orden de comprobaciones:** **M-02** (esquema viejo) y **M-13** (híbrido) se comprueban **ANTES** de Pydantic; si no, un defecto de columna dentro de `archivos[]` taparía el mensaje del residual.
> 4. **Reutilización, no reescritura:** `Columna`, `TipoDato` (6 tipos), el validador de columnas duplicadas, el fail-fast y `ContractParseError`/`ContractSchemaError` se reutilizan. Los dos `field_validator` de columna solo **cambian de casa** (de `Contract` a `ArchivoContrato`).
> 5. **Sin atajo de compatibilidad (D-25d):** no hay `Contract.columnas`; los tests se **migran** (CA-25).
> 6. **CA-21 es agnóstico al orden** (D-26b): verifica cardinalidad, no quién gana.

## Enfoque Técnico

**Ubicación.** No se crean módulos nuevos: la feature **evoluciona** `app/src/zeroleak/config/contract.py` (el mismo eje de configuración de D-21/D-22) y su reexport `app/src/zeroleak/config/__init__.py`.

**Motor (core), pieza a pieza:**

- **Se reutiliza sin tocar:** `TipoDato` (enum de 6, D-23b), `Columna` (4 campos), `ContractParseError`, `ContractSchemaError`, `_MENSAJE_YAML_INVALIDO` y la rama de parseo (`yaml.YAMLError → ContractParseError`, M-12).
- **`class ArchivoContrato(BaseModel)` — nuevo:** `nombre: str`, `columnas: list[Columna]`. **Recibe los dos `field_validator` que hoy viven en `Contract`** (`_columnas_no_vacias`, `_columnas_sin_duplicados`): mismo código, misma comparación por **cadena exacta** (D-23e), solo **cambian de casa** para validar las columnas **de ese archivo**. De ahí sale gratis el hallazgo 2 de D-25 (**duplicado de columna por archivo, no global**, CA-03).
- **`class Contract(BaseModel)` — cambia de forma:** `columnas: list[Columna]` → **`archivos: list[ArchivoContrato]`**, con dos `field_validator` nuevos: `_archivos_no_vacia` (**M-04**) y `_archivos_sin_duplicados` por cadena exacta (**M-05**, D-25b). **No** se añade propiedad `columnas` (D-25d, CA-24).
- **`load_contract(path) -> Contract` — misma firma (CA-27).** Secuencia:
  1. Abre **únicamente** `path` (frontera D-21, CA-23) y `yaml.safe_load` → `ContractParseError` con **M-12** si el YAML no parsea.
  2. **Extracción defensiva por tipo (T-56, ampliado):** `raiz = crudo if isinstance(crudo, dict) else {}`; `cuerpo = raiz.get("contract_data")`; si `not isinstance(cuerpo, dict)` → `ContractSchemaError` **M-01**. **Nunca** se encadena `.get(...).get(...)` → **jamás** un `AttributeError` (CA-19/CA-20). Sustituye la línea vigente `contract.py:115`.
  3. **Comprobaciones pre-Pydantic del residual (D-26, orden obligatorio):** con `columnas` presente en la raíz de `contract_data`, se bifurca por la **utilizabilidad de `archivos`** (lista no vacía):
     - sin `archivos` utilizable → **M-02** (esquema viejo, CA-08);
     - con `archivos` utilizable → **M-13** (híbrido, CA-28, se **rechaza**).
  4. **Nivel raíz de `archivos`:** normaliza ausente/nula a `[]`; si es un valor no-lista → **M-03** (CA-09).
  5. `Contract.model_validate({"archivos": archivos_crudos})`; ante `ValidationError` → `ContractSchemaError(_mensaje_esquema(exc, archivos_crudos))`.
  6. Devuelve el `Contract` en el orden declarado (CA-01/CA-02).
- **Traductor de errores — cambio de firma (hallazgo 3 de D-25).** El `nombre` del archivo **no viene** en el `ValidationError` cuando el defecto está en una columna: hay que recuperarlo del **YAML crudo por índice**. Por eso `_mensaje_esquema(exc)` → **`_mensaje_esquema(exc, archivos_crudos)`** (dos entradas), apoyado en un `_localizador_archivo(indice, archivos_crudos)` que devuelve `archivo[i] '<nombre>'` y **degrada a `archivo[i]`** cuando el archivo no declara `nombre` (D-25a, CA-10). Formas de `loc` a desarmar:
  | `loc` | Nivel | Mensajes |
  |---|---|---|
  | `('archivos',)` | raíz | M-04, M-05 |
  | `('archivos', i, campo)` | archivo | M-06, M-07, M-08 |
  | `('archivos', i, 'columnas', j, campo)` | columna | M-09, M-10, M-11 |
  La forma interna la fija el bucle TDD; lo observable es el mensaje.
- **Fail-fast (D-23c):** se mantiene `exc.errors()[0]`, sin agregación (CA-21).

**Plantilla (T-58, CA-22).** `600_template/contract_data.yaml` se reescribe al esquema `archivos[]` partiendo del texto ya propuesto y **ejecutado** en la celda 13 del spike (documenta las reglas nuevas de nivel archivo y que dos archivos distintos **sí** pueden tener columnas homónimas). Se elimina de paso la instrucción vigente que apunta a `610_features/config_contract/cargar_contrato.py`.

**Dependencias.** Ninguna nueva: `pydantic>=2.7` y `pyyaml>=6.0` ya están en `pyproject.toml`.

**Fuera de alcance del plan.** Sin `cli.py`, sin `integration_tester` (core-only, D-23d); sin emparejar `nombre` con archivos físicos ni abrir nada bajo `data/bronze/` (D-21); sin resolver la colisión `Ventas.csv`/`ventas.csv` (riesgo aceptado, diferido a **T-59**).

## Archivos Afectados
- `app/src/zeroleak/config/contract.py` — **modificar** (`ArchivoContrato`, `Contract.archivos`, validadores movidos y nuevos, extracción defensiva, comprobaciones pre-Pydantic M-02/M-13, traductor con dos entradas).
- `app/src/zeroleak/config/__init__.py` — **modificar** (reexportar `ArchivoContrato`).
- `600_template/contract_data.yaml` — **reescribir** al esquema multi-archivo (T-58).
- `app/tests/conftest.py` — **modificar** (`write_contract_yaml` migrado a `archivos=`; fixtures sintéticas multi-archivo).
- `app/tests/test_config_contract.py` → `app/tests/test_contract_multifile.py` — **renombrar (`git mv`) y migrar** (CA-25).

## Estrategia de migración de los tests (CA-25) — decisión visible en el gate

Los 15 tests vigentes prueban **el mismo módulo** que esta feature evoluciona. Mantener dos archivos de test sobre `zeroleak.config.contract` fragmentaría la suite, así que **se renombra** `test_config_contract.py` → `test_contract_multifile.py` (`git mv`, conserva historia) y ahí se consolidan viejos y nuevos.

La migración es **real, no cosmética**: **M-09 reordena la frase** respecto del texto vigente (`falta el campo requerido 'tipo' en la columna de índice 1` → `archivo[1] 'ventas.csv', columna de índice 1: falta el campo requerido 'tipo' (Field required)`), así que hay que reescribir **aserciones**, no solo fixtures.

Se hace en **dos tiempos**, para que la suite quede **verde en cada caso** del bucle:
1. **Migración de forma (TSK-03, Caso 1):** los 15 tests pasan a construir `contract_data.archivos[].columnas` y a leer `contrato.archivos[i].columnas`. Sus aserciones vigentes son **de subcadena** y sobreviven al traductor genérico; la **única** excepción es el test de `columnas: []`, cuya aserción de igualdad exacta se **relaja temporalmente a subcadena** y se **endurece al texto literal M-07** en el Caso 12.
2. **Endurecimiento por caso:** cada test viejo se reescribe al **texto literal M-xx** en el caso que especifica su comportamiento equivalente, según este inventario (auditado a cero por el Caso 25 / CA-25):

| Test vigente | Comportamiento | Caso destino |
|---|---|---|
| `..._valido_n_columnas_orden` | camino feliz, count + orden | Caso 1 (CA-01) / Caso 3 (CA-04) |
| `..._fidelidad_de_campos` | 4 campos 1:1 | Caso 2 (CA-02) |
| `..._seis_tipos_enum` | enum de 6 | Caso 5 (CA-05) |
| `..._campo_tipo_faltante` | campo requerido faltante | Caso 16 (CA-15, **M-09**) |
| `..._otros_campos_faltantes` (x3) | `nombre`/`nulable`/`llave` faltantes | Caso 16 (CA-15, **M-09**) |
| `..._lista_vacia` | `columnas: []` | Caso 12 (CA-11, **M-07**) |
| `..._tipo_fuera_de_enum` | tipo inválido | Caso 17 (CA-16, **M-10**) |
| `..._duplicados_exactos` | columna duplicada | Caso 18 (CA-17, **M-11**) |
| `..._no_duplicado_por_caso_o_espacio` | comparación exacta (sin CA nuevo propio) | Caso 18 (regresión, CA-25) |
| `..._fail_fast_un_solo_error` | cardinalidad | Caso 20 (CA-21) |
| `..._yaml_roto_parse_error` | tipo de excepción | Caso 19 (CA-18, **M-12**) |
| `..._parse_error_mensaje_accionable` | mensaje accionable | Caso 19 (CA-18) |
| `..._frontera_no_toca_bronze` | frontera D-21 | Caso 24 (CA-23, + guarda **L-17**) |
| `..._core_invocable_sin_cli` | core-only, firma | Caso 22 (CA-27) |
| `..._fixtures_sinteticos_sin_pii` | C-01 | Caso 26 (CA-26) |

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición: un solo responsable, un solo entregable, codificar ≠ testear (test-first: la tarea de test antecede a la de código). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`. **Estado** ∈ `no_implementada | implementada | cancelada_suspendida`; el **responsable es el único que actualiza el estado de su tarea** (Single Writer Rule). Todas se crean en `no_implementada`.
>
> `(car?)` = **candidata a caracterización** (L-13/L-14): puede quedar en verde de inmediato por efecto colateral del diseño; entonces el `tdd_tester` conserva el test como regresión, reporta el hallazgo con honestidad (verificándolo con la inyección temporal del defecto, **L-10**) y el `tdd_coder` marca su tarea `cancelada_suspendida` **sin entregable**. No se fuerza un RED artificial.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Migrar el helper `write_contract_yaml` a la forma multi-archivo: `write_contract_yaml(archivos=[{nombre, columnas:[...]}])` genera `contract_data.archivos[].columnas`; se **retira** el parámetro `columnas=` (que generaba el esquema viejo, hoy inválido) y se conserva `texto=` para fixtures crudos. | Helper migrado en `app/tests/conftest.py` | tdd_tester | implementada | CA-25 (andamiaje), CA-01 |
| TSK-02 | Fixtures sintéticas multi-archivo reutilizables: `clientes.csv` (3 columnas) + `ventas.csv` (4, incl. `cliente_id` homónimo y `vendida_en: datetime`), variante de un solo archivo, variante de **tres** archivos (añade `catalogo.csv`, 2 columnas: `sku`/`precio`) y variante de los 6 tipos. Sin PII, siempre en `tmp_path`, nunca bajo `clients/*/data/` (C-01). | Adiciones de fixtures a `app/tests/conftest.py` | tdd_tester | implementada | CA-26 (andamiaje), CA-01 |
| TSK-03 | **Migración de forma** de los 15 tests vigentes: `git mv test_config_contract.py test_contract_multifile.py` y reescritura de sus fixtures/lecturas a `archivos[].columnas`, relajando temporalmente a subcadena la única aserción de igualdad exacta (`columnas: []`, se endurece en el Caso 12). No se endurece ningún texto M-xx aquí. | `app/tests/test_contract_multifile.py` (migración de forma) | tdd_tester | implementada | CA-25 |
| TSK-04 | Test: YAML válido de 2 archivos → `len(archivos) == 2`, `[a.nombre …] == ['clientes.csv','ventas.csv']` (orden declarado) y `[len(a.columnas) …] == [3,4]`. | Test "valido-dos-archivos-orden" | tdd_tester | implementada | CA-01 |
| TSK-05 | Núcleo multi-archivo (camino feliz): `ArchivoContrato` con los dos `field_validator` de columna **mudados** desde `Contract`; `Contract.archivos: list[ArchivoContrato]`; `load_contract` toma `contract_data.archivos`, valida con Pydantic y devuelve el `Contract`; reexport de `ArchivoContrato` en `config/__init__.py`. | Núcleo de camino feliz en `config/contract.py` (+ superficie pública) | tdd_coder | implementada | CA-01 |
| TSK-06 | Test: cada columna expone `nombre`/`tipo`/`nulable`/`llave` iguales a lo declarado y en el orden declarado dentro de su archivo (p. ej. `archivos[1].columnas[0]` → `venta_id`/`integer`/`False`/`True`). | Test "fidelidad-de-campos-por-archivo" | tdd_tester | implementada | CA-02 |
| TSK-07 | `(car?)` Fidelidad 1:1 de los 4 campos de `Columna` anidada en `ArchivoContrato` (sin coerción no deseada); ajustar solo si el test lo exige. | Ajuste de modelos en `config/contract.py` | tdd_coder | cancelada_suspendida | CA-02 |
| TSK-08 | Test: YAML válido con **un solo** archivo → `len(archivos) == 1` y `archivos[0].columnas` contiene exactamente las mismas columnas (4 campos, mismo orden) que producía `Contract.columnas` en la forma anterior: un archivo es el caso general. | Test "un-archivo-caso-general" | tdd_tester | implementada | CA-04 |
| TSK-09 | `(car?)` Asegurar que el camino de un archivo **no** es una rama especial (misma ruta de código que N archivos); ajustar solo si el test lo exige. | Ajuste de `load_contract` en `config/contract.py` | tdd_coder | cancelada_suspendida (paso 10, Caso 3: sin entregable — `load_contract` ya usa una única ruta para 1 o N archivos desde TSK-05/Caso 1; honestidad verificada por inyección/reversión en TSK-08. pytest 86 passed/5 failed, sin regresión. Sigue trazando también a Caso 3b/CA-01, pendiente de que `tdd_tester` confirme TSK-08b) | CA-04 |
| TSK-08b | Test: YAML válido de **3** archivos (`clientes.csv` 3 columnas, `ventas.csv` 4, `catalogo.csv` 2) → `len(archivos) == 3`, `[a.nombre …] == ['clientes.csv','ventas.csv','catalogo.csv']` (orden declarado) y `[len(a.columnas) …] == [3,4,2]`. Cierra el hueco de **N ≥ 3** detectado en el gate (paso 9): el diseño no acota `archivos` (la única restricción es "no vacía", M-04) y ningún caso lo ejercitaba. Reutiliza el helper `write_contract_yaml` (TSK-01); **sin fixtures nuevos en disco**. Lado de código: **TSK-09** (misma ruta que 1 o 2 archivos, sin rama especial). | Test "valido-tres-archivos-orden" | tdd_tester | implementada | CA-01, CA-04 |
| TSK-10 | Test: `cliente_id` como columna de `clientes.csv` **y** de `ventas.csv` se acepta sin error (duplicado de columna **por archivo, no global**, D-25 hallazgo 2). | Test "columna-homonima-en-dos-archivos" | tdd_tester | implementada | CA-03 |
| TSK-11 | `(car?)` Alcance por-archivo del validador de columnas duplicadas (consecuencia de residir en `ArchivoContrato`); ajustar solo si el test lo exige. | Sin entregable — caracterización confirmada por el tester (honestidad verificada por inyección/reversión L-10, ver Caso 4 en `state.json`) | tdd_coder | cancelada_suspendida | CA-03 |
| TSK-12 | Test: YAML con los 6 tipos (`string`, `integer`, `float`, `date`, `datetime`, `boolean`), uno por columna dentro de un archivo, se acepta y cada `tipo` mapea a su valor de enum. | Test "seis-tipos-dentro-de-archivo" | tdd_tester | implementada | CA-05 |
| TSK-13 | `(car?)` Enum `TipoDato` de 6 valores aplicado dentro de `ArchivoContrato.columnas`; ajustar solo si el test lo exige. | Sin entregable — caracterización confirmada por el tester (honestidad verificada por inyección/reversión L-10, ver Caso 5 en `state.json`) | tdd_coder | cancelada_suspendida | CA-05 |
| TSK-14 | Test (T-56, parametrizado): `contract_data:` **nulo** y `contract_data: pendiente_de_completar` (**no-mapa**) → `ContractSchemaError` con el texto literal **M-01** (`… (se encontró: None)` / `… (se encontró: 'pendiente_de_completar')`); el test verifica además que **no** se propaga `AttributeError`. | Test "raiz-nula-o-no-mapa-M01" | tdd_tester | implementada | CA-19, CA-20 |
| TSK-15 | Extracción defensiva **por tipo** de la raíz: `isinstance` en vez de `.get(...).get(...)` (sustituye `contract.py:115`); si `contract_data` no es mapa → `ContractSchemaError` con **M-01** incluyendo el `repr` del valor encontrado. | Extracción defensiva de raíz en `config/contract.py` | tdd_coder | implementada | CA-19, CA-20 |
| TSK-16 | Test (parametrizado): `archivos: []`, clave `archivos` **ausente** y `archivos:` **nula** (los tres **sin** `columnas` en la raíz) → `ContractSchemaError` con el texto literal **M-04** (`la lista de archivos no puede estar vacía`); no se retorna objeto. | Test "archivos-vacia-ausente-nula-M04" | tdd_tester | implementada | CA-06, CA-07 |
| TSK-17 | Normalización de `archivos` ausente/nula a `[]` + `field_validator` `_archivos_no_vacia` de `Contract` con el mensaje estable **M-04**. | Validador "archivos no vacía" en `config/contract.py` | tdd_coder | implementada | CA-06, CA-07 |
| TSK-18 | Test: `archivos: ventas.csv` (valor no-lista) → `ContractSchemaError` con el texto literal **M-03** (`'archivos' debe ser una lista (se encontró: 'ventas.csv')`). | Test "archivos-no-lista-M03" | tdd_tester | implementada | CA-09 |
| TSK-19 | Guarda de tipo sobre `archivos` antes de Pydantic: si está presente y no es lista → `ContractSchemaError` con **M-03** y el `repr` del valor. | Guarda de tipo de `archivos` en `config/contract.py` | tdd_coder | implementada | CA-09 |
| TSK-20 | Test: YAML en el **esquema viejo** (`contract_data.columnas` con columnas válidas, **sin** `archivos`) → `ContractSchemaError` con el texto literal **M-02**, y **no** el genérico M-04 (D-25c). | Test "esquema-viejo-M02" | tdd_tester | implementada | CA-08 |
| TSK-21 | Comprobación **pre-Pydantic** del caso "esquema viejo": hay `columnas` en la raíz de `contract_data` y **no** hay `archivos` utilizable → `ContractSchemaError` con **M-02**. | Rama M-02 (pre-Pydantic) en `config/contract.py` | tdd_coder | implementada | CA-08 |
| TSK-22 | Test: YAML **híbrido** (`archivos` válida —que por sí sola cargaría sin error— **y además** `columnas` residual en la raíz) → `ContractSchemaError` con el texto literal **M-13**; no se retorna objeto. Incluye la verificación de **disyunción**: el fixture híbrido y el del esquema viejo (CA-08) producen mensajes **distintos**. | Test "hibrido-M13-y-disyuncion-con-M02" | tdd_tester | implementada | CA-28 |
| TSK-23 | Comprobación **pre-Pydantic** del caso **híbrido** (D-26a): hay `columnas` en la raíz **y** `archivos` es lista no vacía → `ContractSchemaError` con **M-13**; el contrato se **rechaza**, nunca se ignora el residual. Se sitúa **antes** de la validación de Pydantic y **disjunta** de la rama M-02 (TSK-21). **Tarea propia** (nota de riesgo de D-26): es la única regla de la feature sin código prototipado en el spike. | Rama M-13 (pre-Pydantic) en `config/contract.py` | tdd_coder | implementada | CA-28 |
| TSK-24 | Test: YAML de 2 archivos donde el segundo omite `nombre` → `ContractSchemaError` con el texto literal **M-06** (`archivo[1]: falta el campo requerido 'nombre' (Field required)`): el localizador **degrada limpio al índice**. | Test "archivo-sin-nombre-M06" | tdd_tester | implementada | CA-10 |
| TSK-25 | `_localizador_archivo(indice, archivos_crudos)`: devuelve `archivo[i] '<nombre>'` recuperando el `nombre` del **YAML crudo por índice**, y **degrada a `archivo[i]`** si el archivo no declara un `nombre` no vacío; + rama `missing` de nivel archivo del traductor (**M-06**). | Localizador de archivo en `config/contract.py` | tdd_coder | implementada | CA-10 |
| TSK-26 | Test: `archivos[1]` (`ventas.csv`) con `columnas: []` → `ContractSchemaError` con el texto literal **M-07** (`archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía`): índice **y** nombre. Endurece a igualdad exacta la aserción relajada en TSK-03. | Test "columnas-vacias-en-archivo-M07" | tdd_tester | implementada | CA-11 |
| TSK-27 | Rama `value_error` de nivel archivo del traductor (`loc == ('archivos', i, 'columnas')`): antepone el localizador al mensaje del validador mudado, sin la envoltura de "campo" que no aplica (**M-07**). | Rama M-07 del traductor en `config/contract.py` | tdd_coder | implementada | CA-11 |
| TSK-28 | Test: `archivos[1]` (`ventas.csv`) omite la clave `columnas` → `ContractSchemaError` con el texto literal **M-08** (`archivo[1] 'ventas.csv': falta el campo requerido 'columnas' (Field required)`). | Test "archivo-sin-columnas-M08" | tdd_tester | implementada | CA-12 |
| TSK-29 | Cobertura de **M-08** por la rama `missing` de nivel archivo: guarda ampliada de `loc[2] == "nombre"` a `loc[2] in ("nombre", "columnas")`. Verificado por inyección/reversión (L-10) que el defecto era real (fallback genérico se disparaba); no era caracterización. | Ajuste de la rama `missing` en `config/contract.py` (guarda `loc[2] in ("nombre", "columnas")`) | tdd_coder | implementada | CA-12 |
| TSK-30 | Test: contrato de **3** archivos con la colisión **no adyacente** (`ventas.csv`, `clientes.csv`, `ventas.csv`: `nombre` idéntico por cadena exacta en los índices **0 y 2**, separados por un archivo válido) → `ContractSchemaError` con el texto literal **M-05** (`nombre de archivo duplicado: 'ventas.csv'`), error de nivel raíz **sin** prefijo `archivo[i]`; no se retorna objeto. **La no adyacencia es deliberada** (endurecimiento del gate, paso 9): con dos `ventas.csv` contiguos en una lista de 2, un detector que solo compare el par vecino pasaría en verde y **no** vería este duplicado. Reutiliza `write_contract_yaml` (TSK-01); sin fixtures nuevos en disco. | Test "archivo-duplicado-no-adyacente-M05" | tdd_tester | implementada | CA-13 |
| TSK-31 | `field_validator` `_archivos_sin_duplicados` de `Contract.archivos`: detecta `nombre` repetido **sobre toda la lista** (conjunto/contador de los nombres ya vistos, **no** comparación por pares adyacentes), por **cadena exacta** (sin normalizar, D-25b/D-23e), y rechaza con **M-05** nombrando el nombre colisionado; + rama de nivel raíz del traductor (`loc == ('archivos',)`), que propaga el mensaje del validador sin prefijo. | Validador "archivos sin duplicados" en `config/contract.py` | tdd_coder | implementada | CA-13 |
| TSK-32 | Test: `Ventas.csv` y `ventas.csv` (difieren solo en mayúsculas) **cargan sin error**, `len(archivos) == 2` (comparación exacta, D-25b). Congela el **riesgo aceptado** de colisión física, diferido a `load_data` (**T-59**); esta feature no lo resuelve. | Test "mayusculas-no-son-duplicado" | tdd_tester | implementada | CA-14 |
| TSK-33 | Test: en un YAML de 2 archivos, la columna de índice 1 de `ventas.csv` omite `tipo` → `ContractSchemaError` con el texto literal **M-09** (`archivo[1] 'ventas.csv', columna de índice 1: falta el campo requerido 'tipo' (Field required)`): el nombre del archivo aparece **aunque Pydantic no lo reporte**. Endurece los tests migrados de campos faltantes (frase reordenada respecto del texto vigente). | Test "columna-sin-tipo-M09" | tdd_tester | implementada | CA-15 |
| TSK-34 | **Cambio de firma del traductor:** `_mensaje_esquema(exc)` → `_mensaje_esquema(exc, archivos_crudos)` (verificado ya vigente desde el Caso 9, sin tocar), y rama `missing` de nivel columna (`loc == ('archivos', i, 'columnas', j, campo)`) que compone **M-09** con el localizador de archivo + índice de columna. | Traductor de dos entradas (rama M-09) en `config/contract.py` | tdd_coder | implementada | CA-15 |
| TSK-35 | Test: `tipo: numero_magico` en la columna de índice 1 de `ventas.csv` → `ContractSchemaError` con el texto literal **M-10** (archivo, columna, valor inválido y los 6 permitidos). | Test "tipo-fuera-de-enum-M10" | tdd_tester | implementada | CA-16 |
| TSK-36 | Rama `enum` de nivel columna del traductor: compone **M-10** con localizador, índice de columna, `input` inválido y el mensaje nativo de Pydantic (que ya enumera los 6). | Rama M-10 del traductor en `config/contract.py` | tdd_coder | implementada | CA-16 |
| TSK-35b | Test: contrato de **3** archivos (`clientes.csv`, `ventas.csv`, `catalogo.csv`) con `tipo: numero_magico` en la columna de índice 1 de `ventas.csv` — el archivo **del medio**, con un archivo **válido detrás** en `archivos[2]` → `ContractSchemaError` con el **mismo** texto literal **M-10** (`archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': …`). El índice reportado ya **no** coincide con el del último archivo: mata el off-by-one y la implementación que localiza "el último" en vez del defectuoso. Reutiliza `write_contract_yaml` (TSK-01); sin fixtures nuevos en disco. Lado de código: **TSK-25** (localizador) + **TSK-36** (rama enum). | Test "tipo-fuera-de-enum-archivo-del-medio-M10" | tdd_tester | implementada | CA-16 |
| TSK-37 | Test: `ventas.csv` declara dos veces la columna `venta_id` → `ContractSchemaError` con el texto literal **M-11** (`archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'`). | Test "columna-duplicada-en-archivo-M11" | tdd_tester | implementada | CA-17 |
| TSK-38 | `(car?)` Cobertura de **M-11** por el validador mudado + la rama `value_error` de nivel archivo (TSK-27); ajustar solo si el test lo exige. | Ajuste de la rama `value_error` en `config/contract.py` | tdd_coder | cancelada_suspendida | CA-17 |
| TSK-39 | `(car?)` Test: archivo con sintaxis YAML inválida → `ContractParseError` (no `ContractSchemaError`), distinguibles **por tipo**, con el mensaje anteponiendo `el archivo YAML del contrato es sintácticamente inválido` (**M-12**, sin cambios respecto de `config_contract`). | Test "yaml-roto-M12" | tdd_tester | implementada | CA-18 |
| TSK-40 | `(car?)` Test: YAML que viola **dos** reglas a la vez (dos `ventas.csv` **y** `tipo` inválido en el segundo) → **exactamente una** `ContractSchemaError` con **un solo** mensaje, sin lista agregada de Pydantic. **Agnóstico al orden** (D-26b): acepta **M-05 o M-10** como conformes; **no** fija cuál gana. | Test "fail-fast-cardinalidad-agnostico" | tdd_tester | implementada | CA-21 |
| TSK-41 | `(car?)` Test: `Contract` **no** expone `columnas` — `'columnas' not in Contract.model_fields` y el acceso al atributo falla con `AttributeError`; la única vía es `archivos[i].columnas` (D-25d). | Test "contract-sin-columnas" | tdd_tester | implementada | CA-24 |
| TSK-42 | Test: `load_contract` invocable directamente como función Python (sin argv/subprocess/CLI); `inspect.signature` expone **exactamente** el parámetro `path` (sin `estilo`, que era solo del spike) y devuelve `Contract`; `zeroleak.cli` no registra ningún símbolo `contract` ni lo menciona en `_USAGE` (D-23d). | Test "core-invocable-firma-sin-cli" | tdd_tester | implementada | CA-27 |
| TSK-43 | Test (T-58): `load_contract("600_template/contract_data.yaml")` (la plantilla **real del repo**, resuelta desde la raíz del proyecto) no lanza excepción y devuelve `len(archivos) >= 1`, cada archivo con `nombre` no vacío y `columnas` no vacía; el archivo declara `contract_data.archivos` y **no** `contract_data.columnas`. | Test "plantilla-real-carga" | tdd_tester | implementada | CA-22 |
| TSK-44 | Reescribir `600_template/contract_data.yaml` al esquema multi-archivo (T-58) partiendo del texto propuesto y ejecutado en la celda 13 del spike: `archivos[]` con `clientes.csv`/`ventas.csv` de ejemplo, reglas de nivel archivo documentadas (al menos un archivo, `nombre` obligatorio, sin `nombre` duplicado, columnas homónimas legales entre archivos distintos) y sin la instrucción vigente que apunta a `cargar_contrato.py`. YAML sintético, sin PII. | `600_template/contract_data.yaml` reescrito | tdd_coder | implementada | CA-22 |
| TSK-45 | Test (frontera D-21 + **L-17**): con la apertura de archivos instrumentada (`monkeypatch` sobre `builtins.open` — **sí funciona bajo pytest**; el fallo de L-17 era exclusivo del kernel de Jupyter), cargar un contrato multi-archivo válido que **nombra** `clientes.csv` y `ventas.csv` observa **exactamente una** apertura, y es la del propio `contract_data.yaml`: ninguna ruta bajo `data/bronze/`, ninguna bajo `clients/`, ningún `.csv`. **Guarda de no-vacuidad primero** (el espía observó ≥ 1 apertura) antes de cualquier aserción de ausencia. | Test "frontera-no-toca-bronze-con-guarda" | tdd_tester | implementada | CA-23 |
| TSK-46 | Test/auditoría de migración (CA-25): la suite completa corre sin fallos y **ningún** test construye o afirma `contract_data.columnas` como forma **válida** (salvo los fixtures de CA-08 y CA-28, que la usan como caso **inválido**); el inventario de migración de este plan queda **en cero**. | Test "auditoria-migracion-sin-esquema-viejo" | tdd_tester | implementada | CA-25 |
| TSK-47 | Test (cumplimiento C-01): todos los fixtures (válidos e inválidos, de uno y de varios archivos) son YAMLs **sintéticos** sin PII y ninguno reside bajo `clients/*/data/`; amplía la lista blanca sintética con los nombres nuevos (`clientes.csv`, `ventas.csv`, `catalogo.csv`, `cliente_id`, `venta_id`, `vendida_en`, `sku`, `precio`). | Test "fixtures-sinteticos-sin-pii" | tdd_tester | no_implementada | CA-26 |
| TSK-48 | Refactor manteniendo verde: constantes para los mensajes **M-01 … M-13** (un único sitio donde vive cada texto congelado), helpers cohesivos para las comprobaciones pre-Pydantic y para el traductor por nivel de `loc`, docstrings con referencia a CA/M, tipado con generics de builtin (patrón del proyecto). | `config/contract.py` refactorizado | tdd_refactor | no_implementada | CA-01 … CA-28 (calidad) |

## Dependencias y Contratos
- **Consume:** `contract_data.yaml` (YAML 1 de 4, §5), que **ya existe** (D-22, no se crea aquí); `pydantic>=2.7` y `pyyaml>=6.0` (ya en `pyproject.toml`, **sin** dependencia nueva); `constraints.md` C-01.
- **Evoluciona (breaking):** la superficie pública de `zeroleak.config` — `Contract.columnas` **desaparece** y se sustituye por `Contract.archivos`; se añade `ArchivoContrato`. Único consumidor hoy: la suite de tests (se migra, CA-25). `Columna`, `TipoDato`, `ContractParseError`, `ContractSchemaError` no cambian.
- **Produce:** `600_template/contract_data.yaml` en esquema multi-archivo (T-58) y el objeto `Contract` **en memoria** (no se escribe a disco).
- **Cierra:** **T-56** (raíz nula/no-mapa → M-01, nunca `AttributeError`) y **T-58** (plantilla).
- **Habilita / difiere:** `load_data` comparará los CSV reales de bronze contra un contrato ya validado y resolverá la colisión `Ventas.csv`/`ventas.csv` (**T-59**).
- **Frontera (D-21):** no abre, lee ni referencia nada bajo `data/bronze/` ni `clients/` (CA-23); no empareja `nombre` ↔ archivo físico.

## Estrategia de Test
- **Unit (`app/tests/test_contract_multifile.py`):** camino feliz multi-archivo (count/orden, fidelidad, un archivo como caso general, **tres archivos como caso general sin cota**, 6 tipos, columna homónima entre archivos); raíz defensiva (M-01, T-56); nivel `archivos` (M-04, M-03, M-02, M-13); nivel archivo (M-06, M-07, M-08, M-05 con colisión **no adyacente**, y el no-duplicado por mayúsculas); nivel columna localizado (M-09, M-10 —también sobre el archivo **del medio** de tres—, M-11); parseo (M-12); fail-fast agnóstico al orden; ausencia de `Contract.columnas`; firma core-only; plantilla real; frontera con guarda de no-vacuidad; auditoría de migración y de C-01.
- **Integración:** **ninguna**. Core-only (D-23d): no hay comando instalado que ejecutar por subprocess → **sin** tareas de `integration_tester`. La cobertura end-to-end se logra invocando `load_contract` directamente.
- **Fixtures / datos de prueba:** **sintéticos** (Regla "Datos en Bóveda", C-01), escritos en `tmp_path` por `write_contract_yaml`. Vocabulario ficticio: `clientes.csv`/`ventas.csv`/`catalogo.csv`, columnas `cliente_id`, `correo`, `venta_id`, `vendida_en`, `monto`, `fecha_alta`, `activo`, `creado_en`, `sku`, `precio`. **Única excepción deliberada:** CA-22 lee la plantilla **real y versionada** `600_template/contract_data.yaml` — que es sintética por definición y no contiene datos de cliente.

## Casos de Test (bucle TDD)
Ordenados de simple a complejo, cimiento primero: **camino feliz → raíz → lista `archivos` → nivel archivo → nivel columna → transversales**. Deben coincidir con `stages.tdd.cases[]` del `state.json` de la feature. Cada caso agrupa sus tareas de test y de código.

> **Sufijo `b` (adiciones del gate, paso 9).** Los casos **3b** y **17b** (y sus tareas **TSK-08b** y **TSK-35b**) se **insertan junto a su caso hermano** en vez de renumerar los 26 casos originales: la numeración vigente ya está referenciada por el inventario de migración, la nota de caracterización y la tabla de cobertura, y renumerar solo añadiría ruido al diff del gate. El sufijo marca "adición de cobertura sobre un hermano ya especificado, mismo CA, sin mensaje M-xx nuevo".

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | YAML válido de 2 archivos → `len(archivos) == 2`, nombres en el orden declarado, `[3, 4]` columnas. | TSK-01, TSK-02, TSK-03, TSK-04, TSK-05 | CA-01, CA-25 |
| 2 | Cada columna expone `nombre`/`tipo`/`nulable`/`llave` iguales a lo declarado, en orden, dentro de su archivo. | TSK-06, TSK-07 | CA-02 |
| 3 | Un solo archivo → `len(archivos) == 1`, con las mismas columnas que producía la forma anterior: caso general, no rama especial. | TSK-08, TSK-09 | CA-04 |
| 3b | **3 archivos** válidos → `len(archivos) == 3`, nombres en el orden declarado, `[3, 4, 2]` columnas: N archivos es el caso general, sin rama especial ni cota superior. | TSK-08b, TSK-09 | CA-01, CA-04 |
| 4 | `cliente_id` en `clientes.csv` **y** en `ventas.csv` → se acepta (duplicado por archivo, no global). | TSK-10, TSK-11 | CA-03 |
| 5 | Los 6 tipos, uno por columna dentro de un archivo → aceptados y mapeados al enum. | TSK-12, TSK-13 | CA-05 |
| 6 | `contract_data:` nulo / no-mapa → `ContractSchemaError` **M-01** exacto, sin `AttributeError` (T-56). | TSK-14, TSK-15 | CA-19, CA-20 |
| 7 | `archivos: []` / ausente / nula (sin `columnas` en la raíz) → **M-04** exacto. | TSK-16, TSK-17 | CA-06, CA-07 |
| 8 | `archivos: ventas.csv` (no-lista) → **M-03** exacto. | TSK-18, TSK-19 | CA-09 |
| 9 | Esquema viejo (`columnas` en la raíz, sin `archivos` utilizable) → **M-02** exacto, no el genérico M-04. | TSK-20, TSK-21 | CA-08 |
| 10 | **Híbrido** (`archivos` válida **+** `columnas` residual) → **M-13** exacto, contrato rechazado; mensaje **distinto** del de CA-08. | TSK-22, TSK-23 | CA-28 |
| 11 | Archivo sin `nombre` → **M-06** exacto: el localizador degrada limpio a `archivo[1]`. | TSK-24, TSK-25 | CA-10 |
| 12 | `archivos[1] 'ventas.csv'` con `columnas: []` → **M-07** exacto (índice + nombre). | TSK-26, TSK-27 | CA-11 |
| 13 | `archivos[1] 'ventas.csv'` sin la clave `columnas` → **M-08** exacto. | TSK-28, TSK-29 | CA-12 |
| 14 | `ventas.csv`, `clientes.csv`, `ventas.csv`: duplicado **no adyacente** (índices 0 y 2, cadena exacta) → **M-05** exacto, sin prefijo `archivo[i]`. El detector mira **toda la lista**, no el par vecino. | TSK-30, TSK-31 | CA-13 |
| 15 | `Ventas.csv` vs `ventas.csv` → **cargan sin error**, `len(archivos) == 2` (riesgo aceptado, T-59). | TSK-32 | CA-14 |
| 16 | Columna de índice 1 de `ventas.csv` sin `tipo` → **M-09** exacto: el archivo aparece aunque Pydantic no lo reporte. | TSK-33, TSK-34 | CA-15 |
| 17 | `tipo: numero_magico` en `ventas.csv` → **M-10** exacto (archivo, columna, valor y los 6 permitidos). | TSK-35, TSK-36 | CA-16 |
| 17b | `tipo: numero_magico` en `ventas.csv` = `archivos[1]` de **3** archivos (el del **medio**, con `catalogo.csv` válido detrás) → **M-10** exacto: el índice localizado es el del archivo defectuoso, **no** el del último. | TSK-35b, TSK-25, TSK-36 | CA-16 |
| 18 | `venta_id` dos veces en `ventas.csv` → **M-11** exacto; + regresión: `test_id`/`Test_ID` **no** son duplicado (comparación exacta). | TSK-37, TSK-38 | CA-17, CA-25 |
| 19 | YAML sintácticamente roto → `ContractParseError` (**M-12**), distinguible por tipo de `ContractSchemaError`. | TSK-39 | CA-18 |
| 20 | Dos violaciones a la vez → **una única** excepción, un solo mensaje, sin agregación; **cualquiera** de M-05/M-10 es conforme. | TSK-40 | CA-21 |
| 21 | `Contract` no expone `columnas` (`model_fields` + `AttributeError`); única vía `archivos[i].columnas`. | TSK-41 | CA-24 |
| 22 | `load_contract(path) -> Contract` invocable directo, sin `estilo`, sin `zlk contract …`. | TSK-42 | CA-27 |
| 23 | `load_contract("600_template/contract_data.yaml")` (T-58) carga sin error, `len(archivos) >= 1`, y la plantilla declara `archivos`. | TSK-43, TSK-44 | CA-22 |
| 24 | Frontera: espía de `open` observa **exactamente 1** apertura (guarda de no-vacuidad primero, L-17) y es el propio YAML; nada de `data/bronze/`, `clients/` ni `.csv`. | TSK-45 | CA-23 |
| 25 | Auditoría de migración: suite verde, inventario en cero, ningún test usa `contract_data.columnas` como forma válida. | TSK-46 | CA-25 |
| 26 | Todos los fixtures son YAMLs sintéticos sin PII, ninguno bajo `clients/*/data/`. | TSK-47 | CA-26 |

> **Refactor:** TSK-48 (`tdd_refactor`) se ejecuta manteniendo verde tras consolidar el traductor (típicamente hacia los últimos casos). **Sin** fase `integration_tester` (core-only, D-23d).
>
> **Nota sobre caracterización (L-13/L-14).** Las tareas marcadas `(car?)` — TSK-07, TSK-09, TSK-11, TSK-13, TSK-29, TSK-38, TSK-39, TSK-40, TSK-41, TSK-42 — y sus casos (2, 3, **3b**, 4, 5, 13, 17*, 19, 20, 21, 22) son **candidatos serios a caracterización**: si el núcleo se reutiliza bien, quedan en verde de inmediato como efecto colateral del diseño (los validadores mudados a `ArchivoContrato`, el enum cerrado, `exc.errors()[0]` ya vigente, la rama de parseo intacta, la firma sin tocar). **No se fuerza un RED artificial**: el `tdd_tester` conserva el test como regresión, verifica su honestidad **inyectando temporalmente el defecto** (L-10) y el `tdd_coder` marca su tarea `cancelada_suspendida` sin entregable. Los casos que **sí** esperan código real: 1 (núcleo), 6 (T-56), 7, 8, 9 (M-02), **10 (M-13, la parte con menos evidencia)**, 11, 12, 14, 16 (cambio de firma del traductor), 17 (rama enum) y 23 (plantilla).

## Verificación de Cobertura (todo `CA-xx` tiene ≥ 1 `TSK-xx`)
| CA | Cubierto por |
|---|---|
| CA-01 | TSK-01, TSK-02, TSK-04, TSK-05, TSK-08b |
| CA-02 | TSK-06, TSK-07 |
| CA-03 | TSK-10, TSK-11 |
| CA-04 | TSK-08, TSK-09, TSK-08b |
| CA-05 | TSK-12, TSK-13 |
| CA-06 | TSK-16, TSK-17 |
| CA-07 | TSK-16, TSK-17 |
| CA-08 | TSK-20, TSK-21 |
| CA-09 | TSK-18, TSK-19 |
| CA-10 | TSK-24, TSK-25 |
| CA-11 | TSK-26, TSK-27 |
| CA-12 | TSK-28, TSK-29 |
| CA-13 | TSK-30, TSK-31 |
| CA-14 | TSK-32 |
| CA-15 | TSK-33, TSK-34 |
| CA-16 | TSK-35, TSK-36, TSK-35b |
| CA-17 | TSK-37, TSK-38 |
| CA-18 | TSK-39 |
| CA-19 | TSK-14, TSK-15 |
| CA-20 | TSK-14, TSK-15 |
| CA-21 | TSK-40 |
| CA-22 | TSK-43, TSK-44 |
| CA-23 | TSK-45 |
| CA-24 | TSK-41 |
| CA-25 | TSK-01, TSK-03, TSK-46 |
| CA-26 | TSK-02, TSK-47 |
| CA-27 | TSK-42 |
| CA-28 | TSK-22, TSK-23 |
| todos | TSK-48 (calidad, manteniendo verde) |

## Riesgos Técnicos / Decisiones a Validar en el Gate (paso 9)

1. **CA-28 / M-13 es la parte con menos evidencia detrás (nota de riesgo de D-26).** Es la **única** regla de la feature sin código prototipado en el spike: M-13 es texto nuevo y la comprobación pre-Pydantic no existía en el prototipo. Por eso lleva **tarea propia** (TSK-23) y **caso propio** (Caso 10), no colgada de la de M-02 (TSK-21/Caso 9). **A validar:** que la disyunción se implemente como dos ramas separadas y contiguas —"hay `columnas` en la raíz" → bifurcar por "¿`archivos` es lista no vacía?"— y que el Caso 10 verifique explícitamente que los dos fixtures dan mensajes distintos. **Riesgo residual:** la definición operativa de "`archivos` utilizable" (lista no vacía **sin** validar su contenido) hace que un YAML con `columnas` residual **y** `archivos: [ {…roto…} ]` dé **M-13**, no el error del ítem — es lo que exige el orden fijado por la spec, pero conviene que el humano lo vea escrito.

2. **Renombrar `test_config_contract.py` → `test_contract_multifile.py` y migrar en dos tiempos.** Alternativa descartada: mantener dos archivos de test sobre el mismo módulo. La migración **no puede** hacerse de golpe al texto literal M-xx sin dejar la suite roja durante media docena de casos, así que se hace **de forma** en el Caso 1 y se **endurece por caso** según el inventario. Esto implica **una** aserción temporalmente relajada (la de `columnas: []`, hasta el Caso 12), explícitamente inventariada y auditada por el Caso 25. **A validar:** que la ventana de aserción relajada es aceptable, y que renombrar (en vez de duplicar) el archivo de tests es lo deseado.

3. **Cambio de firma del traductor (`_mensaje_esquema(exc, archivos_crudos)`).** El `nombre` del archivo no viaja en el `ValidationError`; se recupera del YAML crudo por índice. Consecuencia: el traductor **depende del crudo**, no solo de Pydantic, y el índice puede en teoría no existir en la lista cruda. El plan asume la degradación del spike (`archivo[i]` sin nombre) para todo caso en que el crudo no ofrezca un `nombre` **str no vacío**. **A confirmar** que esa degradación silenciosa por robustez es aceptable y no debe reportarse de otro modo.

4. **CA-22 lee un archivo versionado, fuera de `tmp_path`.** Es el único test que abre un archivo real del repo (`600_template/contract_data.yaml`) y necesita resolver la raíz del proyecto desde `app/tests/` (p. ej. `Path(__file__).resolve().parents[2]`). Interactúa con la auditoría C-01 (Caso 26), que debe tratarlo como **excepción declarada** (plantilla sintética, sin PII). **A confirmar** el mecanismo de resolución de la ruta y la excepción en la auditoría.

5. **Cambio breaking de la superficie pública.** `Contract.columnas` desaparece (D-25d). Hoy el único consumidor es la suite; si existiera cualquier otro (script suelto, notebook fuera de `610_features/`), quedará roto sin aviso del compilador. **El humano debe notar** que se acepta el breaking a cambio de no tener dos formas de leer lo mismo.

6. **Volumen del bucle: 28 casos.** Es casi el doble de `config_contract` (15), aunque ~11 son candidatos a caracterización y deberían resolverse baratos. **A confirmar** que no se prefiere agrupar (p. ej. fundir los casos 12/13 —M-07 y M-08— o 21/22 en uno solo) a cambio de perder la trazabilidad 1:1 caso ↔ mensaje congelado.

7. **Cobertura de N ≥ 3 — hueco detectado y aprobado en el gate (paso 9).** El diseño soporta N archivos **sin cota** (`Contract.archivos: list[ArchivoContrato]`, sin `max_length`; la única restricción es "no vacía", M-04), pero **ningún** caso de la versión original del plan ejercitaba N ≥ 3: todos los válidos usaban 1 o 2 archivos. Eso dejaba **dos tests que podían pasar en verde con una implementación defectuosa**:
   - **Detector de duplicados (M-05):** con dos `ventas.csv` **adyacentes** en una lista de 2, una comparación por pares vecinos pasa y **no** ve un duplicado no adyacente. → **Caso 14 endurecido** a 3 archivos con la colisión en los índices **0 y 2** (TSK-30), y **TSK-31** reescrito para describir el validador **sobre toda la lista** (conjunto/contador), no por pares.
   - **Localizador `archivo[i]` (TSK-25):** todos los errores de nivel archivo y columna apuntaban a `archivo[1]` de un contrato de 2, donde el índice 1 es **también el último**; un off-by-one, o una implementación que reporte el índice del último archivo, pasaba los 26 casos. → **Caso 17b** (TSK-35b): la misma violación **M-10** sobre el archivo **del medio** de tres, con uno válido detrás.
   - Más el **camino feliz de 3 archivos** (**Caso 3b**, TSK-08b), que fija que N archivos es el caso general.

   **Por qué M-10 y no M-07 para el caso del medio** (ambos estaban sobre la mesa): la rama de nivel archivo (`value_error`, TSK-27) que produce **M-07** ya tiene **dos usuarios independientes** del localizador (Caso 12 / M-07 y Caso 18 / M-11), mientras que la rama de **nivel columna** solo lo ejercita con `archivo[1]` = último. Además `loc == ('archivos', i, 'columnas', j, campo)` es la forma **más profunda**: discrimina a la vez el índice de archivo y el de columna, así que un mismo test mata el "reporta el último" **y** una confusión entre `i` y `j`. **Sin texto nuevo:** el literal M-10 de la spec ya está redactado sobre `archivo[1] 'ventas.csv', columna de índice 1`, que se conserva **exacto** en un contrato de 3. **A validar:** que 3 casos añadidos (2 tests, 0 tareas de código nuevas — el lado de código son TSK-09, TSK-25, TSK-31 y TSK-36, ya existentes) es el precio correcto por cerrar el hueco.

8. **`monkeypatch` sobre `builtins.open` bajo pytest (CA-23).** L-17 fue un fallo **exclusivo del kernel de Jupyter**; bajo pytest el parche sí funciona (lo prueba el test vigente de CA-12, que hoy observa exactamente 1 apertura). **No** se arrastra el workaround del notebook. Lo que **sí** se conserva de L-17 es la **guarda de no-vacuidad**: primero se afirma que el espía observó ≥ 1 apertura, y solo entonces la ausencia de bronze.

---

**Siguiente paso:** **gate humano (paso 9)** para aprobar/rechazar este plan. **No** se arranca el bucle TDD (paso 10: `tdd_tester → tdd_coder → tdd_refactor`) hasta la aprobación.
