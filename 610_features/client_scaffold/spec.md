# Spec — client_scaffold

> Artefacto del paso 6 (`spec_writer`), escrito **después** de aprobar el notebook (spike). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate, paso 7) antes de planear.

## Resumen
Dar de alta un cliente nuevo materializando en disco un **tenant** aislado (`clients/<NOMBRE>/`) con su estructura canónica (`client.yaml`, `input/` con 3 YAMLs, `data/{bronze,silver,gold}`, `manifest.json`) mediante la función core `create_client(name, clients_root) -> Path`, expuesta por la fachada CLI `zlk client new <NOMBRE>`, con validación estricta del nombre, comportamiento no idempotente y atomicidad todo-o-nada.

## Contratos de Datos / Artefactos

### Entradas
| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `name` | `str` | Nombre del cliente. Debe cumplir la regla de validación (ver §Comportamiento). |
| requiere | `clients_root` | `Path` / `str` | Directorio raíz de tenants (configurable, no hardcodeado). Debe existir y ser un directorio escribible. |
| requiere | `.gitignore` (repo) | texto | Debe contener la regla `clients/*/data/` vigente (C-01). |

### Salidas / artefactos producidos (bajo `clients_root/<name>/`)
| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| produce | `<Path>` retornado | `pathlib.Path` | Ruta absoluta o relativa al tenant creado: `clients_root / name`. |
| produce | `client.yaml` | YAML | Claves presentes con valores **vacíos** + comentarios guía: `client_id`, `display_name`, `sector_id`, `created_at`. Versionable. |
| produce | `input/contrato_datos.yaml` | YAML | Claves presentes con valores vacíos + comentarios guía (Contrato de Datos, YAML 1). Versionable. |
| produce | `input/reglas_negocio.yaml` | YAML | Claves presentes con valores vacíos + comentarios guía (Reglas de Negocio, YAML 2). Versionable. |
| produce | `input/finanzas.yaml` | YAML | Claves presentes con valores vacíos + comentarios guía (Variables Financieras, YAML 3). Versionable. |
| produce | `data/bronze/` | directorio | Vacío. Cubierto por `.gitignore` (C-01). |
| produce | `data/silver/` | directorio | Vacío. Cubierto por `.gitignore` (C-01). |
| produce | `data/gold/` | directorio | Vacío. Cubierto por `.gitignore` (C-01). |
| produce | `data/manifest.json` | JSON | Ledger inicial vacío y válido: `{"version": 1, "files": []}`. Cubierto por `.gitignore` (C-01). |

> **Datos en Bóveda (C-01):** todos los placeholders se generan con estructura y comentarios guía **sin datos reales ni sensibles**. La carpeta `data/` del tenant queda cubierta por `.gitignore clients/*/data/`; solo `client.yaml` e `input/` son versionables.

## Comportamiento Esperado

