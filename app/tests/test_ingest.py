"""Tests unitarios del core `zeroleak.ingest.core`.

Caso 1 del bucle TDD (feature `ingest`): invocar `ingest_paths` sobre un
tenant inexistente lanza `TenantNotFoundError` sin crear ni modificar ningún
artefacto en bronze ni en manifest de ningún tenant (CA-08, TSK-02).

Caso 2 del bucle TDD: dado un tenant existente y un `.csv` sintético válido,
`ingest_paths` copia el archivo byte a byte a `data/bronze/<file>` y agrega
**una** entrada en `manifest.json` con el `sha256` correcto y
`status == "pending"` (CA-01, TSK-04).

Caso 3 del bucle TDD: la entrada de manifest agregada tiene **exactamente**
las 4 claves `file`, `sha256` (64 hex), `ingested_at` (ISO-8601, precisión de
segundos) y `status`; **no** contiene `period`, `run_id` ni `output` (CA-02,
TSK-06). Este test es de **caracterización/regresión**, no de ciclo
rojo-verde: al revisarlo, CA-02 ya estaba completamente satisfecho como
efecto colateral del Caso 2 (`_build_manifest_entry` en `core.py`, TSK-05);
no hubo código nuevo que escribir (TSK-07), así que este test blinda ese
comportamiento contra regresiones futuras. Datos sintéticos únicamente
(regla "Datos en Bóveda", C-01).

Caso 4 del bucle TDD: un archivo de 0 bytes se reporta como fallo con motivo
"archivo vacío"; no se copia a `data/bronze/` ni se anota en el manifest; la
invocación cuyo único archivo es vacío retorna `exit_code == 1` (CA-09,
TSK-08). El core actual (Caso 2/TSK-05) todavía no implementa la validación
básica por archivo (tamaño > 0), así que este test debe fallar en RED.

Caso 5 del bucle TDD: reenviar un archivo cuyo `sha256` ya está en el
manifest es un no-op idempotente (SKIP): no se copia de nuevo a
`data/bronze/`, no se agrega una entrada nueva, se reporta en
`result.duplicates` y `exit_code == 0` (no cuenta como fallo). Cubre también
el dedupe **dentro de la misma invocación**: si dos rutas del mismo llamado
a `ingest_paths` tienen contenido idéntico, la segunda se reporta como
duplicado (CA-05, TSK-10). El core actual (Caso 4/TSK-09) todavía no calcula
dedupe por `sha256` -- copiaría/anotaría la segunda entrada -- así que estos
tests deben fallar en RED.

Caso 6 del bucle TDD: ingerir un archivo con **mismo nombre** pero
**contenido distinto** a uno ya presente en `data/bronze/` crea una
**nueva** entrada; el archivo se almacena como `<stem>__<sha8><suffix>` (los
8 primeros hex del nuevo `sha256`) sin sobrescribir el original, y el campo
`file` de la nueva entrada es ese nombre con sufijo (CA-06, TSK-12). El core
actual (Caso 5/TSK-11) siempre copia a `bronze_dir / source.name`, así que
una colisión de nombre con contenido distinto sobrescribiría el original en
vez de recibir un nombre con sufijo -- este test debe fallar en RED.

Caso 9 del bucle TDD: tres archivos `.csv` con contenido **lógicamente
equivalente** pero delimitador `,`, `;` y `|` respectivamente (bytes crudos
distintos entre sí) se ingieren **los tres sin error**: copia byte a byte,
`sha256` calculado sobre los bytes crudos (nunca sobre contenido parseado),
produciendo **3 entradas** distintas con **3 `sha256` distintos**. `ingest`
en ningún caso abre ni parsea el contenido como CSV -- ninguna librería de
CSV se usa en el test ni se espera que el core distinga entre delimitadores
(CA-10, TSK-18). El core actual (desde el Caso 2/TSK-05 en adelante) ya
opera exclusivamente sobre bytes crudos (`Path.read_bytes()` +
`hashlib.sha256`, sin `csv.reader`/`open(..., newline=...)` en ningún punto
de `core.py`), así que se espera que este test sea de
**caracterización/regresión** (mismo patrón que los Casos 3 y 8), no un
ciclo rojo-verde clásico.

Caso 10 del bucle TDD: una invocación con **cuatro** rutas mezcladas --
válida, vacía, extensión no permitida (archivo suelto) e inexistente -- debe
ingerir **solo** la válida; las 3 inválidas se reportan en `result.failed`,
cada una con su motivo respectivo: `"archivo vacío"`, `"extensión fuera de
allow-list"` y `"la ruta no existe"`; `exit_code == 1`. El procesamiento es
**parcial**: una ruta que falla no aborta el resto (CA-07, TSK-20). El core
actual (Caso 7/TSK-15) valida únicamente tamaño > 0 para archivos sueltos
(`_validate_file`); no valida existencia de ruta ni extensión fuera de
allow-list para un archivo suelto pasado directamente (esa allow-list solo
se aplica hoy al recorrido de carpetas, `_expand_paths`). Además, una ruta
inexistente hace que `Path(path).stat()` lance `FileNotFoundError` sin
capturar, en vez de enrutarse a `result.failed`. Por eso este test debe
fallar en RED.

Caso 7 del bucle TDD: una **carpeta** pasada como `path` se recorre de forma
**plana** (solo primer nivel, sin recursión, `iterdir()`): se ingieren
únicamente los archivos con extensión ∈ allow-list (`a.csv`, `b.xlsx`); los
demás archivos fuera de la allow-list (`c.txt`) y las **subcarpetas**
(`sub/`, junto con su contenido `sub/d.csv`) se **ignoran en silencio** --
no aparecen en bronze, ni en el manifest, ni en `result.failed` (CA-03,
TSK-14). El core actual (Caso 6/TSK-13) trata **todo** `path` de `paths`
como si fuera un archivo (`_validate_file`/`_hash_file` llaman a
`source.stat()`/`source.read_bytes()` directamente sobre `source`, sin
distinguir si es una carpeta): al recibir una carpeta, `read_bytes()` sobre
un directorio lanza `IsADirectoryError`, así que este test debe fallar en
RED. (En la práctica, `_validate_file`/`_hash_file` no distinguen archivo de
carpeta: el `path` de la carpeta se enruta por el camino de validación de
archivo -- en algunas plataformas `stat().st_size` de un directorio es `0`,
así que se reporta como fallo "archivo vacío" y nada se copia a bronze; en
otras, `read_bytes()` sobre un directorio lanza una excepción. En ambos
casos, el resultado observable no cumple el contrato de CA-03: no hay
despacho de carpeta todavía.)

Caso 11 del bucle TDD: la regla `.gitignore` `clients/*/data/` (ya vigente
desde `client_scaffold`, C-01) cubre efectivamente cualquier ruta bajo
`clients/<CLIENTE>/data/bronze/...` y `clients/<CLIENTE>/data/manifest.json`,
y NO cubre `client.yaml` ni `input/...` (artefactos versionables) (CA-11,
TSK-22). Se verifica el comportamiento **real** de Git con
`git check-ignore -v`, ejecutado desde la raíz del repo, sobre rutas
relativas **ficticias** (`clients/DEMO_INGEST_X/...`); no se crea ningún
tenant real (Regla "Datos en Bóveda", C-01) -- `git check-ignore` evalúa el
path contra las reglas sin requerir que el archivo/directorio exista en
disco. Mismo patrón que `app/tests/test_scaffold.py`
(`test_gitignore_cubre_data_del_tenant` /
`test_gitignore_no_cubre_client_yaml_ni_input`, Caso 12 de `client_scaffold`).
Este test es de **caracterización**: la regla `.gitignore` ya está vigente y
no requiere código nuevo (TSK-22 no tiene tarea de código pareja); se espera
que pase de inmediato si el `.gitignore` ya se comporta como exige CA-11.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

import pytest

from zeroleak.ingest.core import TenantNotFoundError, ingest_paths


def test_ingest_paths_argumentos_mezclados_archivo_y_carpeta_ingiere_union(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-04 (Caso 8): argumentos mezclados `[archivo.csv, carpeta/]`.

    Dado un tenant existente, un `.csv` sintético válido suelto y una
    carpeta con `a.csv`, `b.xlsx`, `c.txt` y una subcarpeta `sub/d.csv`,
    invocar `ingest_paths` con AMBOS `paths` en la MISMA llamada (archivo
    suelto primero, carpeta después) debe ingerir la **unión** de ambos
    orígenes:
    - el archivo suelto (`suelto.csv`);
    - los `.csv`/`.xlsx` del primer nivel de la carpeta (`a.csv`, `b.xlsx`);
    - **sin** descender a `sub/` ni copiar `c.txt` (ignorados en silencio,
      igual que en el Caso 7 de recorrido de carpeta aislado);
    - el manifest gana exactamente **3** entradas nuevas (una por cada
      origen ingerido), sin duplicar el ledger;
    - `resultado.ingested` tiene 3 ítems, `resultado.duplicates == []`,
      `resultado.failed == []` y `resultado.exit_code == 0`.
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    bronze_dir = tenant_dir / "data" / "bronze"

    contenido_suelto = b"producto,monto\nempanada,1500\n"
    suelto = tmp_path / "suelto.csv"
    suelto.write_bytes(contenido_suelto)
    sha256_suelto = hashlib.sha256(contenido_suelto).hexdigest()

    carpeta = tmp_path / "entrega"
    carpeta.mkdir()

    contenido_a = b"fecha,total\n2024-01-01,1000\n"
    (carpeta / "a.csv").write_bytes(contenido_a)
    sha256_a = hashlib.sha256(contenido_a).hexdigest()

    contenido_b = b"bytes-opacos-xlsx-sinteticos-mezclados"
    (carpeta / "b.xlsx").write_bytes(contenido_b)
    sha256_b = hashlib.sha256(contenido_b).hexdigest()

    (carpeta / "c.txt").write_bytes(b"nota fuera de la allow-list")

    subcarpeta = carpeta / "sub"
    subcarpeta.mkdir()
    (subcarpeta / "d.csv").write_bytes(b"producto,monto\narepa,2000\n")

    resultado = ingest_paths(
        "SANDUCHERIA", [str(suelto), str(carpeta)], clients_root
    )

    archivos_bronze = {p.name for p in bronze_dir.iterdir()}
    assert archivos_bronze == {"suelto.csv", "a.csv", "b.xlsx"}, (
        "el archivo suelto y a.csv/b.xlsx deben copiarse; c.txt y sub/ ignorados"
    )

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 3, (
        "deben agregarse exactamente 3 entradas (union de archivo + carpeta)"
    )
    shas_manifest = {entrada["sha256"] for entrada in manifest["files"]}
    assert shas_manifest == {sha256_suelto, sha256_a, sha256_b}

    assert len(resultado.ingested) == 3
    shas_ingeridos = {item["sha256"] for item in resultado.ingested}
    assert shas_ingeridos == {sha256_suelto, sha256_a, sha256_b}
    assert resultado.duplicates == []
    assert resultado.failed == [], (
        "c.txt, sub/ y sub/d.csv se ignoran en silencio, no son fallos"
    )
    assert resultado.exit_code == 0


def test_ingest_paths_tenant_inexistente_lanza_tenant_not_found_error_sin_tocar_disco(
    clients_root: Path,
) -> None:
    """CA-08: tenant inexistente aborta la invocación completa.

    `clients_root` (fixture sintética, aislada en `tmp_path`) está limpio:
    ningún tenant `SANDUCHERIA` fue creado (ni por `client_scaffold` ni por
    ninguna otra vía), por lo que no existen `data/bronze/` ni
    `data/manifest.json` para ese cliente. `ingest_paths` debe lanzar
    `TenantNotFoundError` sin crear ni modificar ningún artefacto: ni el
    tenant destino, ni ningún otro directorio/archivo bajo `clients_root`.
    """
    assert list(clients_root.iterdir()) == []

    with pytest.raises(TenantNotFoundError):
        ingest_paths("SANDUCHERIA", ["archivo_no_ingerido.csv"], clients_root)

    # Precondición global incumplida: no se crea ni el tenant destino ni
    # ningún otro artefacto bajo clients_root (aborta sin tocar disco).
    assert list(clients_root.iterdir()) == []


def test_ingest_paths_csv_valido_copia_a_bronze_y_agrega_entrada_pending(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-01 (Caso 2): un `.csv` sintético válido se ingiere byte a byte.

    Dado un tenant ya existente (`ingestible_tenant`, con `data/bronze/` y
    `data/manifest.json` inicial vacío) y un archivo `.csv` sintético válido
    fuera del tenant, `ingest_paths` debe:
    - copiar el archivo a `data/bronze/<file>` de modo que
      `sha256(bronze/<file>) == sha256(original)` (copia byte a byte, sin
      abrir/parsear el contenido);
    - agregar **una** entrada en `manifest.json` con ese `sha256` y
      `status == "pending"`;
    - retornar un `IngestResult` con `exit_code == 0` (éxito total, sin
      fallos).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")

    origen = tmp_path / "ventas.csv"
    contenido = b"producto,monto\nempanada,1500\n"
    origen.write_bytes(contenido)
    sha256_esperado = hashlib.sha256(contenido).hexdigest()

    resultado = ingest_paths("SANDUCHERIA", [str(origen)], clients_root)

    archivo_bronze = tenant_dir / "data" / "bronze" / "ventas.csv"
    assert archivo_bronze.is_file(), "el archivo debe copiarse a data/bronze/"
    bytes_bronze = archivo_bronze.read_bytes()
    assert bytes_bronze == contenido, "la copia debe ser byte a byte (idéntica)"
    assert hashlib.sha256(bytes_bronze).hexdigest() == sha256_esperado

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1, "debe agregarse exactamente una entrada"
    entrada = manifest["files"][0]
    assert entrada["sha256"] == sha256_esperado
    assert entrada["status"] == "pending"

    assert resultado.exit_code == 0


def test_ingest_paths_entrada_manifest_tiene_exactamente_los_4_campos_de_ca02(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-02 (Caso 3): forma EXACTA de la entrada agregada al manifest.

    Test de **caracterización/regresión**: no forma parte de un ciclo
    rojo-verde clásico. Al escribir este test (fase RED, paso 10) se
    encontró que CA-02 ya estaba completamente satisfecho como efecto
    colateral del Caso 2 (`_build_manifest_entry(name, sha256)` en
    `core.py`, TSK-05/refactor), así que corre en verde desde el primer
    momento. Se conserva como blindaje contra regresiones futuras de la
    forma exacta de la entrada del manifest.

    Tras ingerir un `.csv` sintético válido, la entrada agregada a
    `manifest.json` debe tener **exactamente** el conjunto de claves
    `{"file", "sha256", "ingested_at", "status"}` -- ni una menos, ni una de
    más. En particular:
    - **no** debe contener `period`, `run_id` ni `output` (aserción negativa
      explícita, no basta con que el set de claves "coincida por accidente");
    - `sha256` debe ser una cadena hex de 64 caracteres en minúsculas;
    - `ingested_at` debe ser ISO-8601 con **precisión de segundos** exacta:
      sin componente de microsegundos ni offset de zona horaria -- patrón
      exacto `YYYY-MM-DDTHH:MM:SS`, parseable con
      `datetime.fromisoformat(...)` y `.microsecond == 0` / `.tzinfo is None`.
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")

    origen = tmp_path / "reporte.csv"
    contenido = b"fecha,total\n2024-01-01,1000\n"
    origen.write_bytes(contenido)

    ingest_paths("SANDUCHERIA", [str(origen)], clients_root)

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1
    entrada = manifest["files"][0]

    # Aserción positiva + negativa combinada: el set de claves es EXACTO.
    assert set(entrada.keys()) == {"file", "sha256", "ingested_at", "status"}

    # Aserciones negativas explícitas (independientes de la comparación de
    # sets, para que la traza a CA-02 sea legible por sí sola).
    assert "period" not in entrada
    assert "run_id" not in entrada
    assert "output" not in entrada

    # sha256: 64 hex en minúsculas.
    assert re.fullmatch(r"[0-9a-f]{64}", entrada["sha256"])

    # ingested_at: ISO-8601 con precisión de segundos EXACTA (sin
    # microsegundos, sin offset de zona horaria) -- patrón exacto de la
    # cadena, no solo parseabilidad.
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", entrada["ingested_at"]
    ), f"ingested_at con formato inesperado: {entrada['ingested_at']!r}"
    parsed = datetime.fromisoformat(entrada["ingested_at"])
    assert parsed.microsecond == 0
    assert parsed.tzinfo is None


def test_ingest_paths_archivo_vacio_se_reporta_como_fallo_y_no_se_ingiere(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-09 (Caso 4): un archivo de 0 bytes NO se ingiere; falla por ruta.

    Dado un tenant existente y un archivo `.csv` sintético de **0 bytes**,
    `ingest_paths` debe:
    - **no** copiarlo a `data/bronze/` (ningún archivo nuevo en bronze);
    - **no** agregar ninguna entrada al `manifest.json` (el ledger no se
      corrompe: sigue con las mismas 0 entradas previas);
    - reportarlo en `result.failed` con motivo "archivo vacío";
    - retornar un `IngestResult` con `exit_code == 1` (fallo por ruta /
      éxito parcial, ya que esta es la única ruta de la invocación).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")

    archivo_vacio = tmp_path / "vacio.csv"
    archivo_vacio.write_bytes(b"")
    assert archivo_vacio.stat().st_size == 0

    resultado = ingest_paths("SANDUCHERIA", [str(archivo_vacio)], clients_root)

    bronze_dir = tenant_dir / "data" / "bronze"
    assert list(bronze_dir.iterdir()) == [], (
        "el archivo vacío no debe copiarse a data/bronze/"
    )

    manifest = read_manifest(tenant_dir)
    assert manifest["files"] == [], (
        "el manifest no debe ganar ninguna entrada por un archivo vacío"
    )

    assert len(resultado.failed) == 1
    fallo = resultado.failed[0]
    assert fallo["reason"] == "archivo vacío"
    assert resultado.ingested == []

    assert resultado.exit_code == 1


def test_ingest_paths_dedupe_sha256_reenviar_archivo_ya_ingerido_es_no_op_skip(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-05 (Caso 5): reenviar un `sha256` ya presente en el manifest es SKIP.

    Dado un tenant existente con un archivo ya ingerido (entrada previa en
    `manifest.json` con su `sha256`), reenviar **otro** archivo (incluso con
    nombre distinto) cuyo contenido produce el **mismo** `sha256` debe ser un
    no-op idempotente:
    - **no** se copia una segunda vez a `data/bronze/` (el directorio sigue
      con un único archivo, el de la primera ingesta);
    - **no** se agrega una entrada nueva al manifest (sigue con una sola
      entrada, la original);
    - se reporta en `resultado.duplicates` (no en `failed`, no en
      `ingested`);
    - `resultado.exit_code == 0` (el duplicado no cuenta como fallo).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    contenido = b"producto,monto\nempanada,1500\n"

    primero = tmp_path / "ventas.csv"
    primero.write_bytes(contenido)
    ingest_paths("SANDUCHERIA", [str(primero)], clients_root)

    segundo = tmp_path / "ventas_reenviado.csv"
    segundo.write_bytes(contenido)
    resultado = ingest_paths("SANDUCHERIA", [str(segundo)], clients_root)

    bronze_dir = tenant_dir / "data" / "bronze"
    archivos_bronze = list(bronze_dir.iterdir())
    assert len(archivos_bronze) == 1, (
        "no debe crearse una segunda copia en bronze por contenido duplicado"
    )

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1, (
        "no debe agregarse una entrada nueva al manifest por contenido duplicado"
    )

    assert resultado.ingested == []
    assert resultado.failed == []
    assert len(resultado.duplicates) == 1
    duplicado = resultado.duplicates[0]
    assert duplicado["sha256"] == hashlib.sha256(contenido).hexdigest()
    assert duplicado["status"] == "duplicate"

    assert resultado.exit_code == 0


def test_ingest_paths_dedupe_sha256_dentro_de_la_misma_invocacion_segunda_ruta_es_duplicate(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-05 (Caso 5): dedupe también dentro de una única invocación.

    Dos rutas **distintas** pasadas en la **misma** llamada a `ingest_paths`
    cuyo contenido produce idéntico `sha256`: la primera se ingiere
    normalmente y la segunda se reporta como duplicado (SKIP), sin que el
    manifest previo del tenant tuviera ninguna entrada con ese `sha256`
    (el dedupe debe considerar también lo acumulado en la corrida actual,
    no solo el ledger cargado al inicio).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    contenido = b"fecha,total\n2024-01-01,1000\n"

    ruta_a = tmp_path / "reporte_a.csv"
    ruta_a.write_bytes(contenido)
    ruta_b = tmp_path / "reporte_b.csv"
    ruta_b.write_bytes(contenido)

    resultado = ingest_paths(
        "SANDUCHERIA", [str(ruta_a), str(ruta_b)], clients_root
    )

    bronze_dir = tenant_dir / "data" / "bronze"
    assert len(list(bronze_dir.iterdir())) == 1, (
        "solo la primera ruta con este contenido debe copiarse a bronze"
    )

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1, (
        "solo debe agregarse una entrada para el contenido repetido"
    )

    assert len(resultado.ingested) == 1
    assert resultado.failed == []
    assert len(resultado.duplicates) == 1
    duplicado = resultado.duplicates[0]
    assert duplicado["sha256"] == hashlib.sha256(contenido).hexdigest()
    assert duplicado["status"] == "duplicate"
    assert duplicado["path"] == str(ruta_b)

    assert resultado.exit_code == 0


def test_ingest_paths_colision_de_nombre_con_contenido_distinto_usa_sufijo_sha8(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-06 (Caso 6): mismo nombre, contenido distinto -> nombre con sufijo.

    Dado un tenant existente con un archivo ya ingerido (`ventas.csv`),
    ingerir **otro** archivo cuyo nombre origen es también `ventas.csv` pero
    cuyo contenido -- y por lo tanto `sha256` -- es **distinto**, debe:
    - **no** sobrescribir el `ventas.csv` original en `data/bronze/` (sus
      bytes deben seguir siendo los del primer contenido);
    - almacenar el nuevo archivo como `ventas__<sha8>.csv`, donde `<sha8>`
      son los 8 primeros caracteres hex del `sha256` del **nuevo**
      contenido;
    - agregar una **segunda** entrada al manifest (dos entradas en total)
      cuyo campo `file` sea exactamente ese nombre con sufijo y cuyo
      `sha256` sea el del nuevo contenido;
    - reportar el nuevo archivo en `resultado.ingested` (no en `duplicates`
      ni en `failed`), con `resultado.exit_code == 0`.
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    bronze_dir = tenant_dir / "data" / "bronze"

    contenido_original = b"producto,monto\nempanada,1500\n"
    original = tmp_path / "ventas.csv"
    original.write_bytes(contenido_original)
    ingest_paths("SANDUCHERIA", [str(original)], clients_root)

    contenido_nuevo = b"producto,monto\narepa,2000\n"
    sha256_nuevo = hashlib.sha256(contenido_nuevo).hexdigest()
    sha8_nuevo = sha256_nuevo[:8]

    otra_carpeta = tmp_path / "otra_carpeta"
    otra_carpeta.mkdir()
    colisionado = otra_carpeta / "ventas.csv"
    colisionado.write_bytes(contenido_nuevo)

    resultado = ingest_paths("SANDUCHERIA", [str(colisionado)], clients_root)

    # El original no se sobrescribe.
    original_bronze = bronze_dir / "ventas.csv"
    assert original_bronze.is_file()
    assert original_bronze.read_bytes() == contenido_original, (
        "el archivo original en bronze no debe ser sobrescrito por la colisión"
    )

    # El nuevo archivo se almacena con sufijo __<sha8>.
    nombre_esperado = f"ventas__{sha8_nuevo}.csv"
    archivo_sufijado = bronze_dir / nombre_esperado
    assert archivo_sufijado.is_file(), (
        f"se esperaba {nombre_esperado!r} en data/bronze/"
    )
    assert archivo_sufijado.read_bytes() == contenido_nuevo

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 2, "debe haber dos entradas (original + colisión)"
    entrada_nueva = next(
        e for e in manifest["files"] if e["sha256"] == sha256_nuevo
    )
    assert entrada_nueva["file"] == nombre_esperado

    assert len(resultado.ingested) == 1
    assert resultado.ingested[0]["file"] == nombre_esperado
    assert resultado.duplicates == []
    assert resultado.failed == []
    assert resultado.exit_code == 0


def test_ingest_paths_carpeta_recorrido_plano_ignora_subcarpetas_y_extension_no_permitida(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-03 (Caso 7): recorrido plano de una carpeta pasada como `path`.

    Dada una carpeta con `a.csv`, `b.xlsx`, `c.txt` y una subcarpeta `sub/`
    que contiene `d.csv`, ingerir esa carpeta (como único `path`) debe:
    - registrar **exactamente 2** entradas en el manifest, una por `a.csv`
      y otra por `b.xlsx` (los únicos con extensión ∈ allow-list en el
      primer nivel);
    - **no** copiar `c.txt` a bronze (extensión fuera de la allow-list,
      ignorado en silencio, no cuenta como fallo);
    - **no** descender a `sub/` (sin recursión): ni la subcarpeta ni
      `sub/d.csv` aparecen en bronze, en el manifest, ni en `result.failed`;
    - `result.failed == []` (todo lo ignorado lo es en silencio) y
      `result.exit_code == 0`.
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    bronze_dir = tenant_dir / "data" / "bronze"

    carpeta = tmp_path / "entrega"
    carpeta.mkdir()

    contenido_a = b"producto,monto\nempanada,1500\n"
    (carpeta / "a.csv").write_bytes(contenido_a)
    sha256_a = hashlib.sha256(contenido_a).hexdigest()

    contenido_b = b"bytes-opacos-xlsx-sinteticos"
    (carpeta / "b.xlsx").write_bytes(contenido_b)
    sha256_b = hashlib.sha256(contenido_b).hexdigest()

    (carpeta / "c.txt").write_bytes(b"nota fuera de la allow-list")

    subcarpeta = carpeta / "sub"
    subcarpeta.mkdir()
    (subcarpeta / "d.csv").write_bytes(b"producto,monto\narepa,2000\n")

    resultado = ingest_paths("SANDUCHERIA", [str(carpeta)], clients_root)

    archivos_bronze = {p.name for p in bronze_dir.iterdir()}
    assert archivos_bronze == {"a.csv", "b.xlsx"}, (
        "solo a.csv y b.xlsx deben copiarse a bronze; c.txt y sub/ ignorados"
    )

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 2, "deben agregarse exactamente 2 entradas"
    shas_manifest = {entrada["sha256"] for entrada in manifest["files"]}
    assert shas_manifest == {sha256_a, sha256_b}

    assert len(resultado.ingested) == 2
    assert resultado.duplicates == []
    assert resultado.failed == [], (
        "c.txt, sub/ y sub/d.csv se ignoran en silencio, no son fallos"
    )
    assert resultado.exit_code == 0


def test_ingest_paths_csv_con_distintos_delimitadores_se_ingieren_los_3_sin_parseo(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-10 (Caso 9): agnosticismo de formato -- delimitadores sin parseo.

    Dados tres archivos `.csv` sintéticos con contenido **lógicamente
    equivalente** (mismas "columnas"/"filas") pero con delimitador `,`, `;`
    y `|` respectivamente -- por lo tanto tres secuencias de **bytes
    distintas** entre sí -- invocar `ingest_paths` con los tres `paths` en
    la misma llamada debe:
    - ingerir **los tres sin error** (ninguno cae en `failed`);
    - copiar cada uno **byte a byte** a `data/bronze/<file>` (bytes idénticos
      al origen, sin reformatear ni normalizar delimitador);
    - calcular el `sha256` de cada uno sobre sus **bytes crudos**: los tres
      `sha256` deben ser **distintos entre sí** (si `ingest` parseara el CSV
      y normalizara antes de hashear, los tres podrían colapsar a un único
      contenido "equivalente" -- este test lo descarta explícitamente);
    - agregar **3 entradas** nuevas al manifest, una por archivo, cada una
      con `status == "pending"`;
    - `resultado.ingested` tiene 3 ítems, `resultado.duplicates == []`,
      `resultado.failed == []` y `resultado.exit_code == 0`.

    Este test no importa ni usa el módulo `csv` de la librería estándar en
    ningún punto: el contenido se trata como bytes opacos de principio a
    fin, coherente con "ingest nunca abre ni parsea el contenido" (CA-10).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    bronze_dir = tenant_dir / "data" / "bronze"

    contenido_coma = b"producto,monto,fecha\nempanada,1500,2024-01-01\n"
    contenido_puntocoma = b"producto;monto;fecha\nempanada;1500;2024-01-01\n"
    contenido_pipe = b"producto|monto|fecha\nempanada|1500|2024-01-01\n"

    ruta_coma = tmp_path / "ventas_coma.csv"
    ruta_coma.write_bytes(contenido_coma)
    ruta_puntocoma = tmp_path / "ventas_puntocoma.csv"
    ruta_puntocoma.write_bytes(contenido_puntocoma)
    ruta_pipe = tmp_path / "ventas_pipe.csv"
    ruta_pipe.write_bytes(contenido_pipe)

    sha256_coma = hashlib.sha256(contenido_coma).hexdigest()
    sha256_puntocoma = hashlib.sha256(contenido_puntocoma).hexdigest()
    sha256_pipe = hashlib.sha256(contenido_pipe).hexdigest()

    # Los tres contenidos "lógicamente equivalentes" producen bytes crudos
    # distintos (y por lo tanto sha256 distintos) precisamente porque el
    # delimitador forma parte de los bytes.
    assert len({sha256_coma, sha256_puntocoma, sha256_pipe}) == 3

    resultado = ingest_paths(
        "SANDUCHERIA",
        [str(ruta_coma), str(ruta_puntocoma), str(ruta_pipe)],
        clients_root,
    )

    archivos_bronze = {p.name for p in bronze_dir.iterdir()}
    assert archivos_bronze == {
        "ventas_coma.csv",
        "ventas_puntocoma.csv",
        "ventas_pipe.csv",
    }, "los 3 .csv con distinto delimitador deben copiarse byte a byte a bronze"

    assert (bronze_dir / "ventas_coma.csv").read_bytes() == contenido_coma
    assert (
        bronze_dir / "ventas_puntocoma.csv"
    ).read_bytes() == contenido_puntocoma
    assert (bronze_dir / "ventas_pipe.csv").read_bytes() == contenido_pipe

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 3, "deben agregarse exactamente 3 entradas"
    shas_manifest = {entrada["sha256"] for entrada in manifest["files"]}
    assert shas_manifest == {sha256_coma, sha256_puntocoma, sha256_pipe}, (
        "los 3 sha256 deben ser distintos entre sí (hash sobre bytes crudos, "
        "no sobre contenido parseado/normalizado)"
    )
    for entrada in manifest["files"]:
        assert entrada["status"] == "pending"

    assert len(resultado.ingested) == 3
    shas_ingeridos = {item["sha256"] for item in resultado.ingested}
    assert shas_ingeridos == {sha256_coma, sha256_puntocoma, sha256_pipe}
    assert resultado.duplicates == []
    assert resultado.failed == []
    assert resultado.exit_code == 0


def test_ingest_paths_mezcla_valida_vacia_extension_no_permitida_e_inexistente(
    clients_root: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], Dict],
    tmp_path: Path,
) -> None:
    """CA-07 (Caso 10): mezcla válida + vacía + extensión no permitida + inexistente.

    Dado un tenant existente y CUATRO rutas en la misma invocación:
    - `valido.csv` -- archivo `.csv` sintético válido (no vacío);
    - `vacio.csv` -- archivo de 0 bytes;
    - `datos.txt` -- archivo suelto con extensión fuera de la allow-list;
    - una ruta que no existe en disco;

    `ingest_paths` debe ingerir **únicamente** `valido.csv` y reportar las
    otras 3 rutas en `result.failed`, cada una con su motivo exacto:
    `"archivo vacío"`, `"extensión fuera de allow-list"` y `"la ruta no
    existe"` respectivamente. El procesamiento es parcial: una ruta inválida
    no aborta el resto -- las demás rutas (incluida la válida) se procesan
    igual. `resultado.exit_code == 1` (≥ 1 ruta fallida).
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")
    bronze_dir = tenant_dir / "data" / "bronze"

    contenido_valido = b"producto,monto\nempanada,1500\n"
    valido = tmp_path / "valido.csv"
    valido.write_bytes(contenido_valido)
    sha256_valido = hashlib.sha256(contenido_valido).hexdigest()

    vacio = tmp_path / "vacio.csv"
    vacio.write_bytes(b"")

    extension_no_permitida = tmp_path / "datos.txt"
    extension_no_permitida.write_bytes(b"nota fuera de la allow-list")

    inexistente = tmp_path / "no_existe.csv"
    assert not inexistente.exists()

    resultado = ingest_paths(
        "SANDUCHERIA",
        [str(valido), str(vacio), str(extension_no_permitida), str(inexistente)],
        clients_root,
    )

    # Solo la ruta válida se copia a bronze.
    archivos_bronze = {p.name for p in bronze_dir.iterdir()}
    assert archivos_bronze == {"valido.csv"}, (
        "solo valido.csv debe copiarse a bronze; las 3 inválidas no"
    )

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1, "solo debe agregarse una entrada (la válida)"
    assert manifest["files"][0]["sha256"] == sha256_valido

    assert len(resultado.ingested) == 1
    assert resultado.ingested[0]["sha256"] == sha256_valido
    assert resultado.duplicates == []

    assert len(resultado.failed) == 3, "las 3 rutas inválidas deben reportarse en failed"
    motivos_por_path = {item["path"]: item["reason"] for item in resultado.failed}
    assert motivos_por_path[str(vacio)] == "archivo vacío"
    assert motivos_por_path[str(extension_no_permitida)] == (
        "extensión fuera de allow-list"
    )
    assert motivos_por_path[str(inexistente)] == "la ruta no existe"

    assert resultado.exit_code == 1


