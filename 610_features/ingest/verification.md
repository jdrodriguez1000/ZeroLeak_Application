# Verification — ingest

> Artefacto del paso 12 (`spec_verifier`), escrito en **contexto fresco** e
> **independiente** (P1/P3): el verificador no arregla código ni tests; ejecuta la
> suite él mismo, lee la salida real y contrasta **cada `CA-xx` de `spec.md`**
> contra evidencia concreta. Veredicto binario y conservador: un solo criterio sin
> evidencia verificada basta para NO CONFORME.

## Veredicto: ✅ CONFORME

Los **12 criterios de aceptación** (`CA-01 … CA-12`) de `spec.md` están
**cubiertos** con evidencia verificada (tests identificables en verde ejecutados
por el propio verificador), la suite completa está **verde**, el **alcance**
(in/out scope de `definition.md` y `feature_contract.md`) se respeta y la
restricción **C-01 ("Datos en Bóveda")** se cumple. La feature puede avanzar al
paso 13 (PR) → gate humano (`human_test` + `merge_to_main`).

## Resultado real de la suite (ejecutado por el verificador)

Entorno: `py -3.13` (Python 3.13 requerido; el `python` del PATH es 3.12 y falla).

```
$ py -3.13 -m pytest -q        (desde app/)
69 passed in 8.37s
```

Desglose específico de `ingest` (25 tests, todos PASSED):

- `tests/test_ingest.py` — 17 tests (incluye 6 parametrizados de `.gitignore`).
- `tests/test_cli_ingest.py` — 4 tests (fachada CLI + exit codes 0/1/2).
- `tests/integration/test_ingest_e2e.py` — 5 tests por **subprocess real** del
  comando `zlk` instalado (la costura CLI instalada → proceso → disco realmente
  se ejercitó: los 5 pasaron, lo que confirma que `zlk` está instalado y opera
  end-to-end).

Los 44 tests restantes (hasta 69) son de `client_scaffold`, ya en `main`, sin
regresiones.

## Matriz de trazabilidad `CA-xx → evidencia`

| CA | Estado | Evidencia verificada (test en verde) |
|---|---|---|
| CA-01 | cubierto | `test_ingest_paths_csv_valido_copia_a_bronze_y_agrega_entrada_pending` (asserta `sha256(bronze)==sha256(original)` byte a byte + **una** entrada con ese `sha256` y `status=="pending"`); e2e `test_zlk_ingest_subprocess_csv_valido_copia_a_bronze_y_agrega_entrada_pending`. |
| CA-02 | cubierto | `test_ingest_paths_entrada_manifest_tiene_exactamente_los_4_campos_de_ca02` (set de claves EXACTO `{file,sha256,ingested_at,status}`, asserts **negativos** de `period`/`run_id`/`output`, `sha256` regex 64 hex, `ingested_at` regex ISO segundos + `microsecond==0`/`tzinfo is None`). |
| CA-03 | cubierto | `test_ingest_paths_carpeta_recorrido_plano_ignora_subcarpetas_y_extension_no_permitida` (carpeta con `a.csv`,`b.xlsx`,`c.txt`,`sub/d.csv` → exactamente 2 entradas; `c.txt`/`sub/`/`sub/d.csv` ausentes de bronze, manifest y `failed`). |
| CA-04 | cubierto | `test_ingest_paths_argumentos_mezclados_archivo_y_carpeta_ingiere_union` (asserts reales de unión: 3 en bronze, 3 en manifest, `failed==[]`; test de caracterización pero con aserciones sustantivas, no vacías). |
| CA-05 | cubierto | `test_ingest_paths_dedupe_sha256_reenviar_archivo_ya_ingerido_es_no_op_skip` + `..._dentro_de_la_misma_invocacion_segunda_ruta_es_duplicate` (SKIP, sin copia ni entrada, `exit_code==0`); e2e `test_zlk_ingest_subprocess_dedupe_reenvio_es_no_op_exit_0`. |
| CA-06 | cubierto | `test_ingest_paths_colision_de_nombre_con_contenido_distinto_usa_sufijo_sha8` (original **no** sobrescrito; nuevo como `ventas__<sha8>.csv` con `<sha8>` de `sha256(nuevo)`; `file` con sufijo; nueva entrada). |
| CA-07 | cubierto | `test_ingest_paths_mezcla_valida_vacia_extension_no_permitida_e_inexistente` (solo la válida ingerida; 3 fallos con motivos exactos `"archivo vacío"`/`"extensión fuera de allow-list"`/`"la ruta no existe"`; `exit_code==1`); e2e `..._mezcla_valida_invalida_exit_code_1_procesamiento_parcial`. |
| CA-08 | cubierto | `test_ingest_paths_tenant_inexistente_lanza_tenant_not_found_error_sin_tocar_disco` (`TenantNotFoundError`, `clients_root` intacto antes/después); `test_cli_ingest_exit_code_2_en_tenant_inexistente` (fachada → 2, sin residuo); e2e `..._tenant_inexistente_exit_code_2_sin_residuo`. |
| CA-09 | cubierto | `test_ingest_paths_archivo_vacio_se_reporta_como_fallo_y_no_se_ingiere` (0 bytes → `failed` motivo `"archivo vacío"`, bronze vacío, manifest sin entrada, `exit_code==1`). |
| CA-10 | cubierto | `test_ingest_paths_csv_con_distintos_delimitadores_se_ingieren_los_3_sin_parseo` (3 `.csv` con `,`/`;`/`|` → 3 `sha256` **distintos**, 3 entradas, copia byte a byte; el test no importa el módulo `csv`). Reforzado por lectura de `core.py`: solo `read_bytes()`/`hashlib.sha256`/`shutil.copyfile`, sin parseo. |
| CA-11 | cubierto | `test_gitignore_cubre_bronze_y_manifest_producidos_por_ingest` (4 params: `data/`, `bronze/ventas.csv`, `bronze/ventas__<sha8>.csv`, `manifest.json`) + `test_gitignore_no_cubre_client_yaml_ni_input_para_ingest` (2 params). Verificado además sobre el repo real: `git check-ignore` marca `clients/*/data/` (línea 34) y `git status --ignored` confirma `clients/MI_BUNUELO/data/` como ignorado (`!!`). |
| CA-12 | cubierto | `test_ingest_paths_es_observable_sin_cli` (core observable sin CLI) + `test_cli_ingest_mismo_efecto_en_disco_que_core_y_exit_code_0` (equivalencia core↔CLI sobre raíces gemelas); e2e `..._arbol_y_manifest_identicos_al_core_import_directo`. |

