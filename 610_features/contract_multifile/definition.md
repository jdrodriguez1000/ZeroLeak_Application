# Definition — contract_multifile

> Artefacto del paso 3 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `contract_multifile` (snake_case)
- **Módulo / componente:** capa de **configuración** del motor (eje `load_config`, §5 de `system_design.md`) —
  **segundo eslabón** del lector/validador de configuración (D-21/D-22). Evoluciona el mismo YAML 1 de 4
  (`input/contract_data.yaml`) que ya lee y valida `config_contract` (T-43), pasando de describir la estructura
  de **un** archivo del cliente a la de **uno o varios** archivos declarados bajo `archivos[]`. No toca
  `business_rules.yaml`, `finance.yaml`, el Maestro de Sectores ni el ensamblado final de `ClientConfig`/
  `ClientContext` — cada uno es su propio tracer bullet posterior (D-21).

## Problema / Necesidad
`config_contract` (T-43) resolvió la primera garantía dura del eje de configuración —"el contrato que voy a usar
para validar datos es, él mismo, válido"— pero solo para un cliente que entrega **un único archivo** de datos.
Ese no es el caso real del nicho MVP: un cliente de Retail Moderno típicamente entrega **varios** archivos (p.
ej. `clientes.csv` + `ventas.csv`), cada uno con su propia estructura esperada. Con la forma actual de
`Contract` (`columnas: list[Columna]`), el contrato **no puede representar** esa realidad: fuerza a describir
solo un archivo o a mezclar columnas de distintos archivos en una sola lista ambigua. Sin esta pieza,
`load_data` (etapa posterior) no tendría cómo saber qué columnas corresponden a qué archivo físico del
cliente. Adicionalmente, dos defectos concretos bloquean el uso real del contrato hoy: (T-56) un
`contract_data:` presente pero con valor nulo revienta con un `AttributeError` en vez de un error de esquema
claro, y (T-58) la plantilla vigente (`600_template/contract_data.yaml`) sigue en el esquema viejo de un solo
archivo. `contract_multifile` resuelve las tres carencias a la vez porque comparten la misma línea de código
que se reescribe (`contract.py:115`), evitando trabajo desechado.

## Alcance
**In scope:**
- Modelo `ArchivoContrato` (`nombre` + `columnas`) y cambio de `Contract`: de `columnas: list[Columna]` a
  `archivos: list[ArchivoContrato]`.
- Reutilización **sin reescritura** del núcleo ya verificado en `config_contract`: modelo `Columna`, enum
  cerrado `TipoDato` de 6 tipos, validador de columnas duplicadas por cadena exacta, fail-fast de un solo error,
  y las excepciones `ContractParseError` / `ContractSchemaError`.
- Validación de **nivel archivo**: `archivos` no vacía (ni ausente), cada archivo con `nombre` presente y
  `columnas` no vacías, sin `nombre` de archivo duplicado.
- Validación de **nivel columna**, igual a la vigente hoy, aplicada **dentro de cada archivo**.
- **Localización del error por archivo** en los mensajes de `ContractSchemaError` (no basta el índice de
  columna cuando hay más de un archivo).
- **T-56 (bug):** `contract_data:` presente con valor nulo produce `ContractSchemaError` claro, nunca
  `AttributeError`.
- **T-58 (plantilla):** `600_template/contract_data.yaml` actualizado al esquema multi-archivo y cargable sin
  error con el motor nuevo.
- **Migración** de los tests existentes de `config_contract` que asumen la forma vieja (`contract_data.columnas`)
  a la forma nueva, sin perder cobertura de comportamiento.
- Fixtures sintéticos (YAMLs válidos e inválidos) con un archivo y con varios archivos.

**Out of scope:**
- **Emparejar** el `nombre` declarado en el contrato con el archivo físico realmente ingerido en bronze, y
  decidir qué pasa con archivos extra o faltantes — es `load_data` (etapa posterior); D-18 documenta el
  comportamiento esperado, pero no se construye aquí.
- **Validar los datos** de un CSV contra el contrato (tipos reales, nulos reales, llaves reales) — `load_data`.
- Interpretar `nombre` como patrón/glob o cualquier forma de matching difuso: aquí `nombre` es una **cadena
  declarativa**, no un mecanismo de búsqueda.
- **Cargar/validar** los otros YAMLs (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores) — cada uno su
  propio tracer bullet por-YAML (D-21).
- **Ensamblar** el objeto único de config (`ClientConfig`/`ClientContext`) ni reconciliar referencias cruzadas
  entre YAMLs — paso final de integración, posterior.
- **Crear/autorear** el YAML por entrevista con stakeholders — trabajo futuro (D-22, T-44); aquí el YAML **ya
  existe**.
