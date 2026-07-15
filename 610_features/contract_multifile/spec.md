# Spec — contract_multifile

> Artefacto del paso 6 (`spec_writer`), escrito **después** de aprobar el notebook (spike, gate del paso 5). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate, paso 7) antes de planear. Materializa como contrato (no como opciones) las **4 resoluciones y los 4 hallazgos de D-25**, y mantiene vigentes **D-18** (forma multi-archivo) y **D-23** (enum de 6, fail-fast, core-only, duplicados por cadena exacta).

## Resumen
La misma función core `load_contract(path) -> Contract` pasa a leer y validar un `contract_data.yaml` que describe **uno o varios archivos** (`contract_data.archivos[].{nombre, columnas[]}`), devolviendo un `Contract` tipado en memoria o un `ContractSchemaError`/`ContractParseError` que **dice en cuál archivo** está el defecto — sin abrir jamás un CSV de bronze.

## Contratos de Datos / Artefactos

### Entrada — `contract_data.yaml` (YAML sintético; C-01)
Forma fijada por **D-18** (idioma ES de campos, D-23a):

```yaml
contract_data:                # clave raíz; debe contener un MAPA (nunca nula)
  archivos:                   # lista NO vacía de archivos
    - nombre: clientes.csv    # cadena declarativa del archivo esperado (requerido)
      columnas:               # lista NO vacía de columnas DE ESE archivo
        - {nombre: cliente_id, tipo: integer,  nulable: false, llave: true}
        - {nombre: correo,     tipo: string,   nulable: true,  llave: false}
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id,   tipo: integer,  nulable: false, llave: true}
        - {nombre: cliente_id, tipo: integer,  nulable: false, llave: false}   # legal: mismo nombre, otro archivo
        - {nombre: vendida_en, tipo: datetime, nulable: false, llave: false}
```

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `input/contract_data.yaml` (o cualquier ruta que se le pase) | YAML | raíz `contract_data` (mapa) → `archivos: list`; cada archivo: `nombre: str`, `columnas: list` (no vacía); cada columna: `nombre: str`, `tipo: enum(6)`, `nulable: bool`, `llave: bool` |
| requiere/actualiza | `600_template/contract_data.yaml` (**T-58**) | YAML | la plantilla se reescribe a la forma `archivos[]` y debe cargar sin error con el motor nuevo |
| produce | objeto `Contract` en memoria (no se escribe a disco) | objeto Python tipado | `Contract.archivos: list[ArchivoContrato]`; `ArchivoContrato(nombre: str, columnas: list[Columna])`; `Columna(nombre, tipo, nulable, llave)` |

**Enum cerrado de `tipo` (exactamente 6 valores, D-23b, sin cambios):** `string`, `integer`, `float`, `date`, `datetime`, `boolean`.

### Catálogo de mensajes congelados (D-25a)
Los textos de abajo son **contrato**: los tests los fijan literalmente. Salvo `M-02`, todos provienen de salidas reales del spike aprobado.

| ID | Situación | Mensaje exacto (excepción) |
|---|---|---|
| M-01 | `contract_data` nulo o no-mapa | `la clave raíz 'contract_data' debe contener un mapa con la lista 'archivos' (se encontró: <repr>)` → p. ej. `(se encontró: None)`, `(se encontró: 'pendiente_de_completar')` |
| M-02 | contrato en el **esquema viejo** (hay `columnas` en la raíz y **no** hay `archivos` utilizable) | `el contrato usa el esquema anterior de un solo archivo: se encontró 'columnas' en la raíz de 'contract_data'; ahora las columnas van dentro de 'archivos[]' (contract_data.archivos[].columnas)` |
| M-03 | `archivos` presente pero no es lista | `'archivos' debe ser una lista (se encontró: <repr>)` |
| M-04 | `archivos: []`, ausente o nula (sin `columnas` en la raíz) | `la lista de archivos no puede estar vacía` |
| M-05 | `nombre` de archivo duplicado (nivel raíz) | `nombre de archivo duplicado: 'ventas.csv'` |
| M-06 | archivo sin `nombre` (**degradación**: no hay nombre con qué identificar) | `archivo[1]: falta el campo requerido 'nombre' (Field required)` |
| M-07 | archivo con `columnas: []` | `archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía` |
| M-08 | archivo sin la clave `columnas` | `archivo[1] 'ventas.csv': falta el campo requerido 'columnas' (Field required)` |
| M-09 | columna con campo requerido faltante | `archivo[1] 'ventas.csv', columna de índice 1: falta el campo requerido 'tipo' (Field required)` |
| M-10 | `tipo` fuera del enum de 6 | `archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor 'numero_magico' inválido (Input should be 'string', 'integer', 'float', 'date', 'datetime' or 'boolean')` |
| M-11 | `nombre` de columna duplicado dentro de un archivo | `archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'` |
| M-12 | YAML sintácticamente roto | `el archivo YAML del contrato es sintácticamente inválido: <detalle de PyYAML>` (sin cambios respecto de `config_contract`) |
| M-13 | contrato **híbrido** (hay `archivos` válida **y además** un `columnas` residual en la raíz) | `el contrato declara 'archivos[]' y además un 'columnas' residual en la raíz de 'contract_data': ese bloque no se valida ni se audita; elimínelo y deje cada columna dentro del archivo al que pertenece (contract_data.archivos[].columnas)` |