# --- Caso 11 (TSK-22, CA-11): gitignore-frontera-pii ------------------------
#
# La regla `.gitignore` `clients/*/data/` (C-01, "Datos en Bóveda") debe
# cubrir efectivamente `clients/<CLIENTE>/data/` -- incluyendo `bronze/...` y
# `manifest.json`, que produce/agrega `ingest` -- y NO debe cubrir
# `client.yaml` ni `input/...` (versionables). Se verifica el comportamiento
# REAL de Git con `git check-ignore -v`, ejecutado desde la raíz del repo,
# sobre rutas relativas ficticias del patrón `clients/DEMO_INGEST_X/...`.
# `git check-ignore` evalúa el path contra las reglas sin requerir que el
# archivo exista en disco, por lo que no se crea ningún tenant real bajo
# `clients/` (se respeta C-01: no se ensucia el repo con datos ni artefactos
# reales). Mismo patrón que `app/tests/test_scaffold.py` (Caso 12 de
# `client_scaffold`).


def _repo_root() -> Path:
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def _git_check_ignore(rel_path: str) -> bool:
    """Retorna True si `git check-ignore` marca `rel_path` como ignorado.

    Ejecuta el comando con `cwd` en la raíz del repo, sobre una ruta
    relativa ficticia (no requiere que el archivo/directorio exista).
    """
    import subprocess

    result = subprocess.run(
        ["git", "check-ignore", "-v", "--", rel_path],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
    )
    # exit code 0 => la ruta está ignorada; 1 => no ignorada.
    return result.returncode == 0


