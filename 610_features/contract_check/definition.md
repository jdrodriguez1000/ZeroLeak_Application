# Definition — contract_check

> Artefacto del paso 3 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `contract_check` (snake_case)
- **Módulo / componente:** fachada **CLI** (`app/src/zeroleak/cli.py`), tercer subcomando de `zlk` junto a
  `client new` e `ingest`. Expone, sin modificarlo, el motor de la capa de **configuración**
  (`config/contract.py`, eje `load_config`, §5 de `system_design.md`) construido por `config_contract` y
  `contract_multifile`. No es motor nuevo: es el **puente** entre el humano que edita
  `input/contract_data.yaml` a mano y el validador que ya existe pero que hoy nadie invoca.

## Problema / Necesidad
El motor que valida el Contrato de Datos (`load_contract`) existe, está verificado y habla trece mensajes de
error cuidadosamente congelados (M-01…M-13), pero **nadie lo invoca** en el flujo real: el CLI de `zlk` solo
tiene `client new` (crea el tenant) e `ingest` (archiva bytes crudos sin parsear contenido, D-21). El humano
que edita `contract_data.yaml` a mano no tiene forma de preguntarle al motor, cuando quiera, si su YAML quedó
bien — debe esperar a una etapa futura (`load_data`, aún no construida) para descubrir un error, o adivinar.
`contract_check` cierra ese lazo de retroalimentación: agrega un subcomando que valida el contrato bajo
demanda y muestra la respuesta exacta del motor (éxito o el mensaje de error correspondiente), sin construir
ni un gramo de lógica de validación nueva.

## Alcance
**In scope:**
- Subcomando `zlk contract check <CLIENTE>` en `cli.py`, con su entrada en `_USAGE`.
- Resolución de la ruta del contrato del tenant por la misma convención vigente de `client new` e `ingest`
  (`<clients_root>/<CLIENTE>/input/contract_data.yaml`, con `_clients_root()`/`ZEROLEAK_CLIENTS_ROOT`).
- Traducción a mensaje de dominio + exit code de las precondiciones de existencia que el motor **no** cubre
  hoy (tenant inexistente, o tenant sin `input/contract_data.yaml`), verificadas **antes** de invocar
  `load_contract`, siguiendo el patrón ya usado por `ingest` con `TenantNotFoundError`.
- Invocación de `load_contract` sobre el YAML resuelto y traducción de su resultado a la salida del comando:
  éxito por stdout con exit 0; error por stderr con el mensaje del motor **verbatim** y exit ≠ 0.
- Distinción observable entre `ContractParseError` (YAML sintácticamente roto) y `ContractSchemaError`
  (YAML válido pero que no cumple el esquema).
- Cobertura explícita del contrato recién scaffoldeado por `client new` (raíz `contract_data:` presente y
  sin cuerpo → M-01) como camino de primera clase, no como borde.
- Tests unitarios de la fachada (invocando `main(argv)`, al estilo de `test_cli_client_new.py` /
  `test_cli_ingest.py`) y una prueba de integración end-to-end con tenant sintético
  (`client new` → editar YAML → `contract check`).

**Out of scope:**
- Modificar el motor (`config/contract.py`): firma de `load_contract`, modelos, excepciones o **una sola
  letra** de los mensajes M-01…M-13.
- Escribir, corregir, autocompletar o crear `contract_data.yaml` — el comando diagnostica, no repara (D-22;
  el entrevistador/autor es T-44, futuro).
- Emparejar el contrato declarado con los archivos realmente ingeridos en bronze, o leer/validar cualquier
  CSV — frontera D-21, corresponde a `load_data`.
- Validar los otros YAMLs (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores) — cada uno su propio
  tracer bullet por-YAML (D-21); este subcomando es `contract check`, no `config check`.
- Doblar la validación dentro de `zlk ingest` (opción descartada de T-68); `ingest` sigue siendo archivador
  notarial que no parsea contenido.
- Agregación multi-error o listado de todos los defectos de una vez: el motor es fail-fast (D-23c) y esta
  feature no lo cambia.
