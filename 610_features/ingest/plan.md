# Plan — ingest

> Artefacto del paso 8 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate, paso 9) antes de arrancar el bucle.
>
> Base canónica: `spec.md` (CA-01 … CA-12, aprobada en el gate del paso 7, con 3 defaults ratificados por el humano), `definition.md` (HU-01 … HU-08), `system_design.md` §7/§10/§11, `constraints.md` C-01. Patrón de referencia: la feature `client_scaffold` ya en `main` (`core/scaffold.py`, `cli.py`, `conftest.py`, suite en `app/tests/`).
>
> **Defaults ratificados por el humano (gate paso 7) que este plan honra:**
> 1. Comparación de extensiones **case-insensitive** (`.CSV == .csv`).
> 2. La entrada de manifest tiene **solo** `file`, `sha256`, `ingested_at`, `status` (ausencia **verificable** de `period`/`run_id`/`output`).
> 3. `ingested_at` con **precisión de segundos** (`timespec="seconds"`).

## Enfoque Técnico

**Motor (core).** Toda la lógica de ingesta vive en un módulo nuevo `app/src/zeroleak/ingest/core.py`:

- `ingest_paths(client: str, paths: list[str], clients_root: str | Path) -> IngestResult` — única función pública. Orquesta: precondición global de tenant → carga del ledger → despacho por ruta → persistencia única del manifest → retorno del resultado.
- `class TenantNotFoundError(Exception)` — precondición global incumplida (tenant inexistente). La fachada la traduce a exit code `2`.
- `@dataclass IngestResult` — resultado observable, con tres colecciones por categoría y un `exit_code` derivado:
  - `ingested: list[...]` — cada ítem con `path` (origen), `stored_name` (nombre en bronze, con sufijo `__<sha8>` si hubo colisión), `sha256`, `status="ingested"`.
  - `duplicates: list[...]` — cada ítem con `path`, `sha256`, `status="duplicate"` (SKIP).
  - `failed: list[...]` — cada ítem con `path`, `reason`, `status="failed"`.
  - `exit_code -> int` (propiedad derivada): `0` si `failed` está vacío, `1` si hay ≥ 1 ruta fallida. Los duplicados **no** afectan el código.
- **Allow-list** como constante módulo-nivel: `ALLOWED_EXTENSIONS = {".csv", ".xlsx"}`; la comparación normaliza con `Path(p).suffix.lower()` (default 1, case-insensitive).
- **Motivos de fallo** como constantes de texto estable: `"archivo vacío"`, `"extensión fuera de allow-list"`, `"la ruta no existe"` (referenciables por los tests, sin acoplarlos a redacciones frágiles).

**Precondición global de tenant.** Antes de tocar nada, se resuelve `tenant_dir = clients_root/client` y se verifica que existan `data/bronze/` **y** `data/manifest.json`. Si falta la estructura mínima, se lanza `TenantNotFoundError` **sin** crear ni modificar ningún artefacto (aborta toda la invocación).

**Carga y persistencia del ledger (una sola escritura).** El `manifest.json` se lee **una vez** al inicio (`{"version": 1, "files": [...]}`, formato producido por `client_scaffold`). Las entradas nuevas se acumulan en memoria y se **agregan** (nunca se sobreescriben las previas); se persiste **al final**, en una única escritura, solo si hubo entradas efectivamente ingeridas. Un fallo por ruta nunca corrompe el ledger.

**Despacho por ruta (procesamiento parcial).** Por cada `<ruta>` de `paths`:
- **Archivo** → validación básica + (dedupe) + copia + hash + entrada.
- **Carpeta** → recorrido **plano** (`iterdir()`, primer nivel, sin recursión): se ingieren los archivos con extensión ∈ allow-list; subcarpetas y archivos fuera de la allow-list se **ignoran en silencio** (no aparecen en `failed`).
- **No existe** → se registra como fallo de esa ruta con motivo `"la ruta no existe"`.

