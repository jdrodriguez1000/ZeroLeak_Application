# Plan — client_scaffold

> Artefacto del paso 8 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate, paso 9) antes de arrancar el bucle.
>
> Base canónica: `spec.md` (CA-01 … CA-10, aprobada en el gate del paso 7), `feature_contract.md`, `definition.md` (HU-01 … HU-08), `system_design.md` §11–§12 y `constraints.md` C-01.

## Enfoque Técnico

**Motor (core).** Toda la lógica vive en un módulo nuevo `app/src/zeroleak/core/scaffold.py`:

- `create_client(name: str, clients_root: Path) -> Path` — única función pública; orquesta validación → construcción atómica → retorno de la `Path` del tenant.
- `class ClientNameError(Exception)` y `class TenantExistsError(Exception)` — excepciones de dominio.
- `NAME_PATTERN` — constante módulo-nivel con el patrón **congelado** por la spec: `^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$` (allow-list explícita, **sin** `\w` Unicode amplio). La validación usa `re.fullmatch(NAME_PATTERN, name)` **antes** de tocar disco.
- Helpers internos de render de placeholders: `client.yaml` + los 3 YAMLs de `input/` (`contrato_datos.yaml`, `reglas_negocio.yaml`, `finanzas.yaml`) y `data/manifest.json`.

**Placeholders YAML (decisión del humano, punto 2).** Placeholder **mínimo genérico**: cada archivo se genera con un comentario guía y una o dos claves marcador de **valor vacío**; NO se enumera el esquema completo (lo definirán las features `ingest`/`vault`/`finance`). `client.yaml` sí lleva sus claves de identidad vacías con comentarios: `client_id`, `display_name`, `sector_id`, `created_at`. Todos deben ser parseables por `yaml.safe_load` sin excepción y sin datos reales/sensibles.

**Atomicidad todo-o-nada (decisión del humano, punto 3).** Patrón **staging + rename**:
1. Construir el árbol completo del tenant dentro de un directorio de staging `clients_root/.staging-<uuid>/` (creado **dentro de `clients_root`** para que resida en el **mismo filesystem** que el destino y el `rename` sea atómico).
2. Promover con `os.replace(staging_dir, clients_root/name)` (rename atómico del directorio ya completo).
3. `try/except` que ante **cualquier** fallo elimina el staging (`shutil.rmtree`), de modo que `clients_root` no gana ningún residuo (`.staging` ni tenant parcial).
La comprobación de existencia (`TenantExistsError`) se hace **antes** de promover; `os.replace` sobre un destino existente también falla, como red de seguridad.

**Fachada CLI (decisión del humano, puntos 1 y 5).** `app/src/zeroleak/cli.py` implementa `zlk client new <NOMBRE>`: parsea el subcomando, resuelve `clients_root`, invoca `create_client`, imprime la ruta creada y **traduce** las excepciones de dominio a **exit codes distintos**:
- `0` — éxito (reporta la ruta del tenant).
- `2` — nombre inválido (`ClientNameError`).
- `3` — tenant existente (`TenantExistsError`).
La CLI **no** contiene lógica de negocio: el resultado en disco de la CLI es idéntico al del core invocado directamente.