- Exponer una fachada CLI para el contrato (se mantiene core-only, D-23d).
- Interpretar o ejecutar reglas de negocio, cálculos financieros o scoring.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como desarrollador del motor, quiero cargar un `contract_data.yaml` bien formado que describe **varios archivos** y obtener un `Contract` cuya lista `archivos` refleje fielmente lo declarado, para que etapas posteriores (p. ej. `load_data`) sepan qué columnas corresponden a cada archivo físico del cliente. | Dado un YAML válido con dos o más archivos, `load_contract` devuelve un `Contract.archivos` con, para cada elemento, su `nombre` y su lista de columnas (nombre, tipo, nulable, llave) en el orden declarado. |
| HU-02 | Como desarrollador del motor, quiero que un contrato con **un solo archivo** siga funcionando igual que antes, para que el caso de un archivo sea el caso general (`len(archivos) == 1`) y no una rama especial que duplique lógica. | Dado un YAML válido con un único archivo, `load_contract` devuelve un `Contract` con `archivos` de longitud 1, cuyo contenido es equivalente al `Contract.columnas` que producía la forma anterior de `config_contract`. |
| HU-03 | Como desarrollador del motor, quiero que un contrato con la lista `archivos` **vacía o ausente** sea rechazado con un `ContractSchemaError` claro, para evitar contratos que no describen ningún archivo real. | Un YAML sin la clave `archivos`, o con `archivos: []`, produce un `ContractSchemaError` y no devuelve objeto de contrato. |
| HU-04 | Como desarrollador del motor, quiero que un archivo **sin `nombre`** o con **`columnas` vacías/ausentes** sea rechazado con un error que **identifique de qué archivo se trata**, para poder corregir el contrato sin adivinar cuál de los archivos declarados está incompleto. | Un YAML donde algún elemento de `archivos` carece de `nombre`, o tiene `columnas` vacía o ausente, produce un `ContractSchemaError` cuyo mensaje identifica el archivo afectado (por posición o por `nombre`, cuando esté disponible). |
| HU-05 | Como desarrollador del motor, quiero que dos archivos con el **mismo `nombre`** sean rechazados con un error claro, para evitar contratos ambiguos donde no se sepa a cuál de los dos archivos duplicados corresponde una columna. | Un YAML con dos o más elementos de `archivos` que comparten el mismo `nombre` (cadena exacta) produce un `ContractSchemaError` que menciona el `nombre` duplicado, y no devuelve objeto de contrato. |
| HU-06 | Como desarrollador del motor, quiero que todas las validaciones de columna vigentes (campo requerido faltante, `tipo` fuera del enum de 6, columnas duplicadas por cadena exacta) sigan aplicando **dentro de cada archivo**, con el mensaje **localizando también el archivo**, para poder diagnosticar un contrato multi-archivo roto sin ambigüedad sobre en cuál archivo está el defecto. | Dado un YAML con varios archivos donde una columna de alguno de ellos viola una regla vigente (campo faltante, tipo inválido, o nombre de columna duplicado dentro del mismo archivo), el `ContractSchemaError` resultante identifica tanto el archivo como la columna/campo afectados. |
| HU-07 | Como desarrollador del motor, quiero que un YAML **sintácticamente roto** siga produciendo `ContractParseError`, distinguible de un error de esquema, para poder diagnosticar rápido si el problema es de sintaxis YAML o de contenido del contrato, sin que el cambio a multi-archivo afecte esa distinción. | Un archivo con sintaxis YAML inválida produce un `ContractParseError` con mensaje claro, distinguible (por tipo) de cualquier `ContractSchemaError`. |
| HU-08 | Como desarrollador del motor, quiero que un YAML con `contract_data:` **presente pero con valor nulo** produzca un `ContractSchemaError` claro (bug T-56), para que un contrato vacío o mal generado falle de forma diagnosticable en vez de con un `AttributeError` interno que expone un detalle de implementación. | Dado un `contract_data.yaml` cuya clave raíz `contract_data` existe pero tiene valor `null` (o vacío), `load_contract` produce un `ContractSchemaError` con mensaje claro, y en ningún caso propaga un `AttributeError` u otra excepción no controlada. |
| HU-09 | Como desarrollador que scaffoldea un tenant nuevo, quiero que `600_template/contract_data.yaml` (T-58) esté en el esquema multi-archivo y cargue sin error con el motor nuevo, para que un tenant recién creado con `client_scaffold` tenga desde el día uno una plantilla de contrato consistente con la forma real que el motor espera. | `load_contract("600_template/contract_data.yaml")` no lanza ninguna excepción y devuelve un `Contract` con al menos un elemento en `archivos`, cada uno con `nombre` y columnas válidas según el esquema vigente. |
| HU-10 | Como responsable de la arquitectura del pipeline, quiero que la validación del contrato multi-archivo se limite estrictamente a su propio esquema, sin leer ni requerir ningún CSV de bronze, para mantener nítida la frontera con `load_data` también en la forma nueva de varios archivos. | Al invocar `load_contract` con un `contract_data.yaml` (de uno o varios archivos, válido o inválido), la operación no abre, lee ni referencia ningún archivo bajo `data/bronze/` del tenant; el resultado depende únicamente del contenido del YAML. |
| HU-11 | Como desarrollador del motor, quiero que los tests existentes de `config_contract` que asumen la forma vieja (`contract_data.columnas`) se migren a la forma nueva sin perder cobertura, para que la suite completa quede en verde y ningún comportamiento ya verificado se pierda al introducir el nivel de archivo. | Tras la migración, la suite completa se ejecuta sin fallos; cada comportamiento cubierto anteriormente por un test de `config_contract` sigue teniendo un test equivalente que lo cubre bajo la forma `archivos[].columnas`. |
| HU-12 | Como responsable de cumplimiento del producto, quiero que el desarrollo y las pruebas de esta feature usen exclusivamente YAMLs sintéticos de ejemplo (de uno y de varios archivos), para que la Bóveda de Datos (C-01) se respete por diseño también en la forma multi-archivo. | Todos los fixtures usados en pruebas (contratos válidos e inválidos, de uno y de varios archivos) son YAMLs sintéticos versionables, sin PII ni datos reales de ningún cliente. |

