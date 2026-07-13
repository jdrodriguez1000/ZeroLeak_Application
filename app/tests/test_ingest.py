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
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

import pytest

from zeroleak.ingest.core import TenantNotFoundError, ingest_paths


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
