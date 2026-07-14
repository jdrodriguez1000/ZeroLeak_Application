"""Tests de la fachada CLI `zlk ingest <CLIENTE> <ruta>...` — TSK-23 (Caso 12,
CA-12).

Contrato esperado (fijado por `tdd_tester` para que `tdd_coder` lo implemente
en la fase GREEN, TSK-24):

- El comportamiento completo de la ingesta (validación, copia, hash, dedupe,
  nombrado, manifest, resultado) es observable llamando directamente a
  `zeroleak.ingest.core.ingest_paths(client, paths, clients_root)`, sin pasar
  por la CLI (primera mitad de CA-12; ya cubierto por el core desde el
  Caso 2 en adelante — este archivo agrega un test de "observabilidad sin
  CLI" propio de `test_cli_ingest.py`, sin duplicar el detalle fino que ya
  vive en `test_ingest.py`).
- `zeroleak.cli.main(["ingest", "<CLIENTE>", "<ruta>", ...])` produce el
  **mismo efecto en disco** (mismo árbol de bronze, mismo manifest) que
  invocar `ingest_paths` directamente sobre un `clients_root` gemelo, y
  traduce `IngestResult`/`TenantNotFoundError` a exit code:
  - `0` — éxito total (`IngestResult.exit_code == 0`, sin fallos).
  - `1` — éxito parcial / ≥ 1 ruta fallida (`IngestResult.exit_code == 1`).
  - `2` — precondición global incumplida (`TenantNotFoundError`, tenant
    inexistente).
- Resolución de `clients_root` en la CLI: convención `ZEROLEAK_CLIENTS_ROOT`
  ya fijada por `client_scaffold` (mismo patrón que `test_cli_client_new.py`).
- La CLI no contiene lógica de ingesta propia (fachada delgada, CA-12): el
  árbol de archivos que produce es idéntico al que produce `ingest_paths`
  invocado en proceso.

Regla "Datos en Bóveda" (C-01): `clients_root` siempre en `tmp_path`; tenant
sintético `SANDUCHERIA`, archivos ficticios (`ventas.csv`, `vacio.csv`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import pytest

from zeroleak.cli import main
from zeroleak.ingest.core import ingest_paths


def _make_tenant(clients_root: Path, name: str) -> Path:
    """Crea manualmente la estructura mínima de tenant ingerible bajo un
    `clients_root` propio (no se usa la fixture `ingestible_tenant` de
    `conftest.py` porque este archivo necesita **dos** `clients_root`
    gemelos -- uno para el core, otro para la CLI -- y esa fixture está
    atada a una única instancia de `clients_root`)."""
    tenant_dir = clients_root / name
    (tenant_dir / "data" / "bronze").mkdir(parents=True)
    manifest_path = tenant_dir / "data" / "manifest.json"
    manifest_path.write_text(
        json.dumps({"version": 1, "files": []}, indent=2), encoding="utf-8"
    )
    return tenant_dir


def _read_manifest(tenant_dir: Path) -> dict:
    return json.loads((tenant_dir / "data" / "manifest.json").read_text(encoding="utf-8"))


def test_ingest_paths_es_observable_sin_cli(
    tmp_path: Path,
    ingestible_tenant: Callable[[str], Path],
    read_manifest: Callable[[Path], dict],
) -> None:
    """CA-12 (primera mitad): el comportamiento completo de la ingesta es
    observable llamando directamente a `ingest_paths(...)`, sin usar la CLI.

    Este test ya debería pasar (el core existe desde el Caso 2 en adelante);
    documenta la mitad "core-observable" de CA-12 en este archivo dedicado a
    la fachada CLI.
    """
    tenant_dir = ingestible_tenant("SANDUCHERIA")

    csv_path = tmp_path / "ventas.csv"
    csv_path.write_bytes(b"col_a,col_b\n1,2\n")

    result = ingest_paths("SANDUCHERIA", [str(csv_path)], tenant_dir.parent)

    assert result.exit_code == 0
    assert len(result.ingested) == 1

    bronze_file = tenant_dir / "data" / "bronze" / "ventas.csv"
    assert bronze_file.is_file()
    assert bronze_file.read_bytes() == csv_path.read_bytes()

    manifest = read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["status"] == "pending"


def test_cli_ingest_mismo_efecto_en_disco_que_core_y_exit_code_0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CA-12 (segunda mitad, éxito total): `zlk ingest SANDUCHERIA <ruta>`
    produce el mismo efecto en disco que invocar `ingest_paths` directamente
    sobre un `clients_root` gemelo, y `main` retorna exit code `0`.
    """
    root_core = tmp_path / "root_core"
    root_core.mkdir()
    root_cli = tmp_path / "root_cli"
    root_cli.mkdir()

    tenant_core = _make_tenant(root_core, "SANDUCHERIA")
    tenant_cli = _make_tenant(root_cli, "SANDUCHERIA")

    csv_path = tmp_path / "ventas.csv"
    csv_path.write_bytes(b"col_a,col_b\n1,2\n")

    # Invocación directa del core.
    result_core = ingest_paths("SANDUCHERIA", [str(csv_path)], root_core)
    assert result_core.exit_code == 0

    # Misma ingesta vía la fachada CLI, sobre un clients_root gemelo.
    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(root_cli))
    exit_code = main(["ingest", "SANDUCHERIA", str(csv_path)])

    assert exit_code == 0

    bronze_core = tenant_core / "data" / "bronze" / "ventas.csv"
    bronze_cli = tenant_cli / "data" / "bronze" / "ventas.csv"
    assert bronze_cli.is_file()
    assert bronze_cli.read_bytes() == bronze_core.read_bytes()

    manifest_core = _read_manifest(tenant_core)
    manifest_cli = _read_manifest(tenant_cli)
    assert len(manifest_cli["files"]) == len(manifest_core["files"]) == 1
    assert manifest_cli["files"][0]["sha256"] == manifest_core["files"][0]["sha256"]
    assert manifest_cli["files"][0]["status"] == "pending"


