# Verification — client_scaffold

> Artefacto del paso 12 (`spec_verifier`). Auditoría crítica final antes del PR,
> ejecutada en **contexto fresco** e **independiente** del bucle TDD (P1/P3): el
> verificador **no arregla** código ni tests; **ejecuta la suite él mismo**,
> **lee la salida real** y exige **evidencia concreta** por cada `CA-xx`. Un solo
> criterio sin evidencia verificada basta para NO CONFORME.

- **Fecha:** 2026-07-13
- **Feature:** `client_scaffold` (rama `feature/client_scaffold`)
- **Base de verificación:** `spec.md` (CA-01…CA-10, aprobada gate paso 7),
  `definition.md` (HU-01…HU-08), `plan.md` (TSK-01…TSK-27), `state.json`,
  `constraints.md` (C-01).

---

## Veredicto

# ✅ CONFORME

Los 10 criterios de aceptación (CA-01…CA-10) están **cubiertos con evidencia
verificada** (tests identificables en verde ejecutados por el verificador y/o
comportamiento observado del repo). La suite completa está **verde**. No se
detectaron violaciones de alcance (in/out of scope) ni de restricciones
(C-01 "Datos en Bóveda"). El feature puede avanzar al paso 13 (PR) → gate humano
(`human_test` + `merge_to_main`).

---

## Resultado real de la suite (evidencia ejecutada, no reportada)

Comando ejecutado por el verificador en contexto fresco:

```
.venv/Scripts/python.exe -m pytest app/tests -v
```

Salida real capturada:

```
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\USUARIO\Documents\TripleS\ZeroLeak_Application
configfile: pyproject.toml
collected 43 items
...
============================= 43 passed in 2.80s ==============================
```

- **43 passed, 0 failed, 0 skipped, 0 xfailed** — verde total.
- Ejecutado con **Python 3.13.7** vía `.venv/Scripts/python.exe` (L-09: el
  `python` del PATH es 3.12 y falla con `requires-python >=3.13`). Requisito
  cumplido: la suite corrió con el intérprete correcto.
- Desglose: 4 tests de integración (`app/tests/integration/test_client_new_e2e.py`),
  3 tests de fachada CLI (`test_cli_client_new.py`), 36 tests unitarios del core
  (`test_scaffold.py`, incluyendo casos parametrizados).

### Auditoría de calidad de los tests (escepticismo por defecto)

Se revisó el cuerpo de cada test para descartar "verdes convenientes" (tests que
no asertan, que pasan por estar mal escritos, o que no ejercen el camino real):

- Los tests **asertan condiciones sustantivas** (retorno de `Path`, existencia de
  los 6 artefactos, contenido byte-a-byte, `yaml.safe_load` sin excepción,
  `manifest == {"version":1,"files":[]}`, exit codes exactos, snapshots idénticos
  antes/después).
- CA-04/CA-06 se ejercen con `pytest.raises` sobre la **excepción de dominio
  concreta** (`ClientNameError` / `TenantExistsError`), no una excepción genérica.
- La atomicidad (CA-04) se ejerce con `monkeypatch` de `Path.write_text` que
  fuerza el fallo **después** de crear el staging: ejercita de verdad el
  `except: shutil.rmtree`.
- CA-05 congela el patrón con `assert NAME_PATTERN == FROZEN_NAME_PATTERN`
  (allow-list literal, detecta cualquier deriva a `\w`).
- CA-09 verifica el **comportamiento real de Git** (`git check-ignore -v`), no una
  reimplementación del patrón.
- La integración (TSK-25) ejecuta el binario `zlk` **instalado** por subprocess
  real, cerrando la costura CLI→proceso→disco.

No se hallaron tests vacíos, tautológicos ni con asertos ausentes.

---

## Matriz de trazabilidad `CA-xx → HU-xx → evidencia (test)`

| CA | HU | Evidencia (test verde ejecutado) | Estado |
|---|---|---|---|
| CA-01 | HU-01 | `test_scaffold.py::test_create_client_sobre_clients_root_limpio_crea_estructura_canonica_completa` (retorno `root/"SANDUCHERIA"` + 6 artefactos) · integración `..._exito_crea_estructura_canonica_completa` | **cubierto** |
| CA-02 | HU-01, HU-02 | `test_cli_client_new.py::test_cli_client_new_crea_estructura_y_reporta_ruta` · `..._exit_codes_distintos` (0/2/3) · integración `..._exito...`, `..._nombre_invalido_exit_code_2...`, `..._tenant_existente_exit_code_3...` | **cubierto** |
| CA-03 | HU-02 | `test_cli_client_new.py::test_create_client_import_directo_y_cli_producen_arbol_identico` (rutas + bytes idénticos) · integración `..._arbol_identico_al_core_import_directo` | **cubierto** |
| CA-04 | HU-03 | `test_scaffold.py::test_create_client_nombre_invalido_lanza_client_name_error_sin_tocar_disco[9 nombres]` · `..._no_deja_residuo_en_clients_root` · `..._fallo_io_a_mitad_no_deja_residuo` | **cubierto** |
| CA-05 | HU-03 | `test_scaffold.py::test_create_client_nombre_valido_crea_el_tenant[6 nombres]` · `test_name_pattern_es_exactamente_la_allow_list_congelada_por_la_spec` | **cubierto** |
| CA-06 | HU-04 | `test_scaffold.py::test_create_client_tenant_existente_lanza_tenant_exists_error_y_no_lo_modifica` (snapshot idéntico) · integración `..._tenant_existente_exit_code_3_no_modifica` | **cubierto** |
| CA-07 | HU-05 | `test_scaffold.py::test_placeholder_yaml_es_parseable_con_claves_vacias_y_comentario_guia[4 archivos]` · `test_client_yaml_incluye_las_4_claves_de_identidad_vacias` | **cubierto** |
| CA-08 | HU-06 | `test_scaffold.py::test_medallion_dir_existe_y_esta_vacio[bronze/silver/gold]` · `test_manifest_json_es_el_ledger_inicial_vacio` | **cubierto** |
| CA-09 | HU-07 | `test_scaffold.py::test_gitignore_cubre_data_del_tenant[3]` · `test_gitignore_no_cubre_client_yaml_ni_input[2]` (via `git check-ignore`) + verificación directa del repo (ver C-01) | **cubierto** |
| CA-10 | HU-08 | `test_scaffold.py::test_create_client_company_demo_produce_andamiaje_identico_a_tenant_real` + tenant real `clients/COMPANY_DEMO/` versionado (TSK-24) | **cubierto** |