## Dependencias
- Feature **`config_contract` (T-43, ya en `main` vía PR #3)**: es el **cimiento** de esta feature. Aporta
  `load_contract`, `Contract`, `Columna`, `TipoDato`, los validadores y las excepciones
  `ContractParseError`/`ContractSchemaError` que aquí se envuelven y extienden sin reescribir.
- Feature `client_scaffold` (T-21, ya en `main`): genera el tenant con `input/contract_data.yaml`.
- `900_persistence/decisions.md` **D-18 (🔒 resuelta, 2026-07-15)**: fija la forma exacta
  `contract_data.archivos[].{nombre, columnas}`. También D-21 (descomposición por-YAML), D-22 (cargar vs crear)
  y D-23 (enum de 6 tipos, fail-fast, core-only, duplicados por cadena exacta).
- `900_persistence/tasks.md`: **T-57** (esta feature), **T-56** (bug del `contract_data:` nulo, absorbido aquí)
  y **T-58** (actualizar la plantilla, absorbido aquí).
- `700_architecture/system_design.md` §5 (los 4 YAMLs; YAML 1 = Contrato de Datos) y §7 (`input/` versionable,
  no PII).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda): se desarrolla solo con datos sintéticos.
- Librería **Pydantic** (motor de validación) y **PyYAML** (parser).
- Archivo `app/src/zeroleak/config/contract.py` (código vigente que esta feature evoluciona).

## Riesgos y Supuestos
- **Supuesto:** la forma exacta de cómo el mensaje de error "identifica el archivo" (por posición/índice,
  por `nombre` cuando existe, o ambos) se fija en el detalle de `spec_writer` (paso siguiente); el contrato
  solo exige que la ambigüedad de hoy (solo índice de columna) se resuelva. HU-04 y HU-06 se redactan de forma
  neutral sobre el mecanismo exacto.
- **Supuesto:** "archivo duplicado por `nombre`" se interpreta, igual que en `config_contract` para columnas,
  como comparación exacta de cadena (sin normalizar mayúsculas/espacios), consistente con D-23e; si se requiere
  normalización, se decide en la spec.
- **Vacío heredado del contrato (D-18, parcialmente abierto):** el emparejamiento de un `nombre` de archivo
  declarado con el archivo físico realmente ingerido en bronze queda explícitamente fuera de esta definición;
  ninguna historia lo cubre, para no exceder la frontera fijada en `feature_contract.md`.
- **Punto a decidir en spec, no aquí:** el orden y la representación exacta de campos en el mensaje de
  `ContractSchemaError` para archivo+columna (p. ej. si se usa `archivo[N]` o `archivo 'nombre'`) queda abierto;
  la definición solo exige que el archivo sea identificable.
- **T-56 y contrato:** el `feature_contract.md` entra en detalle suficiente sobre este bug (clave presente pero
  valor nulo → `ContractSchemaError`, nunca `AttributeError`) como para cubrirlo con HU-08 sin ambigüedad; no se
  detectó contradicción ni vacío en esta parte del contrato.
- **Dato sintético:** todo fixture usado en spec/notebook posteriores debe ser un `contract_data.yaml` sintético
  (de uno o varios archivos, válido o deliberadamente inválido), nunca un contrato real de cliente, en línea
  con C-01.
- No se detectaron contradicciones entre `feature_contract.md` y `900_persistence/decisions.md` (D-18, D-21,
  D-22, D-23): la forma `archivos[].{nombre, columnas}`, la reutilización del núcleo de `config_contract` y el
  carácter core-only son consistentes entre ambos artefactos.