def test_cli_ingest_exit_code_1_en_fallo_parcial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CA-12 (traducción de exit code, fallo parcial): si `IngestResult`
    tiene ≥ 1 ruta fallida (aquí, un archivo vacío junto a uno válido),
    `zlk ingest` retorna exit code `1`.
    """
    root_cli = tmp_path / "root_cli"
    root_cli.mkdir()
    _make_tenant(root_cli, "SANDUCHERIA")

    csv_valido = tmp_path / "ventas.csv"
    csv_valido.write_bytes(b"col_a,col_b\n1,2\n")
    csv_vacio = tmp_path / "vacio.csv"
    csv_vacio.write_bytes(b"")

    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(root_cli))
    exit_code = main(["ingest", "SANDUCHERIA", str(csv_valido), str(csv_vacio)])

    assert exit_code == 1

    tenant_cli = root_cli / "SANDUCHERIA"
    bronze_cli = tenant_cli / "data" / "bronze" / "ventas.csv"
    assert bronze_cli.is_file(), "el archivo válido debía ingerirse aunque hubiera un fallo parcial"

    manifest_cli = _read_manifest(tenant_cli)
    assert len(manifest_cli["files"]) == 1


def test_cli_ingest_exit_code_2_en_tenant_inexistente(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CA-12 (traducción de exit code, precondición global): si el tenant no
    existe (`TenantNotFoundError` en el core), `zlk ingest` retorna exit code
    `2` sin crear ni modificar ningún artefacto en disco.
    """
    root_cli = tmp_path / "root_cli"
    root_cli.mkdir()
    # Deliberadamente NO se crea el tenant SANDUCHERIA bajo root_cli.

    csv_path = tmp_path / "ventas.csv"
    csv_path.write_bytes(b"col_a,col_b\n1,2\n")

    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(root_cli))
    exit_code = main(["ingest", "SANDUCHERIA", str(csv_path)])

    assert exit_code == 2
    assert list(root_cli.iterdir()) == []
