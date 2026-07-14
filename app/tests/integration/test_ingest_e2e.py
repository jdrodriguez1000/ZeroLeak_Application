"""Prueba de integración end-to-end — TSK-25 (`integration_tester`, CA-01, CA-12).

Contexto (paso 11 del flujo, contexto fresco, independiente del bucle TDD):
el bucle TDD (Casos 1-12) ya ejercitó `ingest_paths` y `zeroleak.cli.main`
**en proceso** (import directo, `app/tests/test_ingest.py` y
`app/tests/test_cli_ingest.py`). Lo que falta y es responsabilidad de esta
suite es verificar la **costura real** CLI instalada -> proceso ->
disco, siguiendo el mismo patrón que
`app/tests/integration/test_client_new_e2e.py` (Tracer Bullet
`client_scaffold`):

- El comando de consola `zlk` (registrado vía `[project.scripts]` en
  `pyproject.toml`, instalado en el entorno virtual) se invoca por
  **subprocess** real, no por llamada Python en el mismo intérprete. Esto
  ejercita el punto de entrada tal como lo usaría el Científico de Datos en
  su terminal (`zlk ingest <CLIENTE> <ruta>...`), incluyendo el parseo real
  de `sys.argv`, la resolución de `ZEROLEAK_CLIENTS_ROOT` en el proceso hijo
  y los códigos de salida (`returncode`) del proceso completo.
- Se verifica el efecto **en disco real** (no monkeypatch, no mocks): copia
  byte a byte a `data/bronze/` y entrada `pending` en `data/manifest.json`
  (CA-01), procesamiento parcial con exit code 1 (CA-07), dedupe por
  contenido (CA-05), precondición global de tenant con exit code 2 (CA-08),
  y equivalencia de árbol/manifest entre la CLI instalada (subprocess) y el
  core (`ingest_paths`) invocado en proceso (CA-12).

Regla "Datos en Bóveda" (C-01): todos los `clients_root` viven en `tmp_path`
(aislados por pytest); todos los nombres de tenant y contenidos de archivo
son sintéticos (`SANDUCHERIA_E2E`, `ventas.csv`, etc.). No se toca
`clients/` real ni datos de ningún cliente.

Independencia (P1/P3): los asertos de esta suite se derivan de
`610_features/ingest/spec.md` (CA-01, CA-05, CA-07, CA-08, CA-12), no de la
implementación de `core.py`/`cli.py`. Si algún aserto falla, es un hallazgo
de integración a reportar de vuelta al bucle TDD (`tdd_tester`/`tdd_coder`);
esta suite no modifica `app/src/zeroleak/...`.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from zeroleak.ingest.core import ingest_paths


def _zlk_executable() -> str:
    """Localiza el comando `zlk` instalado en el mismo entorno virtual que
    ejecuta pytest (`sys.executable`), sin asumir un layout de proyecto
    concreto (Windows Scripts/ vs POSIX bin/).
    """
    venv_scripts_dir = Path(sys.executable).parent
    candidate = venv_scripts_dir / (
        "zlk.exe" if sys.platform.startswith("win") else "zlk"
    )
    if candidate.exists():
        return str(candidate)

    found = shutil.which("zlk")
    if found:
        return found

    pytest.fail(
        "No se encontró el comando 'zlk' instalado (ni junto a "
        f"sys.executable={sys.executable!r} ni en PATH). La suite de "
        "integración requiere que el paquete esté instalado en el entorno "
        "(pip install -e .) antes de ejecutar pytest."
    )


ZLK = _zlk_executable()


def _run_zlk(args: list[str], clients_root: Path) -> subprocess.CompletedProcess:
    """Invoca `zlk` como proceso real (no en-proceso), con `clients_root`
    inyectado vía la variable de entorno de convención del contrato CLI.
    """
    env = dict(os.environ)
    env["ZEROLEAK_CLIENTS_ROOT"] = str(clients_root)
    return subprocess.run(
        [ZLK, *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _make_tenant(clients_root: Path, name: str) -> Path:
    """Crea manualmente la estructura mínima de tenant ingerible (mismo
    formato que produce `client_scaffold` y que exige la precondición global
    de `ingest_paths`, CA-08): `data/bronze/` + `data/manifest.json` inicial.
    """
    tenant_dir = clients_root / name
    (tenant_dir / "data" / "bronze").mkdir(parents=True)
    manifest_path = tenant_dir / "data" / "manifest.json"
    manifest_path.write_text(
        json.dumps({"version": 1, "files": []}, indent=2), encoding="utf-8"
    )
    return tenant_dir


def _read_manifest(tenant_dir: Path) -> dict:
    return json.loads(
        (tenant_dir / "data" / "manifest.json").read_text(encoding="utf-8")
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_zlk_ingest_subprocess_csv_valido_copia_a_bronze_y_agrega_entrada_pending(
    tmp_path: Path,
) -> None:
    """CA-01: `zlk ingest <CLIENTE> <archivo>.csv` ejecutado como proceso
    real retorna exit code 0, copia el archivo byte a byte a
    `data/bronze/<file>` y agrega una entrada `pending` con el `sha256`
    correcto en `data/manifest.json`.
    """
    clients_root = tmp_path / "clients_root_e2e_exito"
    clients_root.mkdir()
    tenant_dir = _make_tenant(clients_root, "SANDUCHERIA_E2E")

    csv_path = tmp_path / "ventas.csv"
    csv_bytes = b"producto,monto\nempanada,3500\n"
    csv_path.write_bytes(csv_bytes)

    result = _run_zlk(["ingest", "SANDUCHERIA_E2E", str(csv_path)], clients_root)

    assert result.returncode == 0, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    bronze_file = tenant_dir / "data" / "bronze" / "ventas.csv"
    assert bronze_file.is_file()
    assert bronze_file.read_bytes() == csv_bytes

    manifest = _read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1
    entry = manifest["files"][0]
    assert entry["file"] == "ventas.csv"
    assert entry["sha256"] == _sha256(csv_bytes)
    assert entry["status"] == "pending"


def test_zlk_ingest_subprocess_mezcla_valida_invalida_exit_code_1_procesamiento_parcial(
    tmp_path: Path,
) -> None:
    """CA-07: una invocación real con una ruta válida, una vacía, una con
    extensión fuera de allow-list y una inexistente ingiere solo la válida,
    retorna exit code 1 y no corrompe el manifest ni deja residuo de las
    rutas inválidas en bronze.
    """
    clients_root = tmp_path / "clients_root_e2e_parcial"
    clients_root.mkdir()
    tenant_dir = _make_tenant(clients_root, "SANDUCHERIA_E2E")

    csv_valido = tmp_path / "valido.csv"
    csv_valido.write_bytes(b"col_a,col_b\n1,2\n")
    csv_vacio = tmp_path / "vacio.csv"
    csv_vacio.write_bytes(b"")
    txt_no_permitido = tmp_path / "reporte.txt"
    txt_no_permitido.write_bytes(b"texto plano")
    ruta_inexistente = tmp_path / "no_existe.csv"

    result = _run_zlk(
        [
            "ingest",
            "SANDUCHERIA_E2E",
            str(csv_valido),
            str(csv_vacio),
            str(txt_no_permitido),
            str(ruta_inexistente),
        ],
        clients_root,
    )

    assert result.returncode == 1, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stderr.strip() != ""

    bronze_dir = tenant_dir / "data" / "bronze"
    bronze_files = sorted(p.name for p in bronze_dir.iterdir())
    assert bronze_files == ["valido.csv"]

    manifest = _read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["file"] == "valido.csv"


def test_zlk_ingest_subprocess_dedupe_reenvio_es_no_op_exit_0(
    tmp_path: Path,
) -> None:
    """CA-05: reenviar (en una segunda invocación real) un archivo cuyo
    `sha256` ya quedó registrado en el manifest es un no-op idempotente: no
    se agrega copia ni entrada nueva, y el proceso retorna exit code 0.
    """
    clients_root = tmp_path / "clients_root_e2e_dedupe"
    clients_root.mkdir()
    tenant_dir = _make_tenant(clients_root, "SANDUCHERIA_E2E")

    contenido = b"producto,monto\nempanada,3500\n"
    csv_original = tmp_path / "ventas.csv"
    csv_original.write_bytes(contenido)

    primero = _run_zlk(["ingest", "SANDUCHERIA_E2E", str(csv_original)], clients_root)
    assert primero.returncode == 0

    # Mismo contenido, nombre distinto -> el sha256 ya está en el manifest.
    csv_reenviado = tmp_path / "ventas_reenviada.csv"
    csv_reenviado.write_bytes(contenido)

    segundo = _run_zlk(
        ["ingest", "SANDUCHERIA_E2E", str(csv_reenviado)], clients_root
    )
    assert segundo.returncode == 0, (
        f"stdout={segundo.stdout!r} stderr={segundo.stderr!r}"
    )

    bronze_dir = tenant_dir / "data" / "bronze"
    assert sorted(p.name for p in bronze_dir.iterdir()) == ["ventas.csv"]

    manifest = _read_manifest(tenant_dir)
    assert len(manifest["files"]) == 1


def test_zlk_ingest_subprocess_tenant_inexistente_exit_code_2_sin_residuo(
    tmp_path: Path,
) -> None:
    """CA-08: invocar `zlk ingest` sobre un tenant que no existe (ni
    `data/bronze/` ni `data/manifest.json`) retorna exit code 2 por proceso
    real, imprime un mensaje por stderr y no deja ningún artefacto nuevo en
    `clients_root`.
    """
    clients_root = tmp_path / "clients_root_e2e_sin_tenant"
    clients_root.mkdir()
    # Deliberadamente NO se crea el tenant SANDUCHERIA_E2E.

    csv_path = tmp_path / "ventas.csv"
    csv_path.write_bytes(b"col_a,col_b\n1,2\n")

    result = _run_zlk(["ingest", "SANDUCHERIA_E2E", str(csv_path)], clients_root)

    assert result.returncode == 2, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stderr.strip() != ""
    assert list(clients_root.iterdir()) == []


def test_zlk_ingest_subprocess_arbol_y_manifest_identicos_al_core_import_directo(
    tmp_path: Path,
) -> None:
    """CA-12: el efecto en disco de `zlk ingest` ejecutado como proceso real
    (bronze + manifest) es idéntico —mismo nombre almacenado, mismos bytes,
    mismo `sha256`, mismo `status`— al producido por `ingest_paths` invocado
    directamente en este proceso de test sobre un `clients_root` gemelo,
    cerrando el círculo CLI-real <-> core para la feature `ingest`.
    """
    clients_root_cli = tmp_path / "clients_root_e2e_cli"
    clients_root_cli.mkdir()
    clients_root_core = tmp_path / "clients_root_e2e_core"
    clients_root_core.mkdir()

    tenant_cli = _make_tenant(clients_root_cli, "SANDUCHERIA_E2E")
    tenant_core = _make_tenant(clients_root_core, "SANDUCHERIA_E2E")

    csv_path = tmp_path / "ventas.csv"
    csv_path.write_bytes(b"producto,monto\nempanada,3500\n")

    result = _run_zlk(
        ["ingest", "SANDUCHERIA_E2E", str(csv_path)], clients_root_cli
    )
    assert result.returncode == 0

    result_core = ingest_paths("SANDUCHERIA_E2E", [str(csv_path)], clients_root_core)
    assert result_core.exit_code == 0

    bronze_cli = tenant_cli / "data" / "bronze" / "ventas.csv"
    bronze_core = tenant_core / "data" / "bronze" / "ventas.csv"
    assert bronze_cli.is_file()
    assert bronze_core.is_file()
    assert bronze_cli.read_bytes() == bronze_core.read_bytes()

    manifest_cli = _read_manifest(tenant_cli)
    manifest_core = _read_manifest(tenant_core)
    assert len(manifest_cli["files"]) == len(manifest_core["files"]) == 1
    assert manifest_cli["files"][0]["file"] == manifest_core["files"][0]["file"]
    assert manifest_cli["files"][0]["sha256"] == manifest_core["files"][0]["sha256"]
    assert manifest_cli["files"][0]["status"] == manifest_core["files"][0]["status"] == "pending"
