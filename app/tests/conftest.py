"""Fixtures sintéticas compartidas para los tests de ZeroLeak.

Regla "Datos en Bóveda" (C-01): todos los datos usados en los tests son
sintéticos. `clients_root` vive siempre en `tmp_path` (aislado por pytest),
nunca sobre datos reales de un cliente.
"""
from __future__ import annotations

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