**Validación básica por archivo (agnóstica de formato).** (a) existe; (b) `suffix.lower() ∈ ALLOWED_EXTENSIONS`; (c) `stat().st_size > 0`. Cualquier fallo → ítem en `failed` con su motivo; **no** se copia a bronze ni se anota en el manifest. `ingest` **nunca** abre ni parsea el contenido (default: byte a byte).

**Dedupe por contenido.** Se calcula `sha256` sobre los **bytes** del archivo. Si ese `sha256` ya está en el manifest (entradas previas + acumuladas en esta corrida), es un **no-op idempotente** reportado como duplicado (SKIP): no se copia ni se agrega entrada; no cuenta como fallo.

**Copia notarial + nombrado en bronze.** Se copian los bytes tal cual a `data/bronze/`. Nombre por defecto = nombre original. Si ya existe en bronze un archivo con el **mismo nombre** pero **contenido distinto** (`sha256` diferente), se almacena como `<stem>__<sha8><suffix>` (los 8 primeros hex del nuevo `sha256`) para no pisar la evidencia inmutable; ese nombre almacenado se registra en el campo `file`.

**Entrada de manifest (default 2 + default 3).** Constructor que emite **exactamente** `{"file", "sha256", "ingested_at", "status"}`, con `ingested_at = datetime.now().isoformat(timespec="seconds")` (default 3) y `status = "pending"`. **No** se emiten `period`/`run_id`/`output` (default 2: ausencia verificable).

**Fachada CLI (fachada delgada).** `app/src/zeroleak/cli.py` gana el subcomando `zlk ingest <CLIENTE> <ruta>...`: parsea, resuelve `clients_root` (convención `ZEROLEAK_CLIENTS_ROOT`, ya usada por `client new`), invoca `ingest_paths`, imprime el reporte `OK`/`SKIP`/`FAIL` + resumen de conteos y **traduce** el resultado a exit code:
- `0` — éxito total (`IngestResult.exit_code == 0`).
- `1` — éxito parcial / ≥ 1 ruta fallida (`IngestResult.exit_code == 1`).
- `2` — precondición global (`TenantNotFoundError`).
La CLI **no** contiene lógica de ingesta: el efecto en disco es idéntico al del core invocado directamente (CA-12).

