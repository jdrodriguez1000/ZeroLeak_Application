# Spec — config_contract

> Artefacto del paso 6 (`spec_writer`), escrito **después** de aprobar el notebook (spike, gate del paso 5). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate, paso 7) antes de planear. Materializa las 5 resoluciones de **D-23** como contrato (no opciones).

## Resumen
Una función core `load_contract(path) -> Contract` que **lee y valida** el `contract_data.yaml` de un tenant contra su propio esquema (Pydantic), devolviendo un objeto de contrato tipado en memoria o lanzando un error claro y accionable — sin tocar jamás un CSV real de bronze.

## Contratos de Datos / Artefactos

### Entrada — `contract_data.yaml` (YAML sintético; C-01)
Estructura esperada (idioma **ES** de campos, por **D-23a**):

```yaml
contract_data:          # clave raíz confirmada (D-23; placeholder de client_scaffold)
  columnas:             # lista NO vacía de columnas
    - nombre: <str>     # identificador de la columna (requerido)
      tipo: <enum>      # uno de los 6 tipos soportados (requerido)
      nulable: <bool>   # admite nulos (requerido)
      llave: <bool>     # forma parte de la clave del archivo (requerido)
```

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `input/contract_data.yaml` (o cualquier ruta que se le pase) | YAML | raíz `contract_data` → `columnas: list`; cada columna: `nombre: str`, `tipo: enum(6)`, `nulable: bool`, `llave: bool` |
| produce | objeto `Contract` en memoria (no se escribe a disco) | objeto Python tipado | `Contract.columnas: list[Columna]`; `Columna(nombre, tipo, nulable, llave)` |

**Enum cerrado de `tipo` (exactamente 6 valores, por D-23b):**
`string`, `integer`, `float`, `date`, `datetime`, `boolean`.
> Nota: el spike prototipó 5 tipos; la spec **añade `datetime`** (fecha con hora) por D-23b. `float` cubre decimales; la precisión monetaria es tema de `finance.yaml`, no de esta feature.

## Comportamiento Esperado
1. Se lee el archivo indicado por `path` y se parsea como YAML.
2. **Parseo (sintaxis):** si el texto no es YAML válido, se lanza `ContractParseError` (no se intenta validar esquema).
3. Del YAML parseado se toma la clave raíz `contract_data` y su lista `columnas`.
4. **Validación de esquema (Pydantic):** se valida contra el modelo `Contract`. Reglas:
   - `columnas` debe existir y ser una lista **no vacía**.
   - Cada columna debe declarar **los cuatro** campos requeridos: `nombre`, `tipo`, `nulable`, `llave`.
   - `tipo` debe pertenecer al **enum de 6 tipos**.
   - `nulable` y `llave` deben ser booleanos.
   - No puede haber **columnas duplicadas por `nombre`** (comparación de cadena **exacta**, sin normalizar mayúsculas/espacios — D-23e).
5. Si todo es válido, devuelve un `Contract` cuya lista `columnas` refleja fielmente lo declarado, en orden.
6. **Política de errores fail-fast (D-23c):** ante cualquier violación se reporta el **primer** error claro y accionable, **sin agregación multi-error**; **no** se devuelve objeto a medio construir.
7. **Frontera (D-21):** la operación depende **únicamente** del contenido del YAML; no abre, lee ni referencia ningún archivo bajo `data/bronze/` ni datos reales del cliente.

## Casos Límite y Errores
- **YAML sintácticamente roto** (indentación/estructura inválida) → `ContractParseError`, con mensaje claro; **distinguible por tipo** de un error de esquema.
- **Campo requerido faltante** en alguna columna (p. ej. `correo` sin `tipo`) → `ContractSchemaError` que identifica **qué campo** falta y **en qué columna** (índice/posición).
- **`tipo` fuera del enum** (p. ej. `numero_magico`) → `ContractSchemaError` que identifica el **valor inválido**, la **columna afectada** y enumera los valores permitidos.
- **`nulable`/`llave` no booleano** → `ContractSchemaError` indicando campo y columna.
- **Columnas duplicadas por nombre** (cadena exacta) → `ContractSchemaError` que nombra el/los `nombre` duplicado(s). Nombres que difieren solo en mayúsculas o espacios (p. ej. `test_id` vs `Test_ID`) **no** se consideran duplicados.
- **Lista de columnas vacía** (`columnas: []`) → `ContractSchemaError` ("la lista de columnas no puede estar vacía").
- **Clave `contract_data` o `columnas` ausente / YAML vacío** → `ContractSchemaError` (contrato mal formado, no error de parseo).
- En **todos** los casos de error, el valor de retorno es inexistente (se lanza excepción); nunca un objeto parcial.

## Interfaces / Firmas Públicas
- `load_contract(path) -> Contract` — única puerta de entrada del core; invocable directamente (tests, `load_data`, futura fachada). **Core-only: no hay CLI `zlk contract validate` en esta etapa (D-23d).**
- `Contract` — modelo con `columnas: list[Columna]`.
- `Columna` — modelo con `nombre: str`, `tipo: <enum de 6>`, `nulable: bool`, `llave: bool`.
- `ContractParseError` — error de **parseo** (YAML sintácticamente roto).
- `ContractSchemaError` — error de **esquema** (YAML bien formado, contrato mal formado).
> `ContractParseError` y `ContractSchemaError` son **distinguibles por tipo** (HU-04). Firmas a nivel de contrato; algoritmos internos y jerarquía fina de excepciones se deciden en el bucle TDD.

