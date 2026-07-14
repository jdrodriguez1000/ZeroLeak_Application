# Feature Contract — ingest

> Artefacto **a nivel feature**, creado por la **sesión principal** (humano + Claude Code) en el paso 2 del flujo.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de escribir la definición**.
> **Una feature = una construcción completa** (Opción A, sin bandas): un solo ciclo SDD+TDD la lleva a "terminado".

## Estrella Polar
Registrar de forma **notarial** los archivos que el cliente entrega: copiarlos intactos a la capa **bronze**
del tenant y anotarlos en un ledger con su huella `sha256`, de modo que quede evidencia fiel e inmutable de
"qué llegó" y qué está **pendiente** de procesar — sin parsear ni interpretar su contenido.

## Definición de "Terminado"
Condiciones que deben cumplirse para considerar la feature **terminada** (comportamiento end-to-end completo):
- El comando `zlk ingest <CLIENTE> <ruta>...` registra en la capa bronze del tenant `<CLIENTE>` los archivos
  indicados, donde cada `<ruta>` es **un archivo o una carpeta**:
  - Si es **archivo**: se ingiere ese archivo (si su extensión está en la allow-list).
  - Si es **carpeta**: recorrido **plano** (solo primer nivel, sin recursión), ingiriendo los archivos cuya
    extensión esté en la allow-list e ignorando el resto en silencio.
  - Se aceptan **varios argumentos** `<ruta>` en una misma invocación.
- Por cada archivo ingerido, el comando:
  1. **Copia inmutable/fiel** de los bytes a `clients/<CLIENTE>/data/bronze/` (evidencia intacta, con PII).
  2. Calcula el **`sha256`** del contenido.
  3. Registra una entrada en `data/manifest.json` con `status: "pending"` (formato §11 de `system_design.md`).
- **Archivador notarial (principio de diseño clave):** `ingest` **no parsea el contenido** del archivo — solo
  copia bytes y hashea. El delimitador (`,`/`;`/`|`) y la estructura son problema de una etapa posterior
  (`load_data`/`validate`), **no** de `ingest`; bronze guarda el original intacto.
- **Dedupe por `sha256`:** reenviar un archivo con el **mismo contenido** ya registrado **no** lo duplica ni
  lo reprocesa (habilita el **Modo Incremental**, §10). El dedupe es por contenido, no por nombre.
- **Validación básica agnóstica de formato** (no se valida "es un CSV legible", para no acoplar a un formato):
  - (a) el **tenant destino existe** (hay `clients/<CLIENTE>/` con su estructura); si no, error claro.
  - (b) el archivo de entrada **existe y no está vacío**; si no, error claro para ese archivo.
  - (c) su **extensión está en la allow-list**.
- **Allow-list del MVP:** `.csv` y `.xlsx` **únicamente**; `.txt` queda explícitamente fuera.
- **Motor como API:** la operación vive en una función core (p. ej. `ingest_paths(client, paths, clients_root) -> ...`);
  la CLI es solo su fachada (P: la lógica no vive en la CLI).
- **Seguro por diseño (C-01):** bronze cae bajo la regla `.gitignore` `clients/*/data/`; los originales con PII
  nunca se versionan ni salen del tenant.

## Alcance
**In scope:**
- Core que registra archivos en bronze: copia inmutable + `sha256` + entrada en `manifest.json` (`status: pending`).
- Fachada CLI `zlk ingest <CLIENTE> <ruta>...` (uno o varios argumentos; cada uno archivo o carpeta).
- Entrada = **archivo o carpeta con recorrido plano** (sin recursión), filtrada por la allow-list.
- **Dedupe por `sha256`** (idempotencia por contenido: reenviar lo mismo no duplica ni reprocesa).
- Validación básica: tenant existe, archivo existe y no vacío, extensión en allow-list (`.csv`/`.xlsx`).
- Actualización del ledger `manifest.json` en el formato §11 (campos que aplican **hoy**: `file`, `sha256`,
  `ingested_at`, `status: pending`).

**Out of scope (nunca, o en otra feature):**
- **Parsear/leer el contenido** del archivo (delimitador, columnas, tipos): etapa posterior (`load_data`/`validate`).
- Llenar metadatos del manifiesto que dependen del **procesamiento**: `period`, `run_id`, `output` quedan
  vacíos/ausentes hasta que una etapa posterior procese el archivo.
- **Emparejar** el archivo físico con su tipo de contrato (`contract_data.yaml`) — **D-18, punto abierto**; se
  resolverá al construir `load_config`. `ingest` ingiere **todo** lo que caiga en la allow-list.
- Binarización Drop & Detach bronze → silver (feature `vault`).
- Cálculo de métricas / gold (features `finance`/`report`).
- Extensiones fuera de la allow-list del MVP (`.txt`, etc.), recorrido **recursivo** de subcarpetas y expansión
  de comodines/glob (se prefiere "ingerir carpeta" por ser agnóstico del shell — ver D-17).
- Dar de alta el tenant (eso es `client new` / `client_scaffold`, ya construido).

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **verificables y detallados** viven en `spec.md` como `CA-xx`.
1. Ejecutar `zlk ingest <CLIENTE> <archivo.csv>` sobre un tenant existente copia el archivo intacto a
   `data/bronze/` y agrega una entrada en `manifest.json` con `sha256` correcto y `status: "pending"`.
2. Ingerir una **carpeta** ingiere (recorrido plano) los `.csv`/`.xlsx` de su primer nivel e **ignora** los
   demás archivos y las subcarpetas.
3. Reenviar un archivo con **contenido idéntico** a uno ya registrado **no** crea copia ni entrada nueva
   (dedupe por `sha256`); un archivo con el mismo nombre pero **contenido distinto** sí se registra.
4. Un tenant inexistente, un archivo inexistente/vacío o una extensión fuera de la allow-list producen un
   **error claro** y **no** dejan artefactos parciales ni ledger corrupto.
5. El contenido de `bronze/` y del `manifest.json` respeta la frontera de PII de C-01: `data/` cae bajo
   `.gitignore` `clients/*/data/`.
6. `ingest` **no** interpreta el contenido: un `.csv` con delimitador `;` o `|` se registra igual que uno con
   `,` (se copian bytes y se hashea, sin parsear).

## Dependencias
- Feature `client_scaffold` (T-21, ya en `main`): el tenant destino y su estructura (`data/bronze/`,
  `manifest.json` inicial) deben existir antes de ingerir.
- `700_architecture/system_design.md` §10 (Modo Incremental), §11 (capas medallion + esquema de `manifest.json`).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda) — regla `.gitignore` `clients/*/data/`.
- `900_persistence/decisions.md` D-17 (alcance de `ingest`) y D-18 (emparejamiento archivo→contrato, abierto).

## Relación con Hitos de Producto
- **Segundo Tracer Bullet** del proyecto (T-28): reafirma el flujo de 13 pasos y el patrón multi-tenant sobre
  una feature de alcance más acotado que `client_scaffold`.
- Habilita el eje **datos**: sin `ingest` no hay nada en bronze que procesar; es la puerta de entrada del
  pipeline y la base de las features posteriores (`vault`, `modules`, `finance`, `report`).