## Archivos Afectados
- `app/src/zeroleak/ingest/core.py` — **crear** (core `ingest_paths`, `IngestResult`, `TenantNotFoundError`, allow-list, motivos, validación, dedupe, copia+nombrado, constructor de entrada de manifest, carga/persistencia del ledger).
- `app/src/zeroleak/ingest/__init__.py` — **modificar** (reexportar `ingest_paths`, `IngestResult`, `TenantNotFoundError`).
- `app/src/zeroleak/cli.py` — **modificar** (parseo/despacho de `ingest`, impresión de reporte, traducción a exit codes 0/1/2).
- `app/tests/conftest.py` — **modificar** (fixtures sintéticas nuevas: factory de tenant ingerible, generadores de `.csv` con delimitador configurable / `.xlsx` como bytes opacos / archivo vacío, y helper de lectura del manifest).
- `app/tests/test_ingest.py` — **crear** (unit tests del core `ingest_paths`).
- `app/tests/test_cli_ingest.py` — **crear** (tests de la fachada CLI y exit codes 0/1/2).
- `app/tests/integration/test_ingest_e2e.py` — **crear** (integración end-to-end del comando `zlk ingest` instalado, por subprocess).
- `.gitignore` — **verificar** (la regla `clients/*/data/` ya está vigente; CA-11 la caracteriza sobre `bronze/` y `manifest.json`, sin cambio de código).

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición: un solo responsable, un solo entregable, codificar ≠ testear (test-first, la tarea de test antecede a la de código). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`. **Estado** ∈ `no_implementada | implementada | cancelada_suspendida`; el responsable es el único que actualiza el estado de su tarea (Single Writer Rule). Se crean todas en `no_implementada`.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Fixtures sintéticas para ingest: factory de tenant ingerible (`data/bronze/` + `data/manifest.json` inicial), generadores de archivo `.csv` con delimitador configurable, `.xlsx` como bytes opacos, archivo vacío (0 bytes), y helper de lectura del `manifest.json`. Todo sintético (C-01). | Adiciones a `app/tests/conftest.py` | tdd_tester | implementada (parcial: `ingestible_tenant` + `read_manifest` para Caso 1; generadores `.csv`/`.xlsx`/vacío pendientes para casos posteriores) | CA-01 (andamiaje) |
| TSK-02 | Test: `ingest_paths` sobre un `client` sin estructura de tenant lanza `TenantNotFoundError` y no crea/modifica ningún artefacto en bronze ni en manifest de ningún tenant. | Test "tenant-inexistente" en `test_ingest.py` | tdd_tester | implementada | CA-08 |
| TSK-03 | Excepción `TenantNotFoundError` + guarda de precondición global: resolver `tenant_dir` y verificar `data/bronze/` + `data/manifest.json`; si falta, lanzar sin tocar disco. | Bloque precondición + excepción en `core.py` | tdd_coder | implementada | CA-08 |
| TSK-04 | Test: dado un tenant y un `.csv` sintético válido, `ingest_paths` copia a `data/bronze/<file>` con `sha256(bronze) == sha256(original)` (byte a byte) y agrega **una** entrada con ese `sha256` y `status == "pending"`. | Test "ingesta-csv-simple" en `test_ingest.py` | tdd_tester | implementada | CA-01 |
| TSK-05 | Core camino feliz de `ingest_paths`: cargar ledger, validar, calcular `sha256`, copiar bytes a bronze, agregar entrada `pending`, persistir manifest en una sola escritura, retornar `IngestResult` con `exit_code == 0`. | Camino feliz + `IngestResult` en `core.py` | tdd_coder | implementada | CA-01 |
| TSK-06 | Test: la entrada del manifest contiene **exactamente** `file`, `sha256` (64 hex), `ingested_at` (ISO-8601, `timespec` segundos) y `status`; **no** contiene `period`, `run_id` ni `output` (ausencia verificable). | Test "manifest-shape" en `test_ingest.py` | tdd_tester | implementada (test de caracterización de CA-02; no hubo RED porque CA-02 se satisfizo en el Caso 2) | CA-02 |
| TSK-07 | Constructor de entrada de manifest que emite exactamente las 4 claves, con `ingested_at = datetime.now().isoformat(timespec="seconds")` y `status = "pending"` (sin `period`/`run_id`/`output`). | Constructor de entrada en `core.py` | tdd_coder | cancelada_suspendida (sin código nuevo; CA-02 ya cubierto por el código del Caso 2, TSK-05/`_build_manifest_entry`) | CA-02 |
| TSK-08 | Test: un archivo de 0 bytes se reporta como fallo con motivo de archivo vacío, no se copia a bronze ni se registra en manifest; una invocación cuyo único archivo es vacío retorna `exit_code == 1`. | Test "archivo-vacio" en `test_ingest.py` | tdd_tester | implementada | CA-09 |
| TSK-09 | Validación básica por archivo (existe / extensión ∈ allow-list case-insensitive / tamaño > 0) que enruta a `failed` con el motivo correcto sin copiar ni anotar; derivación de `exit_code == 1` cuando hay ≥ 1 fallo. | Validación + motivos + exit_code en `core.py` | tdd_coder | implementada (parcial: solo validación de tamaño > 0 / "archivo vacío" para el Caso 4; validación de existencia y extensión quedan para casos posteriores) | CA-09 |
| TSK-10 | Test: reenviar un archivo cuyo `sha256` ya está en el manifest es no-op (no crea copia ni entrada), se reporta como duplicado (SKIP) y `exit_code == 0`. | Test "dedupe-sha256" en `test_ingest.py` | tdd_tester | implementada | CA-05 |
| TSK-11 | Dedupe por contenido: si el `sha256` ya existe en el manifest (previos + acumulados), marcar como duplicado (SKIP) sin copiar ni agregar entrada; no cuenta como fallo. | Lógica de dedupe en `core.py` | tdd_coder | implementada | CA-05 |
| TSK-12 | Test: ingerir un archivo con **mismo nombre** pero **contenido distinto** a uno ya en bronze crea una **nueva** entrada; el archivo se almacena como `<stem>__<sha8><suffix>` sin sobrescribir el original, y `file` es ese nombre con sufijo. | Test "colision-nombre-sufijo" en `test_ingest.py` | tdd_tester | no_implementada | CA-06 |
| TSK-13 | Nombrado en bronze ante colisión de nombre con contenido distinto: detectar mismo nombre + `sha256` distinto y almacenar con sufijo `__<sha8>`; registrar el nombre almacenado en `file`. | Lógica de nombrado en `core.py` | tdd_coder | no_implementada | CA-06 |
| TSK-14 | Test: una carpeta con `a.csv`, `b.xlsx`, `c.txt` y `sub/d.csv` registra exactamente 2 entradas (`a.csv`, `b.xlsx`); `c.txt`, `sub/` y `sub/d.csv` no aparecen en bronze, ni en manifest, ni en fallos. | Test "carpeta-recorrido-plano" en `test_ingest.py` | tdd_tester | no_implementada | CA-03 |
| TSK-15 | Despacho por ruta para carpetas: recorrido plano (`iterdir`, sin recursión), ingerir solo extensiones ∈ allow-list, ignorar en silencio subcarpetas y demás archivos (no van a `failed`). | Despacho de carpeta en `core.py` | tdd_coder | no_implementada | CA-03 |
| TSK-16 | Test: invocación con argumentos mezclados `[archivo.csv, carpeta/]` ingiere el archivo suelto y los `.csv`/`.xlsx` del primer nivel de la carpeta; conteos y entradas reflejan la unión de ambos orígenes. | Test "args-mezclados" en `test_ingest.py` | tdd_tester | no_implementada | CA-04 |
| TSK-17 | Despacho multi-argumento: iterar sobre todos los `paths` (archivo o carpeta) acumulando resultados en las colecciones de `IngestResult` (unión de orígenes, sin duplicar el ledger). | Bucle de despacho multi-ruta en `core.py` | tdd_coder | no_implementada | CA-04 |
| TSK-18 | Test: tres `.csv` con contenido equivalente pero delimitador `,`, `;`, `\|` se ingieren los tres (copia byte a byte, `sha256` sobre bytes), produciendo 3 entradas; en ningún caso se parsea el contenido como CSV. | Test "delimitadores-sin-parseo" en `test_ingest.py` | tdd_tester | no_implementada | CA-10 |
| TSK-19 | Confirmar (mínimo-suficiente) que el core opera solo sobre bytes: `sha256` y copia sin abrir/parsear; asegurar que 3 contenidos distintos generan 3 `sha256` distintos → 3 entradas. | Verificación/ajuste agnóstico-de-formato en `core.py` | tdd_coder | no_implementada | CA-10 |
| TSK-20 | Test: invocación con rutas válida + vacía + extensión no permitida + inexistente ingiere solo la válida; las 3 inválidas van a `failed` con su motivo respectivo (`"archivo vacío"`, `"extensión fuera de allow-list"`, `"la ruta no existe"`) y `exit_code == 1`. | Test "mezcla-valida-invalida" en `test_ingest.py` | tdd_tester | no_implementada | CA-07 |
| TSK-21 | Procesamiento parcial por ruta: cada ruta se valida/procesa de forma independiente (una falla no aborta el resto); consolidación de motivos y derivación final de `exit_code` (0 sin fallos, 1 con ≥ 1 fallo). | Procesamiento parcial + consolidación en `core.py` | tdd_coder | no_implementada | CA-07 |
| TSK-22 | Test: `git check-ignore` marca como ignorada cualquier ruta bajo `clients/<X>/data/bronze/...` y `clients/<X>/data/manifest.json`, y NO marca `client.yaml` ni `input/` (rutas ficticias, sin crear tenant real; C-01). | Test "gitignore-frontera-pii" en `test_ingest.py` | tdd_tester | no_implementada | CA-11 |
| TSK-23 | Test: el comportamiento completo es observable llamando directamente a `ingest_paths(...)`; y `zlk ingest <CLIENTE> <ruta>...` produce el mismo efecto en disco invocando el core y traduciendo `exit_code` (0 éxito, 1 parcial/fallo, 2 tenant inexistente). | Tests "core-observable" y "cli-equivalencia+exit-codes" en `test_cli_ingest.py` | tdd_tester | no_implementada | CA-12 |
| TSK-24 | Fachada CLI `zlk ingest <CLIENTE> <ruta>...`: parsear subcomando, resolver `clients_root`, invocar `ingest_paths`, imprimir reporte OK/SKIP/FAIL + resumen, traducir `IngestResult.exit_code` (0/1) y `TenantNotFoundError` → 2 (sin lógica de ingesta propia). | Despacho `ingest` en `cli.py` | tdd_coder | no_implementada | CA-12 |
| TSK-25 | Prueba de integración end-to-end: ejecutar el comando instalado `zlk ingest` por subprocess sobre un `clients_root` temporal (tenant sintético); verificar éxito y estructura en bronze/manifest, exit code 1 en mezcla válida/inválida, exit code 2 en tenant inexistente, y equivalencia con `ingest_paths` en proceso. | `app/tests/integration/test_ingest_e2e.py` | integration_tester | no_implementada | CA-01, CA-12 |
| TSK-26 | Refactor de `core.py` manteniendo verde: extraer helpers cohesivos (validación, hash+copia, nombrado, carga/persistencia del ledger), nombrar constantes de motivos y allow-list, docstrings con referencia a CA. | `core.py` refactorizado | tdd_refactor | no_implementada | CA-01 (calidad) |
| TSK-27 | Refactor de `cli.py` manteniendo verde: separar parseo, despacho, formateo del reporte y traducción de resultado/errores a exit codes en unidades legibles, sin duplicar con la rama `client new`. | `cli.py` refactorizado | tdd_refactor | no_implementada | CA-12 (calidad) |

## Dependencias y Contratos
- **Consume:** feature `client_scaffold` (ya en `main`): el tenant destino y su estructura (`data/bronze/`, `data/manifest.json` inicial `{"version": 1, "files": []}`) deben existir antes de ingerir; `system_design.md` §11 (esquema de `manifest.json`, capas medallion); `constraints.md` C-01 (regla `.gitignore clients/*/data/`, ya vigente); convención `ZEROLEAK_CLIENTS_ROOT` para resolver `clients_root` en la CLI (fijada por `client_scaffold`). No requiere dependencias nuevas en `pyproject.toml` (el `.xlsx` sintético se genera como bytes opacos; `ingest` nunca lo abre, así que no se necesita `openpyxl`).
- **Produce:** función core `ingest_paths`, `IngestResult`, `TenantNotFoundError`, fachada `zlk ingest`. Efecto en disco: copias inmutables en `data/bronze/` y entradas `pending` **agregadas** a `data/manifest.json`.
- **Habilita:** las etapas posteriores del pipeline (`load_data`, `validate`, `vault`) que consumen los archivos `pending` de bronze y el `manifest.json`.

## Estrategia de Test
- **Unit (`test_ingest.py`):** precondición de tenant (`TenantNotFoundError`), ingesta byte-a-byte + entrada `pending`, forma exacta de la entrada de manifest (4 campos, ausencia de `period`/`run_id`/`output`, `ingested_at` con segundos), validación (archivo vacío, extensión fuera de allow-list, ruta inexistente) con motivos y `exit_code`, dedupe por `sha256` (SKIP), nombrado `__<sha8>` ante colisión de nombre, recorrido plano de carpeta con ignorado silencioso, argumentos mezclados (archivo + carpeta), agnosticismo de formato (delimitadores `,`/`;`/`\|`), procesamiento parcial (mezcla válida/inválida → exit 1), y frontera PII del `.gitignore`.
- **CLI (`test_cli_ingest.py`):** observabilidad del core sin CLI y equivalencia core↔CLI (mismo efecto en disco), traducción a exit codes 0/1/2, e impresión del reporte OK/SKIP/FAIL.
- **Integración (`test_ingest_e2e.py`, `integration_tester`):** ejecución real del comando `zlk ingest` por subprocess sobre un `clients_root` temporal, verificando bronze/manifest en disco real, exit codes y equivalencia con el core (la costura CLI instalada → proceso → disco).
- **Fixtures / datos de prueba:** **sintéticos** (Regla "Datos en Bóveda", C-01). `clients_root` siempre en `tmp_path`; tenants y archivos ficticios (`SANDUCHERIA`, `a.csv`, `b.xlsx`, contenidos falsos); ningún dato real ni sensible del cliente. El `.xlsx` sintético es bytes opacos (nunca se parsea).

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Deben coincidir con `stages.tdd.cases[]` del `state.json` de la feature. Cada caso agrupa sus tareas de test y de código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `ingest_paths` sobre un tenant inexistente lanza `TenantNotFoundError` sin crear/modificar bronze ni manifest de ningún tenant. | TSK-02, TSK-03 | CA-08 |
| 2 | Un `.csv` sintético válido se copia byte a byte a `data/bronze/<file>` (`sha256` igual) y agrega **una** entrada con ese `sha256` y `status == "pending"`. | TSK-01, TSK-04, TSK-05 | CA-01 |
| 3 | La entrada del manifest tiene exactamente `file`, `sha256` (64 hex), `ingested_at` (ISO, segundos) y `status`; sin `period`/`run_id`/`output`. | TSK-06, TSK-07 | CA-02 |
| 4 | Un archivo de 0 bytes se reporta como fallo "archivo vacío", no se copia ni se anota, y la invocación retorna `exit_code == 1`. | TSK-08, TSK-09 | CA-09 |
| 5 | Reenviar un archivo con `sha256` ya presente es no-op (SKIP): sin copia ni entrada nueva, `exit_code == 0` (no cuenta como fallo). | TSK-10, TSK-11 | CA-05 |
| 6 | Mismo nombre, contenido distinto → nueva entrada almacenada como `<stem>__<sha8><suffix>` sin sobrescribir el original; `file` refleja el nombre con sufijo. | TSK-12, TSK-13 | CA-06 |
| 7 | Carpeta con `a.csv`, `b.xlsx`, `c.txt`, `sub/d.csv` → exactamente 2 entradas (`a.csv`, `b.xlsx`); `c.txt`, `sub/`, `sub/d.csv` ignorados en silencio. | TSK-14, TSK-15 | CA-03 |
| 8 | Argumentos mezclados `[archivo.csv, carpeta/]` → se ingiere el archivo suelto y los `.csv`/`.xlsx` del primer nivel; conteos/entradas reflejan la unión. | TSK-16, TSK-17 | CA-04 |
| 9 | Tres `.csv` con delimitador `,`, `;`, `\|` se ingieren los tres (byte a byte, `sha256` sobre bytes) → 3 entradas; nunca se parsea el contenido. | TSK-18, TSK-19 | CA-10 |
| 10 | Mezcla válida + vacía + extensión no permitida + inexistente → solo la válida se ingiere; las 3 inválidas en `failed` con su motivo; `exit_code == 1`. | TSK-20, TSK-21 | CA-07 |
| 11 | La regla `.gitignore clients/*/data/` cubre `bronze/...` y `manifest.json`, y NO cubre `client.yaml` ni `input/` (versionables). | TSK-22 | CA-11 |
| 12 | El comportamiento es observable llamando a `ingest_paths` sin CLI; `zlk ingest` produce el mismo efecto y traduce el `exit_code` (0/1/2). | TSK-23, TSK-24 | CA-12 |

> **Integración (fuera del bucle rojo-verde, tras el core y la CLI):** TSK-25 (`integration_tester`) valida el comando instalado `zlk ingest` end-to-end por subprocess (CA-01, CA-12). **Refactor:** TSK-26 y TSK-27 se ejecutan en la fase `tdd_refactor` manteniendo verde.

## Verificación de Cobertura (todo CA-xx tiene ≥ 1 TSK-xx)
| CA | Cubierto por |
|---|---|
| CA-01 | TSK-01, TSK-04, TSK-05, TSK-25, TSK-26 |
| CA-02 | TSK-06, TSK-07 |
| CA-03 | TSK-14, TSK-15 |
| CA-04 | TSK-16, TSK-17 |
| CA-05 | TSK-10, TSK-11 |
| CA-06 | TSK-12, TSK-13 |
| CA-07 | TSK-20, TSK-21 |
| CA-08 | TSK-02, TSK-03 |
| CA-09 | TSK-08, TSK-09 |
| CA-10 | TSK-18, TSK-19 |
| CA-11 | TSK-22 |
| CA-12 | TSK-23, TSK-24, TSK-25, TSK-27 |

## Riesgos Técnicos / Decisiones a Validar en el Gate (paso 9)
- **`ingested_at` sin zona horaria (default 3).** Se usa `datetime.now().isoformat(timespec="seconds")` (hora local, sin `tzinfo`), coherente con el ejemplo de `system_design.md` §11. Si se prefiriera UTC/`timezone.utc`, es un ajuste puntual del constructor; el test de CA-02 solo exige ISO-8601 parseable con precisión de segundos, así que ambas variantes lo satisfacen. **A confirmar por el humano.**
- **Definición de "tenant inexistente" (precondición global).** El plan la implementa como "falta `data/bronze/` **o** `data/manifest.json`", no solo "la carpeta `clients/<X>/` no existe". Esto cubre un tenant a medio crear y evita anotar sobre un ledger ausente. **A validar.**
- **Semántica de `__<sha8>` (CA-06).** El sufijo se aplica solo ante **colisión de nombre con contenido distinto** (mismo `file`, `sha256` diferente). Un mismo nombre con **mismo** contenido cae antes en dedupe (SKIP). Se asume que `<sha8>` (8 hex) es suficientemente único para el volumen de un tenant; una colisión de 8 hex es despreciable y no se maneja como caso especial en el MVP.
- **Dedupe dentro de la misma invocación.** El dedupe considera tanto el ledger previo como las entradas **acumuladas en la corrida**: si dos rutas de la misma invocación tienen `sha256` idéntico, la segunda se reporta como duplicado (SKIP). **A confirmar** que ése es el comportamiento esperado (coherente con "idempotencia por contenido").
- **`.xlsx` sintético sin `openpyxl`.** Como `ingest` no parsea, los fixtures `.xlsx` se generan como bytes opacos con extensión `.xlsx`; no se añade dependencia. Esto refuerza CA-10 (agnosticismo de formato) pero conviene que el humano lo note.
- **Formato del reporte OK/SKIP/FAIL.** La spec fija categorías, motivos y códigos de salida, pero no el layout textual exacto; se deja al `tdd_coder`/`tdd_refactor` con un formato legible, verificado por conteos y presencia de motivos (no por strings frágiles).
- **`.gitignore` ya vigente (CA-11).** No requiere cambio de código; el test caracteriza el comportamiento real de Git sobre `bronze/` y `manifest.json` con rutas ficticias (sin crear tenant real, C-01), igual que en `client_scaffold`.

---

**Siguiente paso:** gate humano (paso 9) para aprobar/rechazar este plan. **No** se arranca el bucle TDD (paso 10: `tdd_tester → tdd_coder → tdd_refactor`) hasta la aprobación.
