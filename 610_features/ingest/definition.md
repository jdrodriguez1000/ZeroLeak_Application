# Definition — ingest

> Artefacto del paso 3 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `ingest` (snake_case)
- **Módulo / componente:** capa de **datos** del motor (`src/zeroleak/ingest/`) — puerta de entrada al pipeline
  medallion del tenant. Registra archivos crudos del cliente en la capa **bronze** y actualiza el manifiesto de
  procesamiento (`manifest.json`), sin tocar `silver`/`gold` ni el resto de módulos (`vault`, `modules`,
  `finance`, `report`).

## Problema / Necesidad
Hoy un tenant recién creado (`client_scaffold`) tiene estructura pero **ningún dato**: no existe una forma
notarial y confiable de recibir los archivos que el cliente entrega (típicamente CSV/XLSX con transacciones,
catálogos, etc.) y dejar constancia fiel de qué llegó, con qué huella de contenido y en qué estado de
procesamiento. Sin esto, no hay nada en bronze que las etapas posteriores (`load_data`, `validate`, `vault`)
puedan consumir, y no hay evidencia auditable de "qué se recibió y cuándo" — algo crítico quincena a quincena
en el Modo Incremental.

## Alcance
**In scope:**
- Core (`ingest_paths(client, paths, clients_root) -> ...`) que, por cada ruta recibida:
  - Si es archivo: lo ingiere si su extensión está en la allow-list (`.csv`, `.xlsx`).
  - Si es carpeta: recorrido **plano** (solo primer nivel, sin recursión) ingiriendo los archivos con
    extensión en la allow-list e ignorando el resto en silencio.
  - Acepta **varios argumentos** de ruta en una misma invocación.
- Por archivo ingerido: copia inmutable de bytes a `clients/<CLIENTE>/data/bronze/`, cálculo de `sha256`,
  y registro de entrada en `manifest.json` con `status: "pending"` (formato §11 de `system_design.md`).
- **Dedupe por `sha256`** (idempotencia por contenido): reenviar un archivo con contenido ya registrado no
  duplica copia ni entrada; un archivo con mismo nombre pero contenido distinto sí se registra.
- Validación básica agnóstica de formato: tenant destino existe, archivo existe y no está vacío, extensión
  en la allow-list `.csv`/`.xlsx`.
- Fachada CLI `zlk ingest <CLIENTE> <ruta>...`, delgada, que solo invoca el core.
- Respeto de la frontera C-01: los archivos ingeridos y el manifiesto viven bajo `clients/<CLIENTE>/data/`,
  cubierto por `.gitignore`.

**Out of scope:**
- Parsear o interpretar el contenido del archivo (delimitador, columnas, tipos, encoding) — eso es
  `load_data`/`validate`, una etapa posterior.
- Llenar metadatos de manifiesto que dependen de procesamiento (`period`, `run_id`, `output`).
- Emparejar el archivo físico con su tipo de contrato de datos (`contract_data.yaml`) — punto abierto D-18,
  se resuelve en `load_config`.
- Binarización Drop & Detach bronze → silver (feature `vault`).
- Cálculo de métricas o capa gold (features `finance`/`report`).
- Extensiones fuera de la allow-list (p. ej. `.txt`), recorrido recursivo de subcarpetas, expansión de
  comodines/glob (D-17).
