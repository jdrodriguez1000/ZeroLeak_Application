# Feature Contract — contract_multifile

> Artefacto **a nivel feature**, creado por la **sesión principal** (humano + Claude Code) en el paso 2 del flujo.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de escribir la definición**.
> **Una feature = una construcción completa** (Opción A, sin bandas): un solo ciclo SDD+TDD la lleva a "terminado".

## Estrella Polar
Evolucionar el **Contrato de Datos** de un tenant para que **un solo** `input/contract_data.yaml` describa la
estructura esperada de **uno o varios archivos** de datos —no de uno solo—, materializando la forma acordada en
**D-18 resuelta**: `contract_data.archivos[].{nombre, columnas[]}`. El resultado sigue siendo un **objeto de
contrato validado en memoria** (o un **error de validación claro** que detiene el análisis), pero ahora capaz de
representar el caso real de un cliente, que casi nunca entrega un único archivo (p. ej. `clientes.csv` +
`ventas.csv`). Es el **segundo eslabón** del lector/validador de configuración (D-21/D-22): sigue asumiendo que el
YAML **ya existe** y solo se ocupa de **cargarlo y validarlo**, nunca de crearlo.

## Definición de "Terminado"
Condiciones que deben cumplirse para considerar la feature **terminada** (comportamiento end-to-end completo):
- La función core `load_contract(path) -> Contract` sigue siendo el **único punto de entrada**, con la misma firma,
  pero el `Contract` que devuelve pasa de tener `columnas: list[Columna]` a tener **`archivos: list[ArchivoContrato]`**,
  donde cada `ArchivoContrato` declara al menos:
  - **nombre** (identificador del archivo físico esperado, p. ej. `ventas.csv`),
  - **columnas** (la lista de columnas de ese archivo, con el **mismo** esquema de `Columna` vigente hoy:
    nombre / tipo / nulable / llave).
- **Se reutiliza lo ya construido y verificado en `config_contract` (T-43), no se reinventa:** el modelo `Columna`,
  el enum cerrado `TipoDato` de 6 tipos (D-23b), la detección de columnas duplicadas por cadena exacta (D-23e), el
  fail-fast de un solo error (D-23c) y las excepciones `ContractParseError` / `ContractSchemaError`. Esta feature
  **envuelve** ese núcleo en un nivel más de anidamiento; no lo reescribe.
- **Validación estructural del contrato en sí mismo** (bien formado), ahora en dos niveles:
  - **Nivel archivo:** lista `archivos` presente y no vacía; cada archivo con `nombre` y `columnas`; sin archivos
    duplicados por `nombre`. Los detalles exactos y casos límite se fijan en la spec.
  - **Nivel columna:** todo lo que ya valida hoy, **por archivo** (columnas no vacías, sin duplicados dentro del
    mismo archivo, tipos dentro del enum, campos requeridos presentes).
- Los **mensajes de error localizan el problema en el archivo correcto**: ante un contrato con varios archivos, el
  error dice **en cuál** de ellos está el defecto (no basta con el índice de columna, que hoy es ambiguo cuando hay
  más de un archivo). La forma exacta del mensaje se fija en la spec.
- **Bug T-56 resuelto como parte de esta feature:** un `contract_data.yaml` con la clave raíz `contract_data:`
  **presente pero con valor nulo** (el caso de la plantilla real vacía) produce un **`ContractSchemaError` claro**,
  no un `AttributeError`. Entra aquí porque el defecto vive en la **misma línea de extracción** que esta feature
  reescribe (`contract.py:115`); arreglarlo por separado antes sería trabajo desechado.
- **Plantilla actualizada (T-58):** `600_template/contract_data.yaml` refleja el esquema multi-archivo y **carga sin
  error** con el motor nuevo; la plantilla vigente (de un solo archivo) queda obsoleta al entrar esta feature.
- **Sin regresiones:** la suite completa queda en verde. Los tests de `config_contract` que asumen la forma vieja
  (`contract_data.columnas`) se **migran** a la forma nueva; el conjunto de comportamientos verificados no se
  reduce.
- **Frontera nítida (lo que define el alcance, D-21):** valida el contrato **contra su propio esquema**; **NO**
  compara nada contra ningún **CSV real** de bronze ni contra datos del cliente. Que el `nombre` declarado
  (`ventas.csv`) corresponda a un archivo realmente ingerido —y qué hacer con los sobrantes o los faltantes— es
  responsabilidad de **`load_data`** (etapa posterior), **no** de esta feature.
- **Motor como API (core-only, D-23d):** la operación vive en la función core; esta feature **no** expone fachada
  CLI, igual que `config_contract`.
- **Seguro por diseño (C-01):** se desarrolla y prueba **exclusivamente contra YAMLs sintéticos de ejemplo**. El
  contrato describe **estructura**, no PII; `input/` es material versionable (§7), no datos reales del cliente.

## Alcance
**In scope:**
- Modelo `ArchivoContrato` (nombre + columnas) y cambio de `Contract`: de `columnas` a `archivos: list[ArchivoContrato]`.
- Reutilización sin cambios de `Columna`, `TipoDato` (6 tipos), validador de duplicados de columna y excepciones
  `ContractParseError` / `ContractSchemaError`.
- Validación de nivel archivo: `archivos` no vacía, `nombre` presente, sin `nombre` de archivo duplicado.
- Validación de nivel columna **por archivo** (todo lo vigente hoy, aplicado dentro de cada archivo).
- **Localización del error por archivo** en los mensajes de `ContractSchemaError`.
- **T-56:** `contract_data:` presente con valor nulo → `ContractSchemaError` claro (no `AttributeError`).
- **T-58:** actualizar `600_template/contract_data.yaml` al esquema multi-archivo.
- **Migración de los tests existentes** de `config_contract` a la forma multi-archivo, sin perder cobertura.
- Fixtures sintéticos (YAMLs válidos e inválidos) con uno y con varios archivos.

