"""Fixtures sintéticas compartidas para los tests de ZeroLeak.

Regla "Datos en Bóveda" (C-01): todos los datos usados en los tests son
sintéticos. `clients_root` vive siempre en `tmp_path` (aislado por pytest),
nunca sobre datos reales de un cliente.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict

import pytest


@pytest.fixture
def clients_root(tmp_path: Path) -> Path:
    """Directorio raíz de tenants, limpio, aislado en `tmp_path`.

    TSK-01: fixture mínima que necesitan los tests de `create_client`.
    """
    root = tmp_path / "clients_root"
    root.mkdir()
    return root


@pytest.fixture
def tenant_snapshot() -> Callable[[Path], Dict[str, int]]:
    """Helper de snapshot del árbol de un tenant (rutas relativas + tamaños).

    TSK-01: usado por casos posteriores (p. ej. Caso 8, no idempotencia) para
    comparar el estado de un tenant antes/después de una operación. Devuelve
    un `dict` `{ruta_relativa_posix: tamaño_en_bytes}`; los directorios se
    representan con tamaño `-1` (no tienen tamaño de archivo propio) para
    poder detectar tanto adiciones/eliminaciones de directorios como cambios
    de contenido en archivos.
    """

    def _snapshot(tenant_dir: Path) -> Dict[str, int]:
        snapshot: Dict[str, int] = {}
        for path in tenant_dir.rglob("*"):
            rel = path.relative_to(tenant_dir).as_posix()
            snapshot[rel] = -1 if path.is_dir() else path.stat().st_size
        return snapshot

    return _snapshot


@pytest.fixture
def ingestible_tenant(
    clients_root: Path,
) -> Callable[[str], Path]:
    """Factory de tenant "ingerible" (TSK-01, feature `ingest`).

    Crea, bajo `clients_root` (sintético, en `tmp_path`), la estructura mínima
    que `ingest_paths` exige como precondición global de tenant: `data/bronze/`
    y `data/manifest.json` inicial `{"version": 1, "files": []}` (formato
    producido por `client_scaffold`). Devuelve la ruta del tenant creado.

    Usado por los casos del bucle TDD de `ingest` que necesitan un tenant
    existente y "vacío" de archivos ingeridos (p. ej. Caso 2 en adelante); el
    Caso 1 (CA-08, tenant inexistente) deliberadamente NO usa esta fixture.
    """

    def _make(name: str) -> Path:
        tenant_dir = clients_root / name
        (tenant_dir / "data" / "bronze").mkdir(parents=True)
        manifest_path = tenant_dir / "data" / "manifest.json"
        manifest_path.write_text(
            json.dumps({"version": 1, "files": []}, indent=2),
            encoding="utf-8",
        )
        return tenant_dir

    return _make


@pytest.fixture
def read_manifest() -> Callable[[Path], dict]:
    """Helper de lectura del `manifest.json` de un tenant (TSK-01).

    Recibe la ruta del tenant y devuelve el contenido parseado de
    `data/manifest.json` como `dict`.
    """

    def _read(tenant_dir: Path) -> dict:
        manifest_path = tenant_dir / "data" / "manifest.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    return _read
