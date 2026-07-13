# Spec — ingest

> Artefacto del paso 6 (`spec_writer`), escrito **después** de aprobar el notebook (spike, gate del paso 5). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate, paso 7) antes de planear.

## Resumen
`ingest` registra de forma **notarial** los archivos que entrega un cliente: copia bytes intactos a la capa **bronze** del tenant, calcula su `sha256` y anota una entrada `status: "pending"` en `manifest.json`, sin parsear el contenido, con dedupe por contenido y procesamiento parcial por ruta.

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `clients/<CLIENTE>/data/bronze/` | Directorio | Debe existir (lo crea `client_scaffold`); precondición de tenant. |
| requiere | `clients/<CLIENTE>/data/manifest.json` | JSON | Ledger existente; al menos `{"files": [...]}`. Precondición de tenant. |
| requiere | `<ruta>...` | Archivo o carpeta | Entradas del usuario. Archivo → se ingiere si extensión ∈ allow-list; carpeta → recorrido plano (primer nivel). |
| produce | `clients/<CLIENTE>/data/bronze/<file>` | Bytes | Copia inmutable byte a byte del original ingerido. |
| produce | `clients/<CLIENTE>/data/manifest.json` | JSON | Se **agregan** entradas (nunca se sobreescriben las previas). |

**Entrada de manifest producida por `ingest` (subconjunto del esquema §11 que aplica hoy):**

| Campo | Tipo | Valor en ingest |
|---|---|---|
| `file` | string | Nombre **almacenado** en `bronze/` (puede llevar sufijo `__<sha8>` ante colisión de nombre). |
| `sha256` | string (64 hex) | `sha256` del contenido del archivo (identidad por contenido). |
| `ingested_at` | string ISO-8601 | Instante de la ingesta (`timespec=seconds`). |
| `status` | string | Siempre `"pending"` en esta feature. |

> Los campos `period`, `run_id` y `output` (§11) **no** los llena `ingest`: quedan fuera hasta una etapa posterior de procesamiento (out of scope).

**Allow-list del MVP:** `.csv`, `.xlsx` (comparación de extensión **case-insensitive**). Todo lo demás queda fuera.

## Comportamiento Esperado

1. **Precondición global (tenant).** Antes de procesar cualquier ruta, se verifica que el tenant exista con su estructura mínima (`data/bronze/` + `data/manifest.json`). Si no existe, se **aborta toda la invocación** sin tocar bronze ni el manifest, con código de salida `2`.
2. **Carga del ledger.** Se lee `manifest.json` una vez al inicio; las entradas nuevas se acumulan y se persisten al final en una sola escritura.
3. **Despacho por ruta.** Por cada `<ruta>` argumento (se aceptan varios):
   - Si es **archivo**: se ingiere (validación básica + copia + hash + entrada).
   - Si es **carpeta**: recorrido **plano** (solo primer nivel, sin recursión). Se ingieren los archivos con extensión ∈ allow-list; los demás archivos y las **subcarpetas** se **ignoran en silencio** (no son errores, no aparecen en el reporte de fallos).
   - Si **no existe** (ni archivo ni carpeta): se registra como fallo de esa ruta.
4. **Validación básica por archivo (agnóstica de formato).** Para cada archivo candidato: (a) existe; (b) extensión ∈ allow-list; (c) tamaño > 0 bytes. Si falla cualquiera, ese archivo se marca como fallo con su motivo y **no** se copia a bronze ni se anota en el manifest.
5. **Dedupe por contenido.** Si el `sha256` del archivo ya existe en el manifest, es un **no-op idempotente** reportado como duplicado (SKIP): no se copia ni se agrega entrada, y **no** cuenta como fallo.
6. **Copia notarial + nombrado en bronze.** Se copian los bytes tal cual a `data/bronze/`. Si ya existe un archivo con el **mismo nombre** pero **contenido distinto** (colisión de nombre, `sha256` diferente), se almacena con sufijo `__<sha8>` (primeros 8 hex del `sha256`) para no pisar la evidencia inmutable; el nombre almacenado se registra en el campo `file`.
7. **Registro en manifest.** Se agrega una entrada con `file`, `sha256`, `ingested_at`, `status: "pending"`.
8. **Reporte y código de salida.** Al terminar se informa, por ruta, qué salió bien / duplicado / falló, cada fallo con su motivo, y un resumen de conteos. El código de salida se deriva del resultado global (ver Casos Límite).
9. **CLI como fachada delgada.** La CLI `zlk ingest <CLIENTE> <ruta>...` solo invoca el core, imprime el reporte y traduce el resultado a código de salida; no contiene lógica de ingesta.

