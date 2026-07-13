"""Prueba de integración end-to-end — TSK-25 (`integration_tester`, CA-01, CA-02).

Contexto (paso 11 del flujo, contexto fresco, independiente del bucle TDD):
el bucle TDD (Casos 1-13) ya ejercitó `create_client` y `zeroleak.cli.main`
**en proceso** (import directo). Lo que falta y es responsabilidad de esta
suite es verificar la **costura real** CLI instalada -> proceso -> disco:

- El comando de consola `zlk` (registrado vía `[project.scripts]` en
  `pyproject.toml`, instalado en el entorno virtual `.venv`) se invoca por
  **subprocess** real, no por llamada Python en el mismo intérprete. Esto
  ejercita el punto de entrada tal como lo usaría el Científico de Datos en
  su terminal (`zlk client new <NOMBRE>`), incluyendo el parseo real de
  `sys.argv`, la resolución de variables de entorno del proceso hijo y los
  códigos de salida (`returncode`) del proceso completo.
- Se verifica el árbol de archivos resultante **en disco real** (no
  monkeypatch, no mocks): estructura canónica completa (CA-01), YAMLs
  parseables, manifest, aislamiento `data/` vs versionable, exit codes
  distintos (CA-02), no idempotencia y equivalencia con `create_client`
  (import directo del core, para cerrar el círculo CLI<->core sin asumir
  nada del coder salvo el contrato observable de la spec).

Regla "Datos en Bóveda" (C-01): todos los `clients_root` viven en `tmp_path`
(aislados por pytest); todos los nombres de tenant son sintéticos
(`SANDUCHERIA_E2E`, `TENANT_E2E_*`). No se toca `clients/` real ni datos de
ningún cliente.

Independencia (P1/P3): los asertos de esta suite se derivan de
`610_features/client_scaffold/spec.md` (CA-01, CA-02, CA-04, CA-06, CA-07,
CA-08, CA-09), no de la implementación de `scaffold.py`/`cli.py`. Si algún
aserto falla, es un hallazgo de integración a reportar de vuelta al bucle
TDD; esta suite no modifica `app/src/zeroleak/...`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict

import pytest
import yaml

from zeroleak.core.scaffold import create_client


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
    import os

    env = dict(os.environ)
    env["ZEROLEAK_CLIENTS_ROOT"] = str(clients_root)
    return subprocess.run(
        [ZLK, *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_zlk_client_new_subprocess_exito_crea_estructura_canonica_completa(
    tmp_path: Path,
) -> None:
    """CA-01, CA-02: `zlk client new <NOMBRE>` ejecutado como proceso real
    retorna exit code 0, reporta la ruta creada por stdout, y materializa en
    disco la estructura canónica completa del tenant.
    """
    clients_root = tmp_path / "clients_root_e2e_exito"
    clients_root.mkdir()

    result = _run_zlk(["client", "new", "SANDUCHERIA_E2E"], clients_root)

    assert result.returncode == 0, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    tenant_dir = clients_root / "SANDUCHERIA_E2E"
    assert str(tenant_dir) in result.stdout

    # Estructura canónica completa (CA-01).
    assert (tenant_dir / "client.yaml").is_file()
    assert (tenant_dir / "input" / "contract_data.yaml").is_file()
    assert (tenant_dir / "input" / "business_rules.yaml").is_file()
    assert (tenant_dir / "input" / "finance.yaml").is_file()
    assert (tenant_dir / "data" / "bronze").is_dir()
    assert (tenant_dir / "data" / "silver").is_dir()
    assert (tenant_dir / "data" / "gold").is_dir()
    assert (tenant_dir / "data" / "manifest.json").is_file()

    # Sin residuo de staging tras un alta exitosa.
    assert not any(p.name.startswith(".staging") for p in clients_root.iterdir())

    # CA-08: manifest inicial válido.
    manifest = json.loads((tenant_dir / "data" / "manifest.json").read_text())
    assert manifest == {"version": 1, "files": []}

    # CA-08: directorios medallion vacíos.
    assert list((tenant_dir / "data" / "bronze").iterdir()) == []
    assert list((tenant_dir / "data" / "silver").iterdir()) == []
    assert list((tenant_dir / "data" / "gold").iterdir()) == []

    # CA-07: YAMLs parseables, con claves esperadas vacías y comentario guía;
    # sin datos reales/sensibles.
    client_yaml_text = (tenant_dir / "client.yaml").read_text(encoding="utf-8")
    assert "#" in client_yaml_text
    client_yaml = yaml.safe_load(client_yaml_text) or {}
    for key in ("client_id", "display_name", "sector_id", "created_at"):
        assert key in client_yaml
        assert not client_yaml[key]

    for input_file in ("contract_data.yaml", "business_rules.yaml", "finance.yaml"):
        text = (tenant_dir / "input" / input_file).read_text(encoding="utf-8")
        assert "#" in text
        # yaml.safe_load no debe lanzar excepción (sintácticamente válido).
        yaml.safe_load(text)


def test_zlk_client_new_subprocess_nombre_invalido_exit_code_2_sin_residuo(
    tmp_path: Path,
) -> None:
    """CA-02, CA-04: un nombre inválido invocado por el comando instalado
    retorna exit code 2, imprime un mensaje por stderr y no deja ningún
    artefacto nuevo en `clients_root` (ni tenant parcial ni `.staging`).
    """
    clients_root = tmp_path / "clients_root_e2e_invalido"
    clients_root.mkdir()

    entries_antes = set(clients_root.iterdir())

    result = _run_zlk(["client", "new", "cli/ente"], clients_root)

    assert result.returncode == 2, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stderr.strip() != ""

    entries_despues = set(clients_root.iterdir())
    assert entries_despues == entries_antes


def test_zlk_client_new_subprocess_tenant_existente_exit_code_3_no_modifica(
    tmp_path: Path,
    tenant_snapshot: Callable[[Path], Dict[str, int]],
) -> None:
    """CA-02, CA-06: reintentar `zlk client new` sobre un tenant ya existente
    retorna exit code 3 por proceso real, imprime un mensaje por stderr y el
    tenant existente queda intacto (snapshot idéntico antes/después).
    """
    clients_root = tmp_path / "clients_root_e2e_existente"
    clients_root.mkdir()

    primero = _run_zlk(["client", "new", "TENANT_E2E_DUP"], clients_root)
    assert primero.returncode == 0

    tenant_dir = clients_root / "TENANT_E2E_DUP"
    snapshot_antes = tenant_snapshot(tenant_dir)

    segundo = _run_zlk(["client", "new", "TENANT_E2E_DUP"], clients_root)

    assert segundo.returncode == 3, (
        f"stdout={segundo.stdout!r} stderr={segundo.stderr!r}"
    )
    assert segundo.stderr.strip() != ""

    snapshot_despues = tenant_snapshot(tenant_dir)
    assert snapshot_antes == snapshot_despues
    assert not any(p.name.startswith(".staging") for p in clients_root.iterdir())


def test_zlk_client_new_subprocess_arbol_identico_al_core_import_directo(
    tmp_path: Path,
    tenant_snapshot: Callable[[Path], Dict[str, int]],
) -> None:
    """CA-02, CA-03: el árbol producido por el comando instalado ejecutado
    como proceso real es idéntico (mismas rutas relativas y mismo contenido
    byte-a-byte) al producido por `create_client` invocado directamente en
    este proceso de test, cerrando el círculo CLI-real <-> core.
    """
    clients_root_cli = tmp_path / "clients_root_e2e_cli"
    clients_root_cli.mkdir()
    clients_root_core = tmp_path / "clients_root_e2e_core"
    clients_root_core.mkdir()

    result = _run_zlk(["client", "new", "TENANT_E2E_PARIDAD"], clients_root_cli)
    assert result.returncode == 0

    tenant_cli = clients_root_cli / "TENANT_E2E_PARIDAD"
    tenant_core = create_client("TENANT_E2E_PARIDAD", clients_root_core)

    snapshot_cli = tenant_snapshot(tenant_cli)
    snapshot_core = tenant_snapshot(tenant_core)
    assert snapshot_cli.keys() == snapshot_core.keys()

    for rel_path in snapshot_cli:
        path_cli = tenant_cli / rel_path
        path_core = tenant_core / rel_path
        if path_cli.is_dir():
            assert path_core.is_dir()
            continue
        assert path_core.is_file()
        assert path_cli.read_bytes() == path_core.read_bytes(), (
            f"Contenido divergente en {rel_path!r} entre CLI (subprocess) y core"
        )
