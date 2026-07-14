# Definition — config_contract

> Artefacto del paso 3 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `config_contract` (snake_case)
- **Módulo / componente:** capa de **configuración** del motor (eje `load_config`, §5 de `system_design.md`) —
  primer eslabón del lector/validador de configuración (D-21/D-22). Lee y valida el **YAML 1 de 4**
  (`input/contract_data.yaml`) del tenant: el Contrato de Datos que declara la estructura esperada de un archivo
  del cliente (columnas, tipos, nulabilidad, llaves). No toca `business_rules.yaml`, `finance.yaml`, el Maestro
  de Sectores ni el ensamblado final de `ClientConfig`/`ClientContext` — cada uno es su propio tracer bullet
  posterior.

## Problema / Necesidad
Hoy un tenant (`client_scaffold`) nace con un placeholder de `contract_data.yaml`, y con `ingest` los archivos
crudos del cliente ya llegan a bronze — pero no existe ninguna forma de saber, de manera confiable y programática,
si el **contrato de datos que describe la estructura esperada de un archivo** está **bien formado en sí mismo**.
Sin esta pieza, cualquier etapa posterior (`load_data`, que comparará el CSV real contra el contrato) carecería
de una base fiable: validaría datos del cliente contra un contrato que podría estar roto, mal tipado o
incompleto, produciendo errores confusos o comportamiento indefinido. `config_contract` resuelve esa carencia:
da la primera garantía dura del eje de configuración — "el contrato que voy a usar para validar datos es, él
mismo, válido" — antes de que nadie intente usarlo.

## Alcance
**In scope:**
- Core (p. ej. `load_contract(path) -> Contract`) que **lee** (parsea) el YAML de `contract_data.yaml` y lo
  **valida** con un modelo Pydantic.
- Modelo(s) Pydantic que representan el contrato: contrato → lista de columnas; columna → `nombre`, `tipo`
  (dentro de un conjunto soportado fijado en la spec), `nulabilidad`, `llave`.
- Validación estructural del contrato **contra su propio esquema**: campos requeridos presentes, tipos de campo
  correctos, `tipo` de columna dentro del enum soportado, sin columnas duplicadas por nombre, lista de columnas
  no vacía.
- Distinción entre error de **parseo** (YAML sintácticamente roto) y error de **validación de esquema**
  (contrato bien formado como YAML pero mal formado como contrato), ambos claros y accionables.
- Objeto de contrato tipado devuelto en memoria, listo para ser consumido por una etapa posterior (`load_data`).
- Desarrollo y pruebas exclusivamente contra **YAMLs sintéticos de ejemplo** (válidos e inválidos) como fixtures
  (C-01).

**Out of scope:**
- Comparar el contrato contra un **CSV real** de bronze o validar que los datos del cliente lo cumplen — es
  `load_data` (etapa posterior); frontera explícita del contrato (D-21).
- Emparejar el archivo físico ingerido con su tipo de contrato — punto abierto **D-18**, no se resuelve aquí.
- Cargar/validar `business_rules.yaml`, `finance.yaml` o el Maestro de Sectores — cada uno su propio tracer
  bullet por-YAML (D-21).
- Ensamblar el objeto único de config (`ClientConfig`/`ClientContext`) o reconciliar referencias cruzadas entre
  YAMLs — paso final de integración pendiente, posterior a esta tanda de features.
- Crear/autorear el YAML por entrevista con stakeholders (entrevistador/autor, D-22, T-44); aquí el YAML **ya
  existe**.