1. **Validación estricta del nombre.** `create_client` valida `name` **antes** de tocar el disco. El nombre es válido si y solo si cumple el patrón exacto:

   ```
   ^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$
   ```

   Es decir, el nombre debe componerse **exclusivamente** de caracteres del alfabeto permitido, con longitud entre **1 y 64** caracteres:
   - Letras ASCII: `A-Z`, `a-z`
   - Dígitos: `0-9`
   - Guion (`-`) y guion bajo (`_`)
   - Letras acentuadas del español: `á é í ó ú ü Á É Í Ó Ú Ü`
   - Eñe: `ñ Ñ`

   **Justificación de que las protecciones se conservan** (decisión del gate): el patrón usa una **lista explícita** de caracteres permitidos (allow-list), **no** `\w` con bandera Unicode amplia; por tanto, todo carácter fuera de esa lista es rechazado por construcción. Quedan bloqueados:
   - **Nombre vacío** o solo espacios: `{1,64}` exige ≥ 1 carácter y el espacio no pertenece al alfabeto → rechazado.
   - **Espacios** (incluye tabs y otros blancos): no están en la lista → rechazados.
   - **Separadores de ruta** `/` y `\`: no están en la lista → rechazados (imposible salir del directorio del tenant ni anidar rutas).
   - **Path traversal** `..`: el punto `.` no está en la lista → cualquier `..` o `.` es rechazado.
   - **Caracteres de control** (`\n`, `\t`, `\0`, etc.): no están en la lista → rechazados.
   - **Scripts no latinos** (cirílico, CJK, emojis, etc.) y cualquier otro carácter Unicode fuera del alfabeto: rechazados (no se usa `\w` Unicode amplio).

   Un nombre inválido lanza la excepción de dominio `ClientNameError` con mensaje claro; **no se crea ningún artefacto en disco**.

2. **No idempotencia (sin `--force`).** Si `clients_root / name` ya existe, `create_client` lanza `TenantExistsError` con mensaje claro y **no modifica** el tenant existente (ningún archivo se altera, agrega o elimina). No hay sobrescritura ni fusión.

3. **Atomicidad todo-o-nada.** La creación es transaccional: ante cualquier fallo (nombre inválido detectado tarde, error de E/S a mitad, etc.), el resultado observable es que **no queda ningún tenant a medias** ni carpeta residual (p. ej. `.staging`) en `clients_root`. Solo un alta que completa la estructura canónica íntegra deja artefactos; cualquier otra ejecución deja `clients_root` sin residuos nuevos.

4. **Estructura canónica creada.** En un alta exitosa se materializan, bajo `clients_root/<name>/`: `client.yaml`; `input/` con `contrato_datos.yaml`, `reglas_negocio.yaml`, `finanzas.yaml`; `data/bronze/`, `data/silver/`, `data/gold/` (vacías); y `data/manifest.json` con `{"version": 1, "files": []}`. La función retorna la `Path` del tenant.

5. **Placeholders YAML (decisión del gate).** `client.yaml` y los 3 YAMLs de `input/` se generan con **las claves presentes pero con valores vacíos**, acompañadas de **comentarios guía** (líneas `#` que orientan al humano que completará la config). Deben ser **sintácticamente válidos** (parseables por `yaml.safe_load` de PyYAML sin excepción) y **nunca** contener datos reales o sensibles.

6. **CLI como fachada.** `zlk client new <NOMBRE>` no contiene lógica propia: parsea el argumento, invoca `create_client(name, clients_root)`, reporta la ruta creada en caso de éxito y traduce las excepciones de dominio a **mensajes claros** y **exit codes distintos**. El resultado en disco de invocar la CLI es idéntico al de invocar el core directamente.

7. **Tenant de demostración.** El tenant `COMPANY_DEMO` se crea por esta **misma vía** (`create_client` / `zlk client new`) y obtiene la estructura canónica idéntica a cualquier tenant real.

## Casos Límite y Errores

| Entrada / situación | Resultado esperado |
|---|---|
| `name = ""` (vacío) | `ClientNameError`; sin artefactos en disco. |
| `name = "   "` (solo espacios) | `ClientNameError`; sin artefactos. |
| `name = "cliente con espacios"` | `ClientNameError` (espacio no permitido); sin artefactos. |
| `name = "cli/ente"` o `"cli\\ente"` | `ClientNameError` (separador de ruta); sin artefactos. |
| `name = "../escape"` | `ClientNameError` (path traversal, `.` no permitido); sin artefactos. |
| `name = "клиент"` / `"顧客"` / `"cli😀"` | `ClientNameError` (script no latino / emoji fuera de la allow-list); sin artefactos. |
| `name = "x" * 65` (65 chars) | `ClientNameError` (excede 64); sin artefactos. |
| `name = "Sanducheria_Ñoño"` o `"Café_Málaga"` | **Válido** (acentos y ñ permitidos): crea el tenant. |
| `name = "x"` (1 char), `name = "COMPANY-DEMO"`, `name = "cliente_01"` | **Válido**: crea el tenant. |
| `name` de tenant ya existente | `TenantExistsError`; el tenant existente queda intacto. |
| Fallo de E/S a mitad de la creación | Se propaga el error; no queda tenant parcial ni carpeta de staging. |

## Interfaces / Firmas Públicas

- `create_client(name: str, clients_root: Path) -> Path` — motor; crea el tenant y retorna su ruta.
- `class ClientNameError(Exception)` — excepción de dominio para nombre inválido.
- `class TenantExistsError(Exception)` — excepción de dominio para tenant ya existente.
- CLI: `zlk client new <NOMBRE>` — fachada; delega en `create_client`. Exit codes:
  - `0` — éxito (tenant creado; reporta la ruta).
  - código distinto para nombre inválido (`ClientNameError`).
  - código distinto para tenant existente (`TenantExistsError`).

  > Los tres exit codes deben ser **distintos entre sí** (éxito ≠ nombre inválido ≠ tenant existente). Los valores numéricos concretos se fijan en el plan (paso 8); el spike propuso `0 / 2 / 3`.