- Modo interactivo, `--fix`, `--watch`, salida JSON, o cualquier bandera más allá de lo mínimo necesario.
- Validar la plantilla `600_template/contract_data.yaml` (ya cubierto por `contract_multifile`).

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como humano que edita `input/contract_data.yaml` a mano, quiero ejecutar `zlk contract check <CLIENTE>` sobre un contrato **válido** y recibir una señal de éxito clara, para saber que el motor leyó *mi* contrato y lo aceptó, sin esperar a una etapa posterior del pipeline. | Sobre un tenant cuyo `contract_data.yaml` es válido (de uno o varios archivos), el comando termina con exit code 0 e imprime por stdout una confirmación que identifica al tenant/contrato validado. |
| HU-02 | Como humano que edita el contrato, quiero que un contrato **inválido por esquema** me muestre el mensaje exacto que el motor ya sabe producir, para corregir el YAML con la misma información precisa que tendría un desarrollador que llama al motor directamente. | Sobre un tenant cuyo `contract_data.yaml` viola el esquema, el comando termina con exit ≠ 0 e imprime por stderr el mensaje de `ContractSchemaError` **exactamente como lo emite el motor**, sin reescritura, adorno ni traducción. |
| HU-03 | Como humano que edita el contrato, quiero que un YAML **sintácticamente roto** me lo indique de forma distinguible de un error de esquema, para saber de inmediato si el problema es de sintaxis YAML o de contenido del contrato. | Sobre un `contract_data.yaml` con sintaxis YAML inválida, el comando termina con exit ≠ 0 e imprime el mensaje de `ContractParseError`, distinguible (por exit code y/o prefijo) del caso de `ContractSchemaError`. |
| HU-04 | Como humano que acaba de crear un tenant con `zlk client new`, quiero que revisar su contrato recién scaffoldeado (sin cuerpo) me dé una señal útil ("tu contrato está vacío, complétalo") en vez de un error genérico, para entender de inmediato qué falta sin tener que interpretar un traceback. | Sobre un tenant recién creado por `client new` (contrato con raíz `contract_data:` presente y sin cuerpo), el comando reporta el mensaje M-01 y exit ≠ 0. |
| HU-05 | Como humano que ejecuta el comando sobre un tenant **inexistente** o sin `input/contract_data.yaml`, quiero recibir un mensaje de dominio claro en vez de un traceback crudo de infraestructura, para entender que el problema es de precondición (tenant/archivo ausente) y no un fallo del motor. | Sobre un tenant inexistente, o uno existente sin `input/contract_data.yaml`, el comando termina con un mensaje de dominio claro y su exit code propio, sin `FileNotFoundError` ni traceback sin traducir. |
| HU-06 | Como humano que ejecuta el comando desde distintos entornos (local, CI, otro `clients_root`), quiero que la ubicación del contrato respete la misma convención de `ZEROLEAK_CLIENTS_ROOT`/`./clients` que ya usan `client new` e `ingest`, para no tener que aprender una convención nueva por subcomando. | La resolución de la ruta del contrato usa `ZEROLEAK_CLIENTS_ROOT` cuando está definida, y cae a `./clients` en caso contrario, de forma idéntica a los subcomandos vigentes. |
| HU-07 | Como humano que escribe mal el comando (`zlk contract`, `zlk contract check` sin cliente, `zlk contract foo`), quiero ver el uso correcto del comando en vez de que la herramienta reviente, para corregir la invocación sin tener que leer código. | Cualquier invocación mal formada del subcomando imprime el texto de uso (`_USAGE`, que incluye la línea del subcomando nuevo) por stderr y termina sin excepción no controlada. |
| HU-08 | Como responsable de la integridad del pipeline, quiero que `contract check` sea puramente de **lectura**: que nunca escriba, corrija ni toque el YAML, `data/` o `manifest.json`, para poder ejecutarlo cuantas veces se quiera sin riesgo de alterar el estado del tenant. | Tras cualquier invocación del comando (contrato válido o inválido), ningún archivo bajo el tenant cambia de contenido ni de timestamp relevante; el comando no crea, corrige ni borra ningún archivo. |
| HU-09 | Como responsable de la frontera de dominio del pipeline (D-21), quiero que `contract check` valide únicamente la estructura del `contract_data.yaml` sin leer ningún CSV del cliente, para que la separación entre "validar contrato" (esta feature) y "validar datos" (`load_data`, futura) se mantenga intacta. | Al invocar el comando (con contrato válido o inválido), no se abre, lee ni referencia ningún archivo bajo `data/bronze/` del tenant; el resultado depende únicamente del contenido de `contract_data.yaml`. |
| HU-10 | Como responsable de la integridad del motor, quiero que exponer `contract check` no requiera tocar `config/contract.py`, para tener la certeza de que el catálogo de mensajes M-01…M-13, ya congelado y verificado, sigue intacto tras esta feature. | Al cerrar la feature, `app/src/zeroleak/config/contract.py` es byte a byte idéntico al de `main` antes de empezar; la suite completa (111 tests vigentes + los nuevos) queda en verde. |
| HU-11 | Como responsable de cumplimiento del producto, quiero que el desarrollo y las pruebas de esta feature usen exclusivamente tenants y YAMLs sintéticos, para que la Bóveda de Datos (C-01) se respete por diseño también en la fachada de validación. | Todos los fixtures y tenants usados en pruebas (contratos válidos e inválidos, tenants con/sin contrato) son sintéticos y viven en `tmp_path`; ningún test usa datos reales de cliente. |