## Archivos Afectados
- `app/src/zeroleak/core/scaffold.py` — **crear** (core `create_client`, excepciones, `NAME_PATTERN`, render de placeholders y manifest, atomicidad staging+rename).
- `app/src/zeroleak/cli.py` — **modificar** (fachada `client new`, resolución de `clients_root`, traducción excepciones → exit codes 0/2/3).
- `app/tests/conftest.py` — **crear** (fixtures sintéticas: `clients_root` limpio en `tmp_path`, helper de snapshot de árbol).
- `app/tests/test_scaffold.py` — **crear** (unit tests del core).
- `app/tests/test_cli_client_new.py` — **crear** (tests de la fachada CLI y exit codes).
- `app/tests/integration/test_client_new_e2e.py` — **crear** (integración end-to-end del comando instalado).
- `.gitignore` — **verificar** (la regla `clients/*/data/` ya está vigente; CA-09 la caracteriza, sin cambio de código).
- `clients/COMPANY_DEMO/{client.yaml,input/}` — **crear/versionar** (tenant de demostración por la vía oficial; `data/` queda gitignored).

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición: un solo responsable, un solo entregable, codificar ≠ testear (test-first). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`. **Estado** ∈ `no_implementada | implementada | cancelada_suspendida`; el responsable es el único que actualiza el estado de su tarea (Single Writer Rule). Se crean todas en `no_implementada`.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Fixtures sintéticas: `clients_root` limpio en `tmp_path` y helper de snapshot (rutas + tamaños) del árbol de un tenant. | `app/tests/conftest.py` | tdd_tester | no_implementada | CA-01 (andamiaje) |
| TSK-02 | Test parametrizado: cada nombre inválido del conjunto de CA-04 hace que `create_client` lance `ClientNameError`. | Grupo de tests "validación-inválidos" en `test_scaffold.py` | tdd_tester | no_implementada | CA-04 |
| TSK-03 | Excepciones `ClientNameError`/`TenantExistsError` + validación `re.fullmatch(NAME_PATTERN, name)` que lanza `ClientNameError` **antes** de tocar disco. | Bloque validación+excepciones en `scaffold.py` | tdd_coder | no_implementada | CA-04 |
| TSK-04 | Test: sobre `clients_root` limpio, `create_client("SANDUCHERIA", root)` retorna `root/"SANDUCHERIA"` y existen los 6 artefactos canónicos (client.yaml, 3 input YAMLs, data/{bronze,silver,gold}, manifest.json). | Test "estructura-canónica" en `test_scaffold.py` | tdd_tester | no_implementada | CA-01 |
| TSK-05 | `create_client`: crea el árbol de directorios del tenant (`<name>/`, `input/`, `data/{bronze,silver,gold}`) y retorna la `Path`. | Creación de directorios + retorno en `scaffold.py` | tdd_coder | no_implementada | CA-01 |
| TSK-06 | Test parametrizado: cada nombre válido del conjunto de CA-05 crea el tenant; assert de que `NAME_PATTERN` es exactamente el patrón allow-list de la spec. | Grupo de tests "validación-válidos" en `test_scaffold.py` | tdd_tester | no_implementada | CA-05 |
| TSK-07 | Congelar el patrón como constante `NAME_PATTERN` a nivel de módulo (allow-list explícita, sin `\w`), referenciable por los tests. | Constante `NAME_PATTERN` en `scaffold.py` | tdd_coder | no_implementada | CA-05 |
| TSK-08 | Test: `client.yaml` y los 3 YAMLs de `input/` cargan con `yaml.safe_load` sin excepción, tienen las claves esperadas con valores vacíos y ≥1 comentario `#`; `client.yaml` incluye `client_id`, `display_name`, `sector_id`, `created_at`; ninguno contiene datos reales. | Grupo de tests "placeholders-yaml" en `test_scaffold.py` | tdd_tester | no_implementada | CA-07 |
| TSK-09 | Escribir los 4 placeholders YAML (client.yaml + contrato_datos/reglas_negocio/finanzas) con placeholder mínimo genérico: comentario guía + clave(s) marcador vacías; identidad vacía comentada en client.yaml. | Render de placeholders YAML en `scaffold.py` | tdd_coder | no_implementada | CA-07 |
| TSK-10 | Test: existen `data/bronze|silver|gold/` (vacíos) y `data/manifest.json` parsea como JSON igual a `{"version": 1, "files": []}`. | Grupo de tests "medallion-manifest" en `test_scaffold.py` | tdd_tester | no_implementada | CA-08 |
| TSK-11 | Escribir `data/manifest.json` inicial `{"version": 1, "files": []}` (ledger vacío válido). | Render de `manifest.json` en `scaffold.py` | tdd_coder | no_implementada | CA-08 |
| TSK-12 | Test: un nombre inválido no deja residuos en `clients_root` (ni tenant parcial ni carpeta `.staging`). | Test "sin-residuo-nombre-inválido" en `test_scaffold.py` | tdd_tester | no_implementada | CA-04 |
| TSK-13 | Test: fallo de E/S a mitad (monkeypatch que fuerza excepción durante la construcción) se propaga y `clients_root` no gana residuos (todo-o-nada). | Test "atomicidad-fallo-io" en `test_scaffold.py` | tdd_tester | no_implementada | CA-04 (andamiaje atomicidad) |
| TSK-14 | Implementar atomicidad staging+rename: construir en `clients_root/.staging-<uuid>/` (mismo filesystem), promover con `os.replace`, y limpiar el staging en `except`. | Mecanismo de atomicidad en `scaffold.py` | tdd_coder | no_implementada | CA-04 |
| TSK-15 | Test: tras crear el tenant `T`, un segundo `create_client("T", root)` lanza `TenantExistsError` y el snapshot del tenant existente es idéntico antes/después. | Test "tenant-existente" en `test_scaffold.py` | tdd_tester | no_implementada | CA-06 |
| TSK-16 | Guarda de no idempotencia: si `clients_root/name` ya existe, lanzar `TenantExistsError` sin modificar el tenant existente (chequeo previo + `os.replace` como red de seguridad). | Guarda `TenantExistsError` en `scaffold.py` | tdd_coder | no_implementada | CA-06 |
| TSK-17 | Test: invocar la fachada `client new SANDUCHERIA` produce en disco la misma estructura que el core y reporta/imprime la ruta creada. | Test "cli-crea-y-reporta" en `test_cli_client_new.py` | tdd_tester | no_implementada | CA-02 |
| TSK-18 | Fachada CLI `zlk client new <NOMBRE>`: parsear subcomando, resolver `clients_root`, invocar `create_client`, imprimir la ruta (sin lógica de negocio propia). | Despacho de la fachada en `cli.py` | tdd_coder | no_implementada | CA-02 |
| TSK-19 | Test: exit codes distintos — `0` en éxito, `2` con `ClientNameError`, `3` con `TenantExistsError`. | Test "cli-exit-codes" en `test_cli_client_new.py` | tdd_tester | no_implementada | CA-02 |
| TSK-20 | Traducción de excepciones de dominio a exit codes (0/2/3) con mensajes claros en `cli.py`. | Manejo de errores/exit codes en `cli.py` | tdd_coder | no_implementada | CA-02 |
| TSK-21 | Test: el conjunto de rutas/contenidos producido por `create_client` (import directo) es idéntico al producido por `zlk client new`. | Test "equivalencia-core-cli" en `test_cli_client_new.py` | tdd_tester | no_implementada | CA-03 |
| TSK-22 | Test: la regla `.gitignore` `clients/*/data/` cubre `clients/<NOMBRE>/data/` (bronze/silver/gold/manifest.json) y NO cubre `client.yaml` ni `input/` (versionables). | Test "gitignore-frontera-pii" en `test_scaffold.py` | tdd_tester | no_implementada | CA-09 |
| TSK-23 | Test: `create_client("COMPANY_DEMO", root)` produce un conjunto de rutas relativas idéntico al de cualquier tenant real creado por la misma vía. | Test "company-demo-canonico" en `test_scaffold.py` | tdd_tester | no_implementada | CA-10 |
| TSK-24 | Crear el tenant de demostración ejecutando `zlk client new COMPANY_DEMO` y versionar `clients/COMPANY_DEMO/client.yaml` + `input/` (`data/` queda gitignored). | Tenant `COMPANY_DEMO` versionado | humano | no_implementada | CA-10 |
| TSK-25 | Prueba de integración end-to-end: ejecutar el comando instalado `zlk client new` por subprocess sobre un `clients_root` temporal; verificar éxito, exit codes y estructura en disco real. | `app/tests/integration/test_client_new_e2e.py` | integration_tester | no_implementada | CA-01, CA-02 |
| TSK-26 | Refactor de `scaffold.py` manteniendo verde: extraer plantillas YAML/manifest a constantes o helpers cohesivos, unificar construcción de rutas, docstrings. | `scaffold.py` refactorizado | tdd_refactor | no_implementada | CA-01 (calidad) |
| TSK-27 | Refactor de `cli.py` manteniendo verde: separar parseo, despacho y traducción de errores en unidades legibles. | `cli.py` refactorizado | tdd_refactor | no_implementada | CA-02 (calidad) |