## Casos Límite y Errores

- **Tenant inexistente** → precondición global incumplida: aborta todo, no crea artefactos, exit code `2`.
- **Ruta inexistente** (ni archivo ni carpeta) → fallo de esa ruta, resto continúa.
- **Archivo vacío (0 bytes)** → fallo de esa ruta con motivo "archivo vacío".
- **Extensión fuera de allow-list pasada como archivo suelto** (p. ej. `reporte.txt`) → fallo de esa ruta con motivo "extensión fuera de allow-list".
- **Extensión fuera de allow-list dentro de una carpeta** → ignorada en silencio (no es fallo).
- **Subcarpeta dentro de una carpeta** → ignorada en silencio (sin recursión).
- **Contenido duplicado** (`sha256` ya en manifest) → SKIP idempotente, no cuenta como fallo.
- **Mismo nombre, contenido distinto** → nueva entrada con nombre `__<sha8>`.
- **Códigos de salida:** `0` = éxito total (0 fallos por ruta); `1` = éxito parcial o fallo por ruta (≥ 1 ruta fallida, procesamiento parcial); `2` = fallo global por precondición (tenant inexistente). Los duplicados (SKIP) **no** afectan el código de salida.
- **Corrupción del ledger:** un fallo por ruta nunca corrompe `manifest.json`; solo se persisten las entradas de archivos efectivamente ingeridos.

## Interfaces / Firmas Públicas

- **Core:** `ingest_paths(client: str, paths: list[str], clients_root: str | Path) -> IngestResult`
  - `IngestResult` expone las rutas por categoría (ingeridos / duplicados / fallidos, cada ítem con `path`, `status`, `reason`, y para ingeridos `sha256` y nombre almacenado) y un `exit_code` derivado (`0`/`1`).
  - Lanza `TenantNotFoundError` cuando el tenant no existe (precondición global) → la fachada lo traduce a exit code `2`.
- **CLI (fachada delgada):** `zlk ingest <CLIENTE> <ruta>...` → invoca el core, imprime el reporte OK/SKIP/FAIL + resumen, retorna el código de salida.

> Firmas a nivel de contrato observable; la estructura interna (algoritmo, tipos privados) es del bucle TDD.

## Criterios de Aceptación (verificables)