**Regla de localización (D-25a, "índice + nombre"):** el prefijo es `archivo[i] '<nombre>'` cuando el archivo declara un `nombre` no vacío, y **degrada a `archivo[i]`** cuando no lo declara. Los índices son **0-based** (archivo y columna). La opción "solo nombre" quedó **descartada con evidencia** en el spike y no se implementa.

## Comportamiento Esperado
1. Se lee el archivo indicado por `path` y se parsea como YAML. Si el texto no es YAML válido → `ContractParseError` (**M-12**), sin intentar validar esquema.
2. **Extracción defensiva de la raíz (T-56, ampliado por hallazgo 1 de D-25):** se comprueba **por tipo** que `contract_data` sea un mapa. Si es **nula** o **no-mapa** (cadena, lista, número…) → `ContractSchemaError` (**M-01**). Nunca se encadena `.get(...).get(...)`, de modo que **jamás** se propaga un `AttributeError`.
3. **Presencia de `columnas` en la raíz de `contract_data` (D-25c y D-26):** un `columnas` en la raíz **nunca** se ignora en silencio, porque un bloque de configuración que el motor no audita y tampoco denuncia es exactamente la fuga silenciosa que ZeroLeak existe para evitar. Se distinguen **dos casos disjuntos**, por la presencia de una `archivos` utilizable:
   - **Esquema viejo** — hay `columnas` en la raíz y **no** hay `archivos` utilizable (ausente, nula o vacía) → `ContractSchemaError` con **M-02** (en vez del genérico M-04), que orienta a la forma nueva.
   - **Híbrido** — hay `columnas` en la raíz **y** `archivos` es una lista no vacía → `ContractSchemaError` con **M-13**, que dice qué sobra y qué hacer. El contrato se **rechaza**: no se valida contra la `archivos` declarada ignorando el resto.
   Ambos casos se comprueban **antes** de validar el esquema con Pydantic, de modo que el mensaje del residual no queda tapado por un defecto de nivel archivo o columna.