- Interpretar o ejecutar reglas de negocio, cálculos financieros o scoring.
- Exponer o decidir sobre una fachada CLI dedicada — se decide en la spec; esta feature puede ser core-only.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como desarrollador del motor, quiero cargar un `contract_data.yaml` bien formado y obtener un objeto de contrato tipado en memoria, para que etapas posteriores (p. ej. `load_data`) puedan consumirlo sin volver a parsear ni reinterpretar el YAML. | Dado un YAML válido, el core devuelve un objeto tipado cuya lista de columnas refleja fielmente lo declarado: nombre, tipo, nulabilidad y llave por cada columna. |
| HU-02 | Como desarrollador del motor, quiero que un contrato con un campo requerido faltante en alguna columna (p. ej. sin `tipo`) sea rechazado con un error claro, para detectar contratos incompletos antes de que lleguen a validar datos reales. | Un YAML con al menos un campo requerido faltante en una columna produce un error de validación claro (qué campo falta y en qué columna) y no devuelve objeto de contrato. |
| HU-03 | Como desarrollador del motor, quiero que un contrato con un tipo de columna fuera del conjunto soportado sea rechazado con un error claro, para evitar contratos que declaren tipos que el sistema no sabe interpretar. | Un YAML con `tipo` de columna fuera del enum soportado (p. ej. un valor inventado) produce un error de validación claro que identifica el valor inválido y la columna afectada. |
| HU-04 | Como desarrollador del motor, quiero que un YAML sintácticamente roto produzca un error de parseo distinguible de un error de validación de esquema, para poder diagnosticar rápido si el problema es de sintaxis YAML o de contenido del contrato. | Un archivo con sintaxis YAML inválida produce un error identificable como error de parseo, con mensaje claro, y ese error es distinguible (por tipo o mensaje) de un error de validación de esquema Pydantic. |
| HU-05 | Como desarrollador del motor, quiero que un contrato con columnas duplicadas por nombre o con lista de columnas vacía sea rechazado con un error claro, para evitar contratos ambiguos o inútiles que no describen ningún archivo real. | Un YAML con dos o más columnas de igual nombre, o con lista de columnas vacía, produce un error de validación claro y no devuelve objeto de contrato. |
| HU-06 | Como responsable de la arquitectura del pipeline, quiero que la validación del contrato se limite estrictamente a su propio esquema, sin leer ni requerir ningún CSV de bronze, para mantener nítida la frontera con `load_data` y no acoplar esta feature a la existencia de datos reales del cliente. | Al invocar el core con un `contract_data.yaml` (válido o inválido), la operación no abre, lee ni referencia ningún archivo bajo `data/bronze/` del tenant; el resultado (objeto u error) depende únicamente del contenido del YAML. |
| HU-07 | Como desarrollador del motor, quiero que la lógica de lectura/validación viva en una función core reutilizable, para poder invocarla desde tests, desde `load_data` (etapa posterior) o desde una futura fachada CLI, sin duplicar lógica. | Existe una función core (p. ej. `load_contract(path) -> Contract`) invocable directamente sin pasar por ninguna CLI; si en la spec se decide exponer una fachada CLI, esta se limita a invocar el core y traducir su resultado/errores. |
| HU-08 | Como responsable de cumplimiento del producto, quiero que el desarrollo y las pruebas de esta feature usen exclusivamente YAMLs sintéticos de ejemplo, para que la Bóveda de Datos (C-01) se respete por diseño y ningún dato real de cliente sea necesario para validar el contrato. | Todos los fixtures usados en pruebas (contratos válidos e inválidos) son YAMLs sintéticos versionables, sin PII ni datos reales de ningún cliente. |

## Dependencias
- Feature `client_scaffold` (T-21, ya en `main`): genera el tenant con `input/contract_data.yaml` (hoy
  placeholder); esta feature asume que el archivo existe con contenido a validar.
- `700_architecture/system_design.md` §5 (los 4 YAMLs; YAML 1 = Contrato de Datos: columnas, tipos, nulos,
  llaves) y §7 (`input/` versionable, no PII).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda): desarrollo exclusivo con datos sintéticos.
- `900_persistence/decisions.md` D-21 (descomposición de `load_config` por-YAML; frontera de `config_contract`),
  D-22 (lector/validador ahora vs autor/entrevistador futuro) y D-18 (emparejamiento archivo→contrato, abierto,
  fuera de alcance de esta feature).
- Librería **Pydantic** (motor de validación) y un parser YAML (p. ej. `PyYAML`).

## Riesgos y Supuestos
- **Supuesto:** el conjunto exacto de tipos soportados (`string`/`integer`/`float`/`date`/`boolean`, según
  ejemplo del contrato) se fija en detalle en `spec_writer` (paso siguiente); el contrato solo exige que exista
  un enum cerrado y validado. HU-03 se define bajo ese supuesto general, sin comprometerse a la lista final.
- **Supuesto:** "columnas duplicadas por nombre" se interpreta como comparación exacta de la cadena `nombre`
  (sin normalización de mayúsculas/espacios); si se requiere normalización, se decide en la spec.
- **Vacío heredado del contrato (D-18, abierto):** el emparejamiento de un archivo físico de bronze con su tipo
  de contrato queda explícitamente fuera de esta definición; ninguna historia lo cubre, para no exceder la
  frontera fijada en `feature_contract.md`.
- **Punto a decidir en spec, no aquí:** si esta feature expone o no una fachada CLI (`zlk contract validate ...`
  o similar) queda abierto; el contrato permite que sea core-only en esta etapa. HU-07 se redacta de forma
  neutral para no forzar esa decisión.
- **Dato sintético:** todo fixture usado en spec/notebook posteriores debe ser un `contract_data.yaml` sintético
  (válido o deliberadamente inválido), nunca un contrato real de cliente, en línea con C-01.
- No se detectaron contradicciones entre `feature_contract.md` y `system_design.md` §5: ambos coinciden en que
  el Contrato de Datos valida columnas/tipos/nulos/llaves de un archivo y se distingue de las Reglas de Negocio
  y las Variables Financieras.