## Dependencias y Contratos
- **Consume:** esqueleto del motor `app/src/zeroleak/` (paquete `zeroleak`, comando `zlk` vía `[project.scripts]` en `pyproject.toml`); `system_design.md` §11–§12 (estructura canónica del tenant); `constraints.md` C-01 (regla `.gitignore clients/*/data/`, ya vigente); PyYAML (dependencia declarada en `pyproject.toml`).
- **Produce:** función core `create_client`, excepciones de dominio, fachada `zlk client new`, y el tenant `COMPANY_DEMO` versionado (solo `client.yaml` + `input/`).
- **Habilita:** features posteriores (`ingest`, `vault`, `finance`, `report`) que consumirán los tenants y el `manifest.json`.

## Estrategia de Test
- **Unit (`test_scaffold.py`, `test_cli_client_new.py`):** validación de nombre (allow-list, inválidos/válidos), estructura canónica, placeholders YAML parseables, manifest, atomicidad (residuo cero ante nombre inválido y ante fallo de E/S forzado con monkeypatch), no idempotencia (`TenantExistsError` con snapshot), fachada CLI (delegación + reporte de ruta), exit codes 0/2/3, equivalencia core↔CLI, y frontera PII del `.gitignore`.
- **Integración (`test_client_new_e2e.py`, `integration_tester`):** ejecución real del comando `zlk client new` por subprocess sobre un `clients_root` temporal, verificando exit codes y árbol en disco (la costura CLI→core→filesystem completa).
- **Fixtures / datos de prueba:** **sintéticos** (Regla "Datos en Bóveda", C-01). `clients_root` siempre en `tmp_path`; nombres de prueba ficticios (`SANDUCHERIA`, `COMPANY_DEMO`, etc.); ningún dato real ni sensible del cliente.

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Deben coincidir con `stages.tdd.cases[]` del `state.json` de la feature. Cada caso agrupa sus tareas de test y de código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | Nombres inválidos (`""`, `"   "`, `"cliente con espacios"`, `"cli/ente"`, `"cli\\ente"`, `"../escape"`, `"клиент"`, `"cli😀"`, `"x"*65`) lanzan `ClientNameError` sin tocar disco. | TSK-02, TSK-03 | CA-04 |
| 2 | Sobre `clients_root` limpio, `create_client("SANDUCHERIA", root)` retorna `root/"SANDUCHERIA"` y crea la estructura canónica completa (6 artefactos). | TSK-01, TSK-04, TSK-05, TSK-09, TSK-11 | CA-01 |
| 3 | Nombres válidos (`"x"`, `"cliente_01"`, `"COMPANY-DEMO"`, `"Sanducheria_Ñoño"`, `"Café_Málaga"`, `"ÁÉÍÓÚüÑ"`) crean el tenant; `NAME_PATTERN` es exactamente la allow-list de la spec. | TSK-06, TSK-07 | CA-05 |
| 4 | `client.yaml` y los 3 YAMLs de `input/` son parseables por `yaml.safe_load`, con claves vacías + comentario guía; `client.yaml` trae `client_id`, `display_name`, `sector_id`, `created_at`; sin datos reales. | TSK-08, TSK-09 | CA-07 |
| 5 | Existen `data/bronze|silver|gold/` vacíos y `data/manifest.json` == `{"version": 1, "files": []}`. | TSK-10, TSK-11 | CA-08 |
| 6 | Un nombre inválido no deja residuos en `clients_root` (ni tenant parcial ni `.staging`). | TSK-12, TSK-14 | CA-04 |
| 7 | Un fallo de E/S a mitad se propaga y no deja tenant parcial ni carpeta de staging (atomicidad todo-o-nada). | TSK-13, TSK-14 | CA-04 |
| 8 | Un segundo `create_client("T", root)` lanza `TenantExistsError`; el snapshot del tenant existente queda idéntico. | TSK-15, TSK-16 | CA-06 |
| 9 | `zlk client new SANDUCHERIA` produce la misma estructura que el core y reporta la ruta creada (delega en el core). | TSK-17, TSK-18 | CA-02 |
| 10 | Exit codes distintos: `0` éxito, `2` nombre inválido, `3` tenant existente. | TSK-19, TSK-20 | CA-02 |
| 11 | `create_client` (import directo) produce un resultado en disco idéntico al de `zlk client new`. | TSK-21, TSK-18 | CA-03 |
| 12 | La regla `.gitignore clients/*/data/` cubre `clients/<NOMBRE>/data/` y NO `client.yaml` ni `input/` (versionables). | TSK-22 | CA-09 |
| 13 | `create_client("COMPANY_DEMO", root)` produce un conjunto de rutas relativas idéntico al de cualquier tenant real. | TSK-23, TSK-24 | CA-10 |