**Resumen:** 12/12 `cubierto`, 0 `parcial`, 0 `no cubierto`.

## Auditoría de alcance (definition.md / feature_contract.md)

**In scope — hecho y verificado:**
- Core `ingest_paths(client, paths, clients_root) -> IngestResult` con copia
  inmutable + `sha256` + entrada `pending` (CA-01/CA-02).
- Entrada = archivo o carpeta con recorrido **plano** filtrado por allow-list
  (CA-03); multi-argumento (CA-04).
- Dedupe por `sha256` (CA-05); nombrado `__<sha8>` ante colisión de nombre (CA-06).
- Validación básica agnóstica: tenant existe (CA-08), archivo existe/no vacío
  (CA-07/CA-09), extensión en allow-list case-insensitive (CA-07).
- Fachada CLI delgada `zlk ingest` que solo invoca el core (CA-12).

**Out of scope — respetado (verificado en `core.py`):**
- **No parsea** contenido: solo `read_bytes()` + `hashlib.sha256` +
  `shutil.copyfile`; ningún `csv`/`open(newline=)`/pandas/openpyxl.
- **No** llena `period`/`run_id`/`output` (asserts negativos en CA-02).
- **No** recursión: usa `iterdir()` sobre el primer nivel, no `rglob`/glob.
- **No** empareja archivo→contrato (D-18, sigue abierto).
- **No** da de alta el tenant (precondición, `TenantNotFoundError`).

## Cumplimiento de restricciones

- **C-01 "Datos en Bóveda" (inviolable):** ✅ Cumplida. Todos los tests usan
  `tmp_path` y datos **sintéticos** (`SANDUCHERIA`, contenidos ficticios); los
  tests de `.gitignore` usan rutas ficticias sin crear tenants reales. En el repo
  real, `clients/*/data/` (bronze + manifest) queda ignorado por `.gitignore`
  (verificado con `git check-ignore` y `git status --ignored`): ningún artefacto
  ingerido es trackeable.
- **C-03 "Merge solo vía PR humano":** aplica en el paso 13; no se hace merge aquí.
- **Cambios quirúrgicos:** la integración (paso 11) añadió únicamente
  `app/tests/integration/test_ingest_e2e.py`, sin tocar producción
  (`app/src/zeroleak/...`), coherente con el registro de `state.json`.

## Hallazgos / huecos

Ninguno. No se detectaron tests sin aserciones sustantivas, cobertura aparente ni
criterios sin evidencia. Los tests marcados como "caracterización" en el bucle TDD
(CA-02, CA-04, CA-10, CA-11) contienen aserciones reales y sustantivas que ejercen
el comportamiento del `CA-xx` correspondiente, por lo que cuentan como evidencia
válida.

## Recomendación

**CONFORME** → la sesión principal puede proceder al **paso 13 (abrir PR)**, que
queda sujeto al **gate humano** (`human_test` + `merge_to_main`, C-03). No se
recomienda ninguna etapa de retorno (`spec_writer` / `plan_builder` / bucle TDD /
`integration_tester`).