## Criterios de Aceptación (verificables)
> Cada criterio lleva un **código `CA-xx`** único y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado un YAML válido con N columnas, `load_contract` devuelve un objeto `Contract` con `len(columnas) == N`, en el mismo orden declarado. | HU-01 |
| CA-02 | Para cada columna del YAML válido, la columna resultante expone `nombre`, `tipo`, `nulable` y `llave` iguales a lo declarado (p. ej. `test_id`/`integer`/`false`/`true` → columna con esos cuatro valores). | HU-01 |
| CA-03 | Un YAML con los 6 tipos soportados (`string`, `integer`, `float`, `date`, `datetime`, `boolean`), uno por columna, se acepta y cada `tipo` se mapea a su valor de enum correspondiente. | HU-01, HU-03 |
| CA-04 | Un YAML donde una columna omite el campo `tipo` lanza `ContractSchemaError`; el mensaje identifica el campo faltante (`tipo`) y la columna afectada (índice/posición), y no se retorna objeto. | HU-02 |
| CA-05 | Un YAML donde una columna omite `nombre`, `nulable` o `llave` lanza `ContractSchemaError` indicando el campo faltante y la columna; no se retorna objeto. | HU-02 |
| CA-06 | Un YAML con `tipo: numero_magico` (valor fuera del enum) lanza `ContractSchemaError`; el mensaje identifica el valor inválido y la columna, y enumera los 6 valores permitidos. | HU-03 |
| CA-07 | Un archivo con sintaxis YAML inválida (p. ej. indentación rota) lanza `ContractParseError`, no `ContractSchemaError`; los dos tipos de error son distinguibles por su tipo de excepción. | HU-04 |
| CA-08 | El mensaje de `ContractParseError` es claro y accionable (referencia a que el YAML es sintácticamente inválido). | HU-04 |
| CA-09 | Un YAML con dos columnas de `nombre` idéntico (cadena exacta, p. ej. `test_id` y `test_id`) lanza `ContractSchemaError` que nombra el duplicado; no se retorna objeto. | HU-05 |
| CA-10 | Un YAML con dos columnas cuyos `nombre` difieren solo en mayúsculas o espacios (p. ej. `test_id` vs `Test_ID`) **no** se considera duplicado y no falla por esa causa (comparación exacta, D-23e). | HU-05 |
| CA-11 | Un YAML con `columnas: []` (lista vacía) lanza `ContractSchemaError` ("la lista de columnas no puede estar vacía"); no se retorna objeto. | HU-05 |
| CA-12 | Al cargar cualquier fixture (válido o inválido), la operación no abre ni referencia ninguna ruta bajo `data/bronze/`; instrumentando la apertura de archivos, la única ruta abierta es el propio `contract_data.yaml`. | HU-06 |
| CA-13 | `load_contract` es invocable directamente como función Python (sin argv, subprocess ni fachada CLI) y su firma es `load_contract(path) -> Contract`; no existe un comando `zlk contract validate` en esta feature (core-only, D-23d). | HU-07 |
| CA-14 | Ante un YAML que viola **más de una** regla a la vez (p. ej. campo faltante Y columnas duplicadas), se reporta **un único** primer error (fail-fast, D-23c); el resultado es una sola excepción, sin lista agregada de errores. | HU-02, HU-05 |
| CA-15 | Todos los fixtures usados en los tests (contratos válidos e inválidos) son YAMLs sintéticos versionables, sin PII ni datos reales de cliente, y ninguno reside bajo `clients/*/data/`. | HU-08 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` debe estar cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03 |
| HU-02 | CA-04, CA-05, CA-14 |
| HU-03 | CA-03, CA-06 |
| HU-04 | CA-07, CA-08 |
| HU-05 | CA-09, CA-10, CA-11, CA-14 |
| HU-06 | CA-12 |
| HU-07 | CA-13 |
| HU-08 | CA-15 |

## No-Objetivos
- **No** compara el contrato contra un **CSV real** de bronze ni valida que los datos del cliente lo cumplan — eso es `load_data` (etapa posterior; frontera D-21).
- **No** empareja el archivo físico ingerido con su tipo de contrato (D-18, punto abierto).
- **No** carga ni valida `business_rules.yaml`, `finance.yaml` ni el Maestro de Sectores (cada uno su propio tracer bullet).
- **No** ensambla `ClientConfig`/`ClientContext` ni reconcilia referencias cruzadas entre YAMLs.
- **No** crea/autorea el YAML por entrevista (autor/entrevistador, D-22); aquí el YAML **ya existe**.
- **No** expone una fachada CLI (`zlk contract validate ...`) en esta etapa (core-only, D-23d).
- **No** agrega múltiples errores en un solo reporte (fail-fast, D-23c); la agregación queda para una feature futura si se justifica.
- **No** interpreta ni ejecuta reglas de negocio, cálculos financieros ni scoring.