4. **Nivel raíz de `archivos`:** si está presente pero no es una lista → **M-03**. Si está ausente, nula o vacía (y no aplica el punto 3) → **M-04**.
5. **Validación de esquema (Pydantic), nivel archivo:** cada elemento de `archivos` debe declarar `nombre` (**M-06** si falta) y `columnas` (**M-08** si falta), con `columnas` **no vacía** (**M-07**). No puede haber dos archivos con el **mismo `nombre`** comparado como **cadena exacta**, sin normalizar mayúsculas ni espacios (**M-05**, D-25b, simetría con D-23e).
6. **Validación de esquema, nivel columna, aplicada DENTRO de cada archivo** (todo lo vigente de `config_contract`, sin reescribir el núcleo): cuatro campos requeridos (**M-09**), `tipo` en el enum de 6 (**M-10**), y sin `nombre` de columna duplicado **dentro del mismo archivo** por cadena exacta (**M-11**).
7. **Alcance del duplicado de columna: por archivo, no global (hallazgo 2 de D-25).** Un mismo `nombre` de columna (p. ej. `cliente_id`) declarado en `clientes.csv` **y** en `ventas.csv` es **legal** y no produce error.
8. **Localización del archivo en errores de columna (hallazgo 3 de D-25):** el `nombre` del archivo **no viene** en el error de Pydantic cuando el defecto está en una columna; se recupera del **YAML crudo por índice**. El traductor de errores recibe, por tanto, **dos entradas** (el `ValidationError` y la lista cruda de archivos) — un cambio de firma respecto del `_mensaje_esquema(exc)` vigente. La forma interna la fija el bucle TDD; lo observable es el mensaje.
9. Si todo es válido, devuelve un `Contract` cuya lista `archivos` refleja fielmente lo declarado, **en el orden declarado**, y dentro de cada archivo sus columnas también en orden.
10. **Fail-fast (D-23c):** ante cualquier violación se reporta el **primer** error claro, **sin agregación multi-error**; nunca se devuelve un objeto a medio construir. **Orden observado (hallazgo 4 de D-25):** los `field_validator` de lista corren **después** de validar cada ítem, de modo que un contrato con un archivo roto **y** nombres de archivo duplicados reporta primero el error **del ítem**.
11. **Frontera (D-21):** el resultado depende **únicamente** del contenido del YAML. El `nombre` es una **cadena declarativa**: no se resuelve, no se busca y no se abre. La única ruta abierta es el propio `contract_data.yaml`.
12. **Sin atajo de compatibilidad (D-25d):** **no** existe una propiedad `Contract.columnas` que aplane las columnas de todos los archivos. Los tests y consumidores se migran a `archivos[].columnas`.

## Casos Límite y Errores
- **YAML sintácticamente roto** → `ContractParseError` (**M-12**), distinguible **por tipo** de cualquier `ContractSchemaError`.
- **`contract_data:` nulo** (plantilla vacía real, T-56) y **`contract_data: pendiente_de_completar`** (no-mapa) → `ContractSchemaError` (**M-01**), nunca `AttributeError`.
- **Contrato del esquema viejo** (`contract_data.columnas` sin `archivos` utilizable; el caso realista durante la migración, incl. `COMPANY_DEMO`) → `ContractSchemaError` (**M-02**).
- **Contrato híbrido** (`archivos` válida **y** `columnas` residual en la raíz) → `ContractSchemaError` (**M-13**): se **rechaza**, nunca se ignora el residual (D-26).
- **`archivos: []` / `archivos:` nula / clave ausente** → `ContractSchemaError` (**M-04**).
- **`archivos: "algo"`** (no lista) → `ContractSchemaError` (**M-03**).
- **Archivo sin `nombre`** → **M-06**, con degradación limpia a `archivo[i]`.
- **Archivo con `columnas: []` o sin la clave `columnas`** → **M-07** / **M-08**, identificando `archivo[i] '<nombre>'`.
- **Dos archivos con el mismo `nombre` exacto** → **M-05**.
- **`Ventas.csv` vs `ventas.csv`** → **NO** son duplicados: el contrato **carga sin error** (D-25b, comparación exacta). **Riesgo aceptado explícitamente:** en Windows/macOS son el mismo fichero físico; la colisión se resuelve en `load_data` (**T-59**). Esta feature **no** intenta resolverla.
- **Columna con campo faltante / `tipo` inválido / duplicada dentro del archivo** → **M-09** / **M-10** / **M-11**.
- **Mismo nombre de columna en archivos distintos** → **válido**, no es error.
- En **todos** los casos de error se lanza excepción; nunca se retorna un objeto parcial.

## Interfaces / Firmas Públicas
- `load_contract(path) -> Contract` — **única** puerta de entrada del core, con la **misma firma de hoy**. **Core-only (D-23d): sin fachada CLI.** El parámetro `estilo` del spike era **solo del prototipo** y **no** forma parte de esta spec.
- `Contract` — modelo con **`archivos: list[ArchivoContrato]`** (reemplaza `columnas: list[Columna]`). **No** expone `columnas` (D-25d).
- `ArchivoContrato` — modelo con `nombre: str`, `columnas: list[Columna]` (no vacía).
- `Columna` — modelo con `nombre: str`, `tipo: <enum de 6>`, `nulable: bool`, `llave: bool` (**reutilizado sin cambios** de `config_contract`).
- `TipoDato` — enum cerrado de 6 valores (reutilizado sin cambios).
- `ContractParseError` / `ContractSchemaError` — reutilizadas sin cambios; **distinguibles por tipo**.
> Firmas a nivel de contrato. Los algoritmos internos (incluida la firma exacta del traductor de errores del punto 8) los decide el bucle TDD.