- Dar de alta el tenant (responsabilidad de `client new` / `client_scaffold`, ya construido).

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como consultor de datos (DS), quiero ingerir un archivo individual (`.csv`/`.xlsx`) de un cliente con un solo comando, para dejar evidencia notarial de que llegó sin tener que manipular la estructura del tenant a mano. | `zlk ingest <CLIENTE> <archivo>` copia el archivo intacto a `data/bronze/` y crea una entrada en `manifest.json` con `sha256` correcto y `status: "pending"`. |
| HU-02 | Como DS, quiero ingerir todos los archivos válidos de una carpeta de entrega del cliente en una sola invocación, para no tener que listar archivo por archivo cuando el cliente entrega varios a la vez. | Al pasar una carpeta, se ingieren (recorrido plano, primer nivel) los `.csv`/`.xlsx` que contiene y se ignoran silenciosamente los demás archivos y las subcarpetas. |
| HU-03 | Como DS, quiero poder mezclar archivos y carpetas como argumentos de una misma invocación, para cubrir entregas heterogéneas del cliente en un solo comando. | `zlk ingest <CLIENTE> <ruta1> <ruta2> ...` procesa correctamente cualquier combinación de archivos y carpetas pasados como argumentos. |
| HU-04 | Como DS, quiero que reenviar un archivo con contenido idéntico a uno ya ingerido no genere duplicados, para poder re-ejecutar `ingest` de forma segura (p. ej. en el Modo Incremental) sin ensuciar bronze ni el manifiesto. | Reenviar un archivo con contenido igual a uno ya registrado no crea copia ni entrada nueva (dedupe por `sha256`); un archivo con mismo nombre pero contenido distinto sí se registra como nueva entrada. |
| HU-05 | Como DS, quiero recibir un error claro cuando el tenant no existe, el archivo no existe/está vacío o su extensión no está permitida, para corregir el problema de inmediato sin dejar el ledger o bronze en un estado inconsistente. | El tenant inexistente aborta toda la invocación (precondición global). Para errores por ruta (archivo no existe/vacío, extensión no permitida) el procesamiento es **parcial**: las rutas válidas se ingieren y las inválidas se omiten, sin copiar sus bytes a bronze ni corromper `manifest.json`. Al final se informa qué rutas salieron bien y cuáles fallaron, cada una con su motivo. |
| HU-06 | Como responsable de cumplimiento del producto, quiero que `ingest` nunca interprete el contenido del archivo del cliente, para mantener la separación entre "archivador notarial" (bronze) y las etapas de parseo/validación, evitando acoplarse a un formato o delimitador específico. | Archivos `.csv` con delimitador `,`, `;` o `|` se ingieren exactamente igual (mismos bytes copiados, mismo cálculo de `sha256`), sin que `ingest` intente leer ni interpretar su estructura interna. |
| HU-07 | Como responsable de cumplimiento del producto, quiero que los datos ingeridos (con PII real) queden fuera del control de versiones y del indexador, para que la Bóveda de Datos (C-01) se cumpla automáticamente por diseño en cada ingesta. | Tras ingerir, `clients/<CLIENTE>/data/bronze/` y `manifest.json` quedan bajo la regla `.gitignore` `clients/*/data/`; ningún archivo ingerido aparece en `git status` como trackeable. |
| HU-08 | Como desarrollador del motor, quiero que la lógica de ingesta viva en una función core reutilizable (no en la CLI), para poder invocarla desde otros puntos del sistema (tests, futura API/SaaS) sin depender de la interfaz de línea de comandos. | Existe una función core (p. ej. `ingest_paths(client, paths, clients_root) -> ...`) que implementa el comportamiento completo de ingesta; la CLI `zlk ingest` es una fachada delgada que solo la invoca y traduce su resultado/errores. |

## Dependencias
- Feature `client_scaffold` (T-21, ya en `main`): el tenant destino y su estructura (`data/bronze/`,
  `manifest.json` inicial) deben existir antes de ingerir.
- `700_architecture/system_design.md` §10 (Modo Incremental) y §11 (capas medallion + esquema de
  `manifest.json`).
- `900_persistence/constraints.md` C-01 (Datos en Bóveda) — regla `.gitignore` `clients/*/data/`.
- `900_persistence/decisions.md` D-17 (alcance de `ingest`) y D-18 (emparejamiento archivo→contrato,
  abierto — no cubierto por ninguna historia de esta feature).

## Riesgos y Supuestos
- **Supuesto:** el contrato ya resuelve la ambigüedad de qué pasa con extensiones fuera de la allow-list
  dentro de una carpeta (se ignoran en silencio, no error) — HU-02 se define bajo ese supuesto.
- **Supuesto:** "archivo existe y no está vacío" se interpreta como validación de tamaño de bytes > 0, no
  como validación de contenido/estructura (coherente con el principio "no parsear" del contrato).
- **Decisión (zanjada por el humano):** en una invocación multi-argumento, el procesamiento es **parcial por
  ruta**: cada ruta se valida/procesa de forma independiente, las rutas válidas se ingieren y las inválidas se
  omiten (sin corromper lo ya válido). Al terminar, el comando **informa qué rutas salieron bien y cuáles
  fallaron, cada una con su motivo**. Excepción: la validación de que el **tenant existe** es una precondición
  global — si el tenant no existe, la invocación aborta por completo antes de procesar rutas. `spec_writer`
  debe precisar en sus `CA-xx` el formato del reporte y el código de salida (p. ej. éxito total vs. éxito
  parcial vs. fallo global).
- **Vacío heredado del contrato (ya señalado como abierto, D-18):** el emparejamiento archivo físico → tipo de
  contrato de datos queda explícitamente fuera; ninguna historia de esta definición lo cubre, para no
  contradecir el contrato.
- **Dato sintético:** cualquier ejemplo usado en la spec/notebook posteriores debe emplear archivos CSV/XLSX
  sintéticos, nunca datos reales de cliente, en línea con C-01.