**Cobertura HU (toda HU cubierta por ≥1 CA cubierto):** HU-01…HU-08 todas
satisfechas. Sin huecos.

---

## Cumplimiento de la restricción C-01 ("Datos en Bóveda", INVIOLABLE)

Verificado directamente sobre el repo (no reportado):

- **Regla vigente en `.gitignore`:** línea 34 `clients/*/data/`.
- **`git check-ignore -v clients/COMPANY_DEMO/data/manifest.json`** →
  `.gitignore:34:clients/*/data/` (ignorado ✅).
- **`git check-ignore -v clients/COMPANY_DEMO/client.yaml`** → sin match, `rc=1`
  (versionable ✅).
- **`git ls-files clients/COMPANY_DEMO/`** → solo `client.yaml` + 3 YAMLs de
  `input/` trackeados. **`git ls-files clients/COMPANY_DEMO/data/`** → vacío: la
  carpeta `data/` del tenant real **no** está bajo control de versiones.
- **Datos sintéticos:** todas las fixtures viven en `tmp_path`; nombres de prueba
  ficticios (`SANDUCHERIA`, `COMPANY_DEMO`, `SANDUCHERIA_E2E`, `TENANT_E2E_*`,
  `DEMO_X`). Los placeholders YAML se generan con claves vacías + comentario guía,
  sin datos reales/sensibles (verificado por CA-07). El test de CA-09 usa rutas
  ficticias que **no** se materializan en disco (`git check-ignore` no requiere
  que el archivo exista), por lo que no ensucia `clients/` real.

**C-01: CUMPLIDA.**

---

## Auditoría de alcance (definition.md / feature_contract.md)

- **In scope — hecho:** core `create_client(name, clients_root) -> Path`; fachada
  `zlk client new`; validación estricta del nombre (allow-list congelada);
  placeholders versionables (`client.yaml` + 3 YAMLs `input/`); medallion
  `data/{bronze,silver,gold}` + `manifest.json`; no idempotencia sin `--force`;
  tenant `COMPANY_DEMO` por la vía oficial; C-01 satisfecha. **Todo presente.**
- **Out of scope — respetado:** no hay ingesta a `bronze/`, ni binarización
  bronze→silver, ni métricas/DHS/Pareto en `gold/`, ni esquema "real" de los
  YAMLs (solo placeholders), ni `--force`/idempotencia, ni registro central en
  BD. El código de `scaffold.py`/`cli.py` no incorpora ninguna de estas
  responsabilidades. **Sin desbordamiento de alcance.**

## Auditoría de cambios quirúrgicos

- Archivos de producción tocados: `app/src/zeroleak/core/scaffold.py` (nuevo, 119
  líneas cohesivas) y `app/src/zeroleak/cli.py` (fachada, 69 líneas, sin lógica de
  negocio). Cambios acotados al alcance del plan; `.gitignore` no requirió
  modificación (regla ya vigente). Sin cambios colaterales.

---

## Hallazgos / huecos

- **Ninguno bloqueante.** No hay `CA-xx` parcial ni no cubierto.
- **Observación no bloqueante (informativa):** varios casos del bucle TDD pasaron
  "verde de inmediato" sin fase roja clásica porque implementaciones previas del
  mismo módulo ya satisfacían el contrato (documentado honestamente en
  `state.json`). En cada uno, `tdd_tester` dejó constancia de una **verificación
  razonada** (rotura temporal + reversión con `git diff` limpio) que confirma que
  el test **sí** detecta la regresión. El verificador considera esto una práctica
  correcta que **no** compromete la validez de la evidencia. No genera acción.

---

## Etapa de retorno recomendada

**No aplica** (veredicto CONFORME). Siguiente paso del flujo: **paso 13 — abrir el
PR** (lo escribe el agente) → **gate humano** `human_test` + `merge_to_main`
(aprobación y merge exclusivos del humano, C-03).