## Criterios de Aceptación (verificables)
> Cada criterio lleva un **código `CA-xx`** único y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado un YAML válido con 2 archivos (`clientes.csv` con 3 columnas y `ventas.csv` con 4), `load_contract` devuelve un `Contract` con `len(archivos) == 2`, `[a.nombre for a in archivos] == ['clientes.csv', 'ventas.csv']` (orden declarado) y `[len(a.columnas) for a in archivos] == [3, 4]`. | HU-01 |
| CA-02 | En ese mismo contrato, cada columna expone `nombre`, `tipo`, `nulable` y `llave` iguales a lo declarado y en el orden declarado dentro de su archivo (p. ej. `archivos[1].columnas[0]` → `venta_id`/`integer`/`False`/`True`). | HU-01 |
| CA-03 | Un YAML donde `cliente_id` aparece como columna de `clientes.csv` **y** de `ventas.csv` se acepta sin error: el duplicado de columna es **por archivo, no global** (D-25, hallazgo 2). | HU-01, HU-06 |
| CA-04 | Un YAML válido con **un solo** archivo devuelve un `Contract` con `len(archivos) == 1`, y `archivos[0].columnas` contiene exactamente las mismas columnas (mismos 4 campos, mismo orden) que producía `Contract.columnas` en la forma anterior: un archivo es el caso general, no una rama especial. | HU-02 |
| CA-05 | Un YAML con los 6 tipos (`string`, `integer`, `float`, `date`, `datetime`, `boolean`), uno por columna dentro de un archivo, se acepta y cada `tipo` se mapea a su valor de enum. | HU-02, HU-06 |
| CA-06 | Un YAML con `contract_data.archivos: []` lanza `ContractSchemaError` con mensaje exactamente `la lista de archivos no puede estar vacía` (**M-04**); no se retorna objeto. | HU-03 |
| CA-07 | Un YAML con la clave `archivos` **ausente o nula** y **sin** `columnas` en la raíz de `contract_data` lanza `ContractSchemaError` con el mensaje **M-04**. | HU-03 |
| CA-08 | Un YAML en el **esquema viejo** (`contract_data.columnas` con columnas válidas, sin `archivos`) lanza `ContractSchemaError` cuyo mensaje es **M-02** (dice que el contrato usa el esquema anterior y orienta a `archivos[]`), y **no** el genérico M-04 (D-25c). | HU-03 |
| CA-09 | Un YAML con `archivos:` de valor no-lista (p. ej. `archivos: ventas.csv`) lanza `ContractSchemaError` con mensaje `'archivos' debe ser una lista (se encontró: 'ventas.csv')` (**M-03**). | HU-03 |
| CA-10 | Un YAML de 2 archivos donde el segundo omite `nombre` lanza `ContractSchemaError` con mensaje exactamente `archivo[1]: falta el campo requerido 'nombre' (Field required)` (**M-06**): el localizador **degrada limpio al índice** cuando no hay nombre. | HU-04 |
| CA-11 | Un YAML donde `archivos[1]` (`ventas.csv`) declara `columnas: []` lanza `ContractSchemaError` con mensaje exactamente `archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía` (**M-07**): índice **y** nombre. | HU-04 |
| CA-12 | Un YAML donde `archivos[1]` (`ventas.csv`) omite la clave `columnas` lanza `ContractSchemaError` con mensaje exactamente `archivo[1] 'ventas.csv': falta el campo requerido 'columnas' (Field required)` (**M-08**). | HU-04 |
| CA-13 | Un YAML con dos archivos de `nombre` idéntico (`ventas.csv` y `ventas.csv`, cadena exacta) lanza `ContractSchemaError` con mensaje exactamente `nombre de archivo duplicado: 'ventas.csv'` (**M-05**, error de nivel raíz, sin prefijo `archivo[i]`); no se retorna objeto. | HU-05 |
| CA-14 | Un YAML con dos archivos llamados `Ventas.csv` y `ventas.csv` (difieren solo en mayúsculas) **carga sin error** y devuelve `len(archivos) == 2`: la comparación es de **cadena exacta**, sin normalizar (D-25b). El riesgo de colisión física está aceptado y diferido a `load_data` (T-59); esta feature no lo resuelve. | HU-05 |
| CA-15 | Un YAML de 2 archivos donde la columna de índice 1 de `ventas.csv` omite `tipo` lanza `ContractSchemaError` con mensaje exactamente `archivo[1] 'ventas.csv', columna de índice 1: falta el campo requerido 'tipo' (Field required)` (**M-09**): el nombre del archivo aparece aunque Pydantic no lo reporte (D-25, hallazgo 3). | HU-06 |
| CA-16 | Un YAML de 2 archivos con `tipo: numero_magico` en la columna de índice 1 de `ventas.csv` lanza `ContractSchemaError` con mensaje exactamente `archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor 'numero_magico' inválido (Input should be 'string', 'integer', 'float', 'date', 'datetime' or 'boolean')` (**M-10**): archivo, columna, valor inválido y los 6 permitidos. | HU-06 |
| CA-17 | Un YAML de 2 archivos donde `ventas.csv` declara dos veces la columna `venta_id` lanza `ContractSchemaError` con mensaje exactamente `archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'` (**M-11**). | HU-06 |
| CA-18 | Un archivo con sintaxis YAML inválida lanza `ContractParseError` (no `ContractSchemaError`); los dos tipos son distinguibles por su tipo de excepción y el mensaje antecede el detalle de PyYAML con `el archivo YAML del contrato es sintácticamente inválido` (**M-12**). | HU-07 |
| CA-19 | Un YAML cuya clave raíz `contract_data:` existe **con valor nulo** (la plantilla vacía real, T-56) lanza `ContractSchemaError` con mensaje exactamente `la clave raíz 'contract_data' debe contener un mapa con la lista 'archivos' (se encontró: None)` (**M-01**); el test verifica además que **no** se propaga `AttributeError`. | HU-08 |
| CA-20 | Un YAML con `contract_data: pendiente_de_completar` (valor **no-mapa**) lanza `ContractSchemaError` con mensaje exactamente `la clave raíz 'contract_data' debe contener un mapa con la lista 'archivos' (se encontró: 'pendiente_de_completar')` (**M-01**), sin `AttributeError` (D-25, hallazgo 1: T-56 es más amplio que el valor nulo). | HU-08 |
| CA-21 | Un YAML que viola **dos** reglas a la vez (dos archivos `ventas.csv` **y** una columna con `tipo` inválido en el segundo) produce **exactamente una** excepción `ContractSchemaError` cuyo mensaje es **uno solo**, sin lista agregada de errores de Pydantic (fail-fast, D-23c). El criterio verifica **cardinalidad y ausencia de agregación**, no la identidad del error ganador: el mensaje puede ser **cualquiera** de los dos posibles (**M-05** o el **M-10** del ítem) y ambos son igualmente conformes. El test **no debe** fijar cuál gana: el orden depende de que los `field_validator` de lista corran tras los de ítem, un detalle interno de Pydantic (D-25, hallazgo 4). | HU-04, HU-05, HU-06 |
| CA-22 | `load_contract("600_template/contract_data.yaml")` (T-58) no lanza excepción y devuelve un `Contract` con `len(archivos) >= 1`, cada archivo con `nombre` no vacío y `columnas` no vacía; el archivo de plantilla en el repo declara `contract_data.archivos` y no `contract_data.columnas`. | HU-09 |
| CA-23 | Al cargar un contrato multi-archivo válido (que **nombra** `clientes.csv` y `ventas.csv`) con la apertura de archivos instrumentada, se observa **exactamente una** apertura y es la del propio `contract_data.yaml`: ninguna ruta bajo `data/bronze/`, ninguna bajo `clients/`, ningún `.csv`. El test **debe** afirmar primero que el espía observó ≥ 1 apertura (guarda de no-vacuidad, **L-17**): una aserción de ausencia sobre un instrumento mudo pasa en vacío y no prueba nada. | HU-10 |
| CA-24 | El modelo `Contract` **no** expone `columnas`: acceder a `Contract(...).columnas` falla (`AttributeError`) y `'columnas' not in Contract.model_fields`; la única vía de acceso a las columnas es `archivos[i].columnas` (D-25d, sin atajo de compatibilidad). | HU-02, HU-11 |
| CA-25 | Tras la migración, la suite completa (`pytest`) se ejecuta **sin fallos** y cada comportamiento cubierto por un test de `config_contract` en la forma vieja tiene un test equivalente bajo `archivos[].columnas`: no queda ningún test que construya o afirme `contract_data.columnas` como forma válida (salvo el fixture de CA-08, que la usa como caso **inválido**). | HU-11 |
| CA-26 | Todos los fixtures usados en los tests (contratos válidos e inválidos, de uno y de varios archivos) son YAMLs **sintéticos** versionables o generados por el propio test, sin PII ni datos reales de cliente, y ninguno reside bajo `clients/*/data/` (C-01). | HU-12 |
| CA-27 | `load_contract` es invocable directamente como función Python (sin argv, subprocess ni fachada CLI) y su firma pública es exactamente `load_contract(path) -> Contract`, sin parámetros añadidos (el `estilo` del spike no existe en producción); no hay comando `zlk contract ...` (core-only, D-23d). | HU-01, HU-02 |
| CA-28 | Un YAML **híbrido** —`contract_data.archivos` válida (lista no vacía, que por sí sola cargaría sin error) **y además** un `columnas` residual en la raíz de `contract_data`— lanza `ContractSchemaError` con mensaje exactamente **M-13**; el contrato se **rechaza** y no se retorna objeto, en vez de ignorar el residual en silencio (D-26). El caso es **disjunto** de CA-08: allí no hay `archivos` utilizable y el mensaje es M-02; aquí sí la hay y el mensaje es M-13. Un test verifica que los dos fixtures producen mensajes **distintos**. | HU-03, HU-11 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` debe estar cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-27 |
| HU-02 | CA-04, CA-05, CA-24, CA-27 |
| HU-03 | CA-06, CA-07, CA-08, CA-09, CA-28 |
| HU-04 | CA-10, CA-11, CA-12, CA-21 |
| HU-05 | CA-13, CA-14, CA-21 |
| HU-06 | CA-03, CA-05, CA-15, CA-16, CA-17, CA-21 |
| HU-07 | CA-18 |
| HU-08 | CA-19, CA-20 |
| HU-09 | CA-22 |
| HU-10 | CA-23 |
| HU-11 | CA-24, CA-25, CA-28 |
| HU-12 | CA-26 |

## No-Objetivos
- **No** empareja el `nombre` declarado con el archivo físico ingerido en bronze, ni decide qué pasa con extras o faltantes — es `load_data` (D-18, etapa posterior).
- **No** resuelve la **colisión de nombres por case-insensitivity del filesystem** (`Ventas.csv` vs `ventas.csv`): riesgo aceptado en D-25b, diferido a `load_data` (**T-59**).
- **No** valida los **datos** de ningún CSV contra el contrato (tipos, nulos, llaves reales) — `load_data`; **no** abre nada bajo `data/bronze/` (frontera D-21).
- **No** interpreta `nombre` como patrón/glob ni con matching difuso: es una cadena declarativa.
- **No** añade una propiedad `Contract.columnas` de compatibilidad (D-25d); los consumidores se migran a `archivos[].columnas`.
- **No** agrega múltiples errores en un solo reporte (fail-fast, D-23c) ni **garantiza orden alguno** de reporte cuando concurren varias violaciones: el contrato es un único error, no cuál de ellos gana (CA-21, D-26).
- **No** carga ni valida `business_rules.yaml`, `finance.yaml` ni el Maestro de Sectores (cada uno su propio tracer bullet, D-21).
- **No** ensambla `ClientConfig`/`ClientContext` ni reconcilia referencias cruzadas entre YAMLs.
- **No** crea/autorea el YAML por entrevista (D-22, T-44); aquí el YAML **ya existe**.
- **No** expone fachada CLI (core-only, D-23d).
- **No** interpreta reglas de negocio, cálculos financieros ni scoring.