**Out of scope (nunca, o en otra feature):**
- **Emparejar** el `nombre` declarado en el contrato con el archivo físico realmente ingerido en bronze; decidir qué
  pasa con los **extras** (ingeridos sin contrato) o los **faltantes** (contrato sin archivo). Es `load_data`
  (etapa posterior); D-18 documenta el comportamiento esperado, pero **no se construye aquí**.
- **Validar los datos** de un CSV contra el contrato (tipos reales, nulos reales, llaves reales) — `load_data`.
- Interpretar el `nombre` como patrón/glob (`ventas_pos_*.csv`) o cualquier forma de matching difuso: en esta
  feature `nombre` es una **cadena declarativa**, no un mecanismo de búsqueda.
- **Cargar/validar los otros YAMLs** (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores): cada uno es su
  propio tracer bullet por-YAML (D-21).
- **Ensamblar** el objeto único de config (`ClientConfig`/`ClientContext`) ni **reconciliar referencias cruzadas**
  entre YAMLs: paso final de integración pendiente de D-21, posterior.
- **Crear/autorear** el YAML por entrevista con stakeholders — entrevistador/autor, trabajo futuro (D-22, T-44).
- Exponer una fachada CLI para el contrato (se mantiene core-only, D-23d).
- Interpretar o ejecutar reglas de negocio, cálculos financieros o scoring.

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **verificables y detallados** viven en `spec.md` como `CA-xx`.
1. Dado un `contract_data.yaml` bien formado con **varios archivos**, `load_contract` devuelve un `Contract` cuya
   lista `archivos` refleja fielmente lo declarado: cada archivo con su `nombre` y su lista de columnas (nombre,
   tipo, nulable, llave), en el orden declarado.
2. Dado un `contract_data.yaml` bien formado con **un solo archivo**, funciona igual (el caso de un archivo es el
   caso general con `len(archivos) == 1`, no una rama especial).
3. Un contrato con la lista **`archivos` vacía o ausente** es rechazado con un `ContractSchemaError` claro.
4. Un archivo **sin `nombre`**, o con **`columnas` vacías/ausentes**, es rechazado con un `ContractSchemaError`
   claro que **identifica de qué archivo se trata**.
5. Dos archivos con el **mismo `nombre`** son rechazados con un `ContractSchemaError` claro.
6. Todas las validaciones de columna vigentes siguen aplicando **dentro de cada archivo**: campo requerido faltante,
   `tipo` fuera del enum de 6, columnas duplicadas por cadena exacta. El mensaje **localiza el archivo** además de
   la columna.
7. Un YAML **sintácticamente roto** sigue produciendo `ContractParseError`, distinguible del error de esquema.
8. Un YAML con `contract_data:` **presente pero nulo** produce un `ContractSchemaError` claro (**T-56**), nunca un
   `AttributeError`.
9. `600_template/contract_data.yaml` está en esquema multi-archivo y **carga sin error** con el motor nuevo
   (**T-58**).
10. La operación valida el contrato **contra su propio esquema únicamente**: no lee, abre ni requiere ningún CSV de
    bronze ni dato real del cliente (frontera con `load_data`, se mantiene el blindaje vigente).
11. La suite completa queda **en verde y sin regresiones**; los tests migrados conservan la cobertura de
    comportamiento de `config_contract`.

## Dependencias
- Feature **`config_contract` (T-43, ya en `main` vía PR #3)**: es el **cimiento** de esta feature. Aporta
  `load_contract`, `Contract`, `Columna`, `TipoDato`, los validadores y las excepciones que aquí se envuelven y
  extienden.
- Feature `client_scaffold` (T-21, ya en `main`): genera el tenant con `input/contract_data.yaml`.
- `900_persistence/decisions.md` **D-18 (🔒 resuelta, 2026-07-15)**: fija la forma exacta
  `contract_data.archivos[].{nombre, columnas}` y la secuencia (mergear PR #3 primero, multi-archivo como siguiente
  Tracer Bullet). También D-21 (descomposición por-YAML), D-22 (cargar vs crear) y D-23 (enum de 6 tipos, fail-fast,
  core-only, duplicados por cadena exacta).
- `900_persistence/tasks.md`: **T-57** (esta feature), **T-56** (bug del `contract_data:` nulo, absorbido aquí) y
  **T-58** (actualizar la plantilla, absorbido aquí).
- `700_architecture/system_design.md` §5 (los 4 YAMLs; YAML 1 = Contrato de Datos) y §7 (`input/` versionable, no PII).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda): se desarrolla solo con datos sintéticos.
- Librería **Pydantic** (motor de validación) y **PyYAML** (parser).

## Relación con Hitos de Producto
- **Cuarto Tracer Bullet** del proyecto (T-57) y **segundo eslabón** del lector/validador de configuración. Cierra
  la brecha entre el motor y la realidad del cliente: sin multi-archivo, el contrato solo puede describir clientes
  que entregan un único CSV, que no es el caso del nicho MVP (Retail Moderno entrega POS + clientes + catálogo…).
- Habilita directamente a **`load_data`** (validar cada CSV de bronze contra el contrato de *su* archivo) y, con
  ello, al resto del pipeline: reglas de negocio, cálculo de pérdidas y scoring.