INGEST_IGNORED_PATHS = [
    "clients/DEMO_INGEST_X/data/",
    "clients/DEMO_INGEST_X/data/bronze/ventas.csv",
    "clients/DEMO_INGEST_X/data/bronze/ventas__a1b2c3d4.csv",
    "clients/DEMO_INGEST_X/data/manifest.json",
]

INGEST_VERSIONABLE_PATHS = [
    "clients/DEMO_INGEST_X/client.yaml",
    "clients/DEMO_INGEST_X/input/contract_data.yaml",
]


@pytest.mark.parametrize("rel_path", INGEST_IGNORED_PATHS)
def test_gitignore_cubre_bronze_y_manifest_producidos_por_ingest(
    rel_path: str,
) -> None:
    """CA-11 (Caso 11): `git check-ignore` marca como ignorada cualquier ruta
    bajo `clients/<CLIENTE>/data/bronze/...` y `clients/<CLIENTE>/data/manifest.json`
    -- exactamente los artefactos que `ingest_paths` produce/agrega.
    """
    assert _git_check_ignore(rel_path), (
        f"{rel_path!r} debería estar cubierto por la regla .gitignore "
        f"'clients/*/data/' (C-01) pero git check-ignore no lo marcó"
    )


@pytest.mark.parametrize("rel_path", INGEST_VERSIONABLE_PATHS)
def test_gitignore_no_cubre_client_yaml_ni_input_para_ingest(
    rel_path: str,
) -> None:
    """CA-11 (Caso 11): `git check-ignore` NO marca como ignorados
    `client.yaml` ni los archivos bajo `input/`: deben permanecer
    versionables.
    """
    assert not _git_check_ignore(rel_path), (
        f"{rel_path!r} NO debería estar cubierto por .gitignore (es "
        f"versionable) pero git check-ignore lo marcó como ignorado"
    )