## Dependencias
- Features **`config_contract` (T-43, en `main` vía PR #3)** y **`contract_multifile` (T-57, en `main` vía
  PR #4)**: aportan el motor completo — `load_contract`, `Contract`, `ArchivoContrato`, `Columna`, `TipoDato`,
  `ContractParseError`, `ContractSchemaError` y el catálogo M-01…M-13 congelado y verificado — que esta
  feature consume sin modificar.
- Feature **`client_scaffold` (T-21, en `main`)**: crea el tenant y su `input/contract_data.yaml`
  placeholder; origen del caso de primera corrida (M-01) y de `_clients_root()`, reutilizado aquí.
- Feature **`ingest` (T-28, en `main`)**: aporta el patrón de fachada delgada a imitar — precondición de
  tenant traducida a exit code (`TenantNotFoundError`), y la forma de los tests de CLI (`main(argv)`).
- `900_persistence/tasks.md` **T-68** (esta feature; opción (a) elegida por el humano en el paso 1).
- `900_persistence/decisions.md`: **D-21** (descomposición por-YAML y frontera con `load_data`), **D-22**
  (cargar/validar vs. crear), **D-23c** (fail-fast), **D-25**/**D-26** (forma y disyunción de los mensajes),
  y **D-23d** (core-only de `contract_multifile`, que esta feature supera deliberadamente agregando una
  fachada, sin contradecir CA-27 de aquella feature).
- `700_architecture/system_design.md` §2.5/§4 (la CLI `zlk` como primera fachada del motor) y §5 (YAML 1 =
  Contrato de Datos).
- `900_persistence/constraints.md` **C-01** (Datos en Bóveda): solo tenants y YAMLs sintéticos.

## Riesgos y Supuestos
- **Supuesto:** la forma exacta de distinguir `ContractParseError` de `ContractSchemaError` en la salida
  (mismo exit code con prefijo distinto, o exit codes distintos) queda deliberadamente abierta para
  `spec_writer` (paso 6); el `feature_contract.md` la deja como decisión de spec (HU-02/HU-03 se redactan
  de forma neutral sobre el mecanismo exacto).
- **Supuesto:** la forma exacta del mensaje de éxito (HU-01) — qué identifica exactamente "tenant/contrato
  validado" en stdout — también se fija en la spec; el contrato solo exige que la señal sea clara.
- **Supuesto:** "mensaje de dominio claro" para tenant inexistente / sin contrato (HU-05) se interpreta
  siguiendo el patrón ya establecido por `ingest` con `TenantNotFoundError`; el exit code específico se
  decide en la spec.
- **Vacío heredado y fuera de alcance (D-21):** el emparejamiento del contrato con los archivos físicos
  ingeridos en bronze no lo cubre ninguna historia de esta definición; corresponde a `load_data`, etapa
  futura.
- **No se detectaron contradicciones** entre `feature_contract.md` y `900_persistence/decisions.md`
  (D-21, D-22, D-23c, D-23d, D-25, D-26): la fachada CLI que se agrega no modifica el core ni contradice el
  carácter core-only de `contract_multifile` (D-23d), consistente con la lectura explícita del contrato de
  que D-23d fue alcance de aquella feature, no prohibición permanente.
- **Dato sintético:** todo fixture usado en el notebook/spec posteriores debe ser un tenant y un
  `contract_data.yaml` sintéticos (válidos e inválidos), nunca datos reales de cliente, en línea con C-01.