> Cada criterio lleva un **código `CA-xx`** (único en la feature) y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado un tenant existente y un `<archivo>.csv` sintético válido, `ingest_paths` copia el archivo a `data/bronze/<file>` de modo que `sha256(bronze/<file>) == sha256(original)` (copia byte a byte), y agrega **una** entrada en `manifest.json` con ese `sha256` y `status == "pending"`. | HU-01 |
| CA-02 | Tras ingerir un archivo, la entrada del manifest contiene exactamente los campos `file`, `sha256` (64 hex), `ingested_at` (ISO-8601) y `status`; **no** contiene `period`, `run_id` ni `output`. | HU-01 |
| CA-03 | Dada una carpeta con `a.csv`, `b.xlsx`, `c.txt` y una subcarpeta `sub/` que contiene `d.csv`, ingerir la carpeta registra exactamente 2 entradas (`a.csv`, `b.xlsx`); `c.txt`, `sub/` y `sub/d.csv` no aparecen en bronze ni en el manifest ni en la lista de fallos (ignorados en silencio). | HU-02 |
| CA-04 | Dada una invocación con argumentos mezclados `[archivo.csv, carpeta/]`, se ingieren el archivo suelto y todos los `.csv`/`.xlsx` del primer nivel de la carpeta; el conteo de ingeridos y las entradas del manifest reflejan la unión de ambos orígenes. | HU-03 |
| CA-05 | Reenviar un archivo cuyo `sha256` ya está en el manifest es un no-op: no se crea copia adicional en bronze, no se agrega entrada, se reporta como duplicado (SKIP) y `exit_code == 0` (no cuenta como fallo). | HU-04 |
| CA-06 | Ingerir un archivo con **mismo nombre** pero **contenido distinto** a uno ya en bronze crea una **nueva** entrada; el archivo se almacena como `<stem>__<sha8><suffix>` (los 8 primeros hex del nuevo `sha256`) sin sobrescribir el original, y el campo `file` de la nueva entrada es ese nombre con sufijo. | HU-04 |
| CA-07 | En una invocación con rutas válidas e inválidas mezcladas (válida + vacía + extensión no permitida + inexistente), solo la válida se ingiere y queda en el manifest; las 3 inválidas se reportan como fallos con su motivo respectivo ("archivo vacío", "extensión fuera de allow-list", "la ruta no existe") y `exit_code == 1`. | HU-05 |
| CA-08 | Invocar `ingest_paths` sobre un tenant inexistente lanza `TenantNotFoundError` (la fachada retorna exit code `2`) sin crear ni modificar ningún archivo en bronze ni en manifest de ningún tenant. | HU-05 |
| CA-09 | Un archivo de 0 bytes se reporta como fallo con motivo de archivo vacío, no se copia a bronze ni se registra en manifest; una invocación cuyo único archivo es vacío retorna `exit_code == 1`. | HU-05 |
| CA-10 | Tres archivos `.csv` con contenido lógicamente equivalente pero delimitador `,`, `;` y `|` respectivamente se ingieren los tres sin error (copia byte a byte, `sha256` sobre bytes), produciendo 3 entradas; `ingest` en ningún caso abre ni parsea el contenido como CSV. | HU-06 |
| CA-11 | La ruta relativa de todo archivo ingerido (`clients/<CLIENTE>/data/bronze/...`) y del `manifest.json` (`clients/<CLIENTE>/data/manifest.json`) cae bajo la regla `.gitignore` `clients/*/data/`; ningún archivo ingerido aparece como trackeable en `git status`. | HU-07 |
| CA-12 | El comportamiento completo de ingesta (validación, copia, hash, dedupe, nombrado, manifest, resultado) es observable llamando directamente a `ingest_paths(client, paths, clients_root)` sin usar la CLI; la CLI `zlk ingest` produce el mismo efecto invocando el core y traduciendo su `exit_code`. | HU-08 |

### Trazabilidad HU → Spec (cobertura)

> Toda `HU-xx` de `definition.md` está cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02 |
| HU-02 | CA-03 |
| HU-03 | CA-04 |
| HU-04 | CA-05, CA-06 |
| HU-05 | CA-07, CA-08, CA-09 |
| HU-06 | CA-10 |
| HU-07 | CA-11 |
| HU-08 | CA-12 |

## No-Objetivos

- **No** parsear ni interpretar el contenido (delimitador, columnas, tipos, encoding) — es `load_data`/`validate`.
- **No** llenar `period`, `run_id`, `output` del manifest — dependen de procesamiento posterior.
- **No** emparejar el archivo físico con su contrato de datos (`contract_data.yaml`) — D-18, punto abierto, se resuelve en `load_config`.
- **No** recorrido recursivo de subcarpetas ni expansión de comodines/glob (D-17).
- **No** aceptar extensiones fuera de la allow-list (`.txt`, etc.).
- **No** dar de alta el tenant — es `client_scaffold`, ya construido.
- **No** binarización bronze → silver (`vault`) ni cálculo de métricas/gold (`finance`/`report`).