> **Integración (fuera del bucle rojo-verde de TDD, tras el core y la CLI):** TSK-25 (`integration_tester`) valida el comando instalado end-to-end (CA-01, CA-02). **Refactor:** TSK-26 y TSK-27 se ejecutan en la fase `tdd_refactor` manteniendo verde.

## Verificación de Cobertura (todo CA-xx tiene ≥1 TSK-xx)
| CA | Cubierto por |
|---|---|
| CA-01 | TSK-01, TSK-04, TSK-05, TSK-09, TSK-11, TSK-25, TSK-26 |
| CA-02 | TSK-17, TSK-18, TSK-19, TSK-20, TSK-25, TSK-27 |
| CA-03 | TSK-21, TSK-18 |
| CA-04 | TSK-02, TSK-03, TSK-12, TSK-13, TSK-14 |
| CA-05 | TSK-06, TSK-07 |
| CA-06 | TSK-15, TSK-16 |
| CA-07 | TSK-08, TSK-09 |
| CA-08 | TSK-10, TSK-11 |
| CA-09 | TSK-22 |
| CA-10 | TSK-23, TSK-24 |

## Riesgos Técnicos / Decisiones a Validar en el Gate (paso 9)
- **Staging en el mismo filesystem (crítico).** El directorio de staging debe crearse **dentro de `clients_root`** (`.staging-<uuid>`) para que `os.replace` sea un rename atómico; en distinto filesystem `os.replace` degrada a copia no atómica. Si `clients_root` no es escribible, el alta debe fallar limpio.
- **Windows / `os.replace` sobre directorios.** En Windows, `os.replace(src_dir, dst_dir)` **falla si el destino existe** (a diferencia de POSIX con archivos): esto refuerza la guarda `TenantExistsError`, pero implica que la comprobación previa de existencia sigue siendo necesaria para dar el error de dominio con mensaje claro (evitar un `OSError` crudo).
- **TOCTOU en la comprobación de existencia.** El chequeo "existe" seguido de `os.replace` tiene una ventana de carrera; aceptable para el uso mono-usuario del Científico de Datos (Fase 1), pero se documenta como supuesto.
- **Nombres con acentos/ñ en el filesystem.** Los nombres válidos incluyen `á é í ó ú ü ñ` y mayúsculas acentuadas; se asume filesystem con soporte Unicode (NTFS lo tiene). No se normaliza Unicode (NFC/NFD): el nombre se usa tal cual.
- **Exit codes 0/2/3** quedan fijados por decisión del humano (se reserva `1` para errores inesperados no de dominio, comportamiento por defecto).
- **Placeholder mínimo genérico** (decisión del humano): los tests de CA-07 comprueban presencia de claves marcador vacías + comentario, **no** un esquema completo; el esquema real lo definirán `ingest`/`vault`/`finance`.

---

**Siguiente paso:** gate humano (paso 9) para aprobar/rechazar este plan. **No** se arranca el bucle TDD (paso 10: `tdd_tester → tdd_coder → tdd_refactor`) hasta la aprobación.
