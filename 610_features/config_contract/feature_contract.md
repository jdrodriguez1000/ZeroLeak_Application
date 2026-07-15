# Feature Contract — config_contract

> Artefacto **a nivel feature**, creado por la **sesión principal** (humano + Claude Code) en el paso 2 del flujo.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de escribir la definición**.
> **Una feature = una construcción completa** (Opción A, sin bandas): un solo ciclo SDD+TDD la lleva a "terminado".

## Estrella Polar
Leer el **Contrato de Datos** de un tenant (`input/contract_data.yaml`, YAML 1 de los 4, §5) y validar con
**Pydantic** que esté **bien formado en sí mismo** — es decir, que declare correctamente la estructura esperada
de un archivo de datos: su lista de columnas, cada una con nombre, tipo, nulabilidad y marca de llave. El
resultado es un **objeto de contrato validado en memoria** (o un **error de validación claro** que detiene el
análisis), listo para que una etapa posterior lo use. Es el primer eslabón del lector/validador de configuración
(D-22): asume que el YAML **ya existe** y solo se ocupa de **cargarlo y validarlo**, nunca de crearlo.

## Definición de "Terminado"
Condiciones que deben cumplirse para considerar la feature **terminada** (comportamiento end-to-end completo):
- Existe una función core (motor como API) que, dado el `contract_data.yaml` de un tenant, **lo lee y lo valida**
  con un modelo Pydantic, devolviendo un **objeto de contrato tipado** cuando es válido.
- El contrato válido describe la estructura de **un tipo de archivo de datos**: una **lista de columnas**, donde
  cada columna declara al menos:
  - **nombre** (identificador de la columna),
  - **tipo** (dato esperado; el conjunto de tipos soportados se fija en la spec — p. ej. `string`/`integer`/
    `float`/`date`/`boolean`),
  - **nulabilidad** (si admite nulos),
  - **llave** (si forma parte de la clave del archivo).
- **Validación estructural del contrato en sí mismo** (bien formado): campos requeridos presentes, tipos de los
  campos correctos, valores de enumeración válidos (p. ej. `tipo` dentro del conjunto soportado), sin columnas
  duplicadas por nombre, lista de columnas no vacía. Los detalles exactos y casos límite se fijan en la spec.
- Ante un contrato **mal formado** (campo faltante, tipo inválido, YAML sintácticamente roto, enum desconocido,
  columnas duplicadas…) la operación produce un **error de validación claro y accionable** (qué está mal y dónde),
  y **no** entrega un objeto a medio construir.
- **Frontera nítida (lo que define el alcance):** valida el contrato **contra su propio esquema**; **NO** lo
  compara contra ningún **CSV real** de bronze ni contra datos del cliente. "¿El archivo de bronze cumple este
  contrato?" es responsabilidad de **`load_data`** (etapa posterior), **no** de `config_contract`.
- **Motor como API:** la operación vive en una función core (p. ej. `load_contract(path) -> Contract` o similar);
  si esta feature expone o no una fachada CLI se decide en la definición/spec (puede ser core-only en esta etapa).
- **Seguro por diseño (C-01):** se desarrolla y prueba **exclusivamente contra YAMLs sintéticos de ejemplo**. El
  contrato describe **estructura**, no PII; `input/` es material versionable (§7), no datos reales del cliente.

## Alcance
**In scope:**
- Core que **lee** `contract_data.yaml` (parseo YAML) y lo **valida** con un modelo Pydantic.
- Modelo(s) Pydantic que representan el contrato: contrato → lista de columnas; columna → (nombre, tipo,
  nulabilidad, llave).
- **Validación del contrato en sí mismo**: campos requeridos, tipos correctos, enums válidos, sin columnas
  duplicadas, lista no vacía (detalle fino en la spec).
- **Errores de validación claros y accionables** ante un contrato mal formado o un YAML sintácticamente roto.
- Objeto de contrato tipado devuelto en memoria para consumo de etapas posteriores.
- Desarrollo contra **YAMLs sintéticos de ejemplo** (válidos e inválidos) como fixtures.

**Out of scope (nunca, o en otra feature):**
- **Comparar** el contrato contra un **CSV real** de bronze / validar que los datos cumplen el contrato — eso es
  `load_data` (etapa posterior). Ésta es la frontera que mantiene delgado al tracer bullet (D-21).
- **Emparejar** el archivo físico ingerido con su tipo de contrato — **D-18, punto abierto**; se revisitará al
  construir esta tanda de features, no aquí.
- **Cargar/validar los otros YAMLs** (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores): cada uno es su
  propio tracer bullet por-YAML (D-21).
- **Ensamblar** el objeto único de config (`ClientConfig`/`ClientContext`) ni **reconciliar referencias cruzadas**
  entre YAMLs (`sector_id`, reglas→columnas): es el **paso final de integración** pendiente de D-21, posterior.
- **Crear/autorear** el YAML por entrevista con stakeholders — es el **entrevistador/autor**, trabajo futuro
  (D-22, T-44). Aquí se asume que el YAML **ya existe**.
- Interpretar o ejecutar reglas de negocio, cálculos financieros o scoring.

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **verificables y detallados** viven en `spec.md` como `CA-xx`.
1. Dado un `contract_data.yaml` **bien formado**, la operación devuelve un **objeto de contrato tipado** cuya
   lista de columnas refleja fielmente lo declarado (nombre, tipo, nulabilidad, llave por columna).
2. Un contrato con un **campo requerido faltante** (p. ej. una columna sin `tipo`) produce un **error de
   validación claro** y **no** devuelve objeto.
3. Un contrato con un **tipo/enum inválido** (p. ej. `tipo: "numero_magico"` fuera del conjunto soportado)
   produce un **error de validación claro**.
4. Un YAML **sintácticamente roto** produce un error claro (parseo), distinguible de un error de validación de
   esquema.
5. Un contrato con **columnas duplicadas por nombre** o con **lista de columnas vacía** es rechazado con error
   claro (según se fije en la spec).
6. La operación valida el contrato **contra su propio esquema únicamente**: **no** lee, abre ni requiere ningún
   CSV de bronze ni dato real del cliente (frontera con `load_data`).

## Dependencias
- Feature `client_scaffold` (T-21, ya en `main`): genera el tenant con `input/contract_data.yaml` (hoy un
  placeholder a completar); esta feature consume ese archivo una vez tiene contenido.
- `700_architecture/system_design.md` §5 (los 4 YAMLs; YAML 1 = Contrato de Datos, valida columnas/tipos/nulos/
  llaves por archivo) y §7 (`input/` versionable, no PII).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda): se desarrolla solo con datos sintéticos.
- `900_persistence/decisions.md` D-21 (descomposición de `load_config` por-YAML; frontera de `config_contract`),
  D-22 (lector/validador ahora vs autor/entrevistador futuro) y D-18 (emparejamiento archivo→contrato, abierto).
- Librería **Pydantic** (motor de validación) y un parser YAML (p. ej. `PyYAML`).

## Relación con Hitos de Producto
- **Tercer Tracer Bullet** del proyecto (T-43) y **primer eslabón** del lector/validador de configuración: sin un
  contrato validado no hay forma de saber si los datos de un cliente están bien formados.
- Habilita directamente a **`load_data`** (validar el CSV de bronze contra el contrato) y, más adelante, a la
  ejecución de reglas de negocio y al scoring; es la puerta de entrada del eje **configuración** del pipeline.