## Criterios de Aceptación (verificables)

> Cada criterio lleva un **código `CA-xx`** (único en la feature) y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Sobre un `clients_root` limpio, `create_client("SANDUCHERIA", root)` retorna una `Path` igual a `root/"SANDUCHERIA"` y, tras la llamada, existen: `client.yaml`, `input/contrato_datos.yaml`, `input/reglas_negocio.yaml`, `input/finanzas.yaml`, `data/bronze/`, `data/silver/`, `data/gold/` y `data/manifest.json`. | HU-01 |
| CA-02 | `zlk client new SANDUCHERIA` (fachada) produce en disco exactamente la misma estructura que invocar `create_client` directamente, y reporta/imprime la ruta del tenant creado; la CLI no ejecuta lógica de negocio propia (delega en el core). | HU-01, HU-02 |
| CA-03 | `create_client` es invocable sin la CLI (import directo) y produce el tenant completo; el resultado en disco es idéntico al obtenido vía `zlk client new`. | HU-02 |
| CA-04 | Para cada nombre inválido del conjunto `{"", "   ", "cliente con espacios", "cli/ente", "cli\\ente", "../escape", "клиент", "cli😀", "x"*65}`, `create_client` lanza `ClientNameError` y `clients_root` no gana ningún artefacto nuevo (sin tenant parcial ni carpeta `.staging`). | HU-03 |
| CA-05 | Para cada nombre válido del conjunto `{"x", "cliente_01", "COMPANY-DEMO", "Sanducheria_Ñoño", "Café_Málaga", "ÁÉÍÓÚüÑ"}` el nombre pasa la validación (crea el tenant); y el patrón usado es exactamente `^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$` (allow-list explícita, sin `\w` Unicode amplio). | HU-03 |
| CA-06 | Tras crear el tenant `T`, un segundo `create_client("T", root)` lanza `TenantExistsError` con mensaje claro y el snapshot (rutas + tamaños de archivo) del tenant existente es idéntico antes y después del reintento (no se modifica ni pierde nada). | HU-04 |
| CA-07 | `client.yaml` y los 3 YAMLs de `input/` son parseables por `yaml.safe_load` sin excepción; cada uno contiene las claves esperadas con **valores vacíos** y al menos un **comentario guía** (`#`), y ninguno contiene datos reales/sensibles. En particular `client.yaml` incluye las claves `client_id`, `display_name`, `sector_id`, `created_at`. | HU-05 |
| CA-08 | Tras el alta existen los directorios `data/bronze/`, `data/silver/`, `data/gold/` (vacíos) y `data/manifest.json` parsea como JSON válido igual a `{"version": 1, "files": []}`. | HU-06 |
| CA-09 | La ruta `clients/<NOMBRE>/data/` (y todo lo que contiene: `bronze/`, `silver/`, `gold/`, `manifest.json`) casa con la regla `.gitignore` `clients/*/data/` vigente en el repo, mientras que `clients/<NOMBRE>/client.yaml` y `clients/<NOMBRE>/input/...` NO casan (permanecen versionables). | HU-07 |
| CA-10 | `create_client("COMPANY_DEMO", root)` crea el tenant `COMPANY_DEMO` cuyo conjunto de rutas relativas (estructura canónica) es idéntico al de cualquier tenant real creado por la misma vía. | HU-08 |

### Trazabilidad HU → Spec (cobertura)

> Toda `HU-xx` de `definition.md` debe estar cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02 |
| HU-02 | CA-02, CA-03 |
| HU-03 | CA-04, CA-05 |
| HU-04 | CA-06 |
| HU-05 | CA-07 |
| HU-06 | CA-08 |
| HU-07 | CA-09 |
| HU-08 | CA-10 |

## No-Objetivos
- Ingesta de archivos reales a `bronze/` (feature `ingest`).
- Binarización Drop & Detach bronze → silver (feature `vault`).
- Cálculo de métricas, DHS, Pareto o CSVs masticados en `gold/` (features `finance`/`report`).
- Contenido "real" de los YAMLs de `input/` más allá de placeholders válidos (claves vacías + comentarios guía).
- Idempotencia / actualización de un tenant existente y bandera `--force`.
- Registro central de clientes en base de datos: la identidad hoy es tenant + `client.yaml` (§12).
- Algoritmo interno de atomicidad (staging + rename, o cualquier otro): es decisión del bucle TDD; la spec solo fija el **contrato observable** de "todo o nada".
