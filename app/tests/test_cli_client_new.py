"""Tests de la fachada CLI `zlk client new <NOMBRE>` — TSK-17 (Caso 9, CA-02)
y TSK-19 (Caso 10, CA-02).

Contrato esperado de la fachada (fijado por `tdd_tester` para que `tdd_coder`
lo implemente en la fase GREEN):

- `zeroleak.cli.main(argv: list[str] | None = None) -> int` es el punto de
  entrada invocable desde Python (usado tanto por `[project.scripts] zlk =
  "zeroleak.cli:main"` como por los tests). Si `argv` es `None`, se usa
  `sys.argv[1:]` (comportamiento estándar de CLI); en los tests se pasa
  explícitamente la lista de argumentos, p. ej.
  `main(["client", "new", "SANDUCHERIA"])`.
- Resolución de `clients_root` (decisión de convención, TSK-17): la CLI lee
  la variable de entorno `ZEROLEAK_CLIENTS_ROOT` y usa su valor como
  `clients_root` (convertido a `Path`). Se elige variable de entorno en vez
  de `cwd`/flag porque no obliga a cambiar el directorio de trabajo del
  proceso de test y es la forma más simple y explícita de inyectar la raíz
  de tenants en un entorno de test aislado (`tmp_path`). `tdd_coder` debe
  implementar exactamente esta convención en `cli.py`.
- En éxito, `main` retorna `0` e imprime en stdout una línea que contiene la
  ruta absoluta del tenant creado (p. ej. `str(tenant_path)` en alguna parte
  de la salida).
- La CLI no contiene lógica de negocio propia: delega en
  `zeroleak.core.scaffold.create_client`, de modo que el árbol de archivos
  creado por la CLI es idéntico al creado por una llamada directa al core.

Regla "Datos en Bóveda" (C-01): `clients_root` vive siempre en `tmp_path`;
nombre de prueba sintético `SANDUCHERIA`.
"""
from __future__ import annotations

import pytest

from pathlib import Path
from typing import Callable, Dict

from zeroleak.cli import main
from zeroleak.core.scaffold import create_client


def test_cli_client_new_crea_estructura_y_reporta_ruta(
    tmp_path: Path,
    capsys: "object",
    tenant_snapshot: Callable[[Path], Dict[str, int]],
) -> None:
    """Caso 9 / TSK-17 (CA-02): `zlk client new SANDUCHERIA` crea en disco la
    misma estructura que `create_client` (llamada directa) y reporta la ruta
    del tenant creado por stdout.
    """
    # clients_root de la CLI: convención elegida = variable de entorno
    # ZEROLEAK_CLIENTS_ROOT, aislada en tmp_path (C-01).
    import os

    cli_root = tmp_path / "clients_root_cli"
    cli_root.mkdir()
    os.environ["ZEROLEAK_CLIENTS_ROOT"] = str(cli_root)
    try:
        exit_code = main(["client", "new", "SANDUCHERIA"])
    finally:
        del os.environ["ZEROLEAK_CLIENTS_ROOT"]

    assert exit_code == 0

    captured = capsys.readouterr()
    tenant_path_cli = cli_root / "SANDUCHERIA"
    assert str(tenant_path_cli) in captured.out

    assert tenant_path_cli.exists()

    # El core, invocado directamente sobre un clients_root gemelo, debe
    # producir el mismo árbol relativo (delegación sin lógica propia, CA-02).
    core_root = tmp_path / "clients_root_core"
    core_root.mkdir()
    tenant_path_core = create_client("SANDUCHERIA", core_root)

    assert tenant_snapshot(tenant_path_cli).keys() == tenant_snapshot(
        tenant_path_core
    ).keys()


def test_cli_client_new_exit_codes_distintos(
    tmp_path: Path,
    capsys: "object",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Caso 10 / TSK-19 (CA-02): la fachada `zlk client new` traduce las
    excepciones de dominio del core a **exit codes distintos**, sin propagar
    la excepción cruda a quien invoca `main` (contrato fijado por
    `tdd_tester` para que `tdd_coder` lo implemente en TSK-20):

    - `0` — éxito (alta creada; ya cubierto por el Caso 9).
    - `2` — nombre inválido (`ClientNameError` del core).
    - `3` — tenant ya existente (`TenantExistsError` del core).
    - `1` queda reservado para errores inesperados no de dominio (no
      ejercido por este test).

    En los casos de error, `main` debe imprimir un mensaje claro por
    **stderr** (no stdout, para no mezclarse con la ruta que se imprime en
    éxito) y no debe dejar residuo en `clients_root` (ni tenant parcial ni
    `.staging-*`), igual que el core (CA-04/CA-06).

    Regla "Datos en Bóveda" (C-01): `clients_root` vive en `tmp_path`;
    nombres sintéticos `SANDUCHERIA` / `cli/ente`.
    """
    root = tmp_path / "clients_root_exit_codes"
    root.mkdir()
    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(root))

    # 1) Éxito -> 0.
    exit_code_ok = main(["client", "new", "SANDUCHERIA"])
    assert exit_code_ok == 0
    assert (root / "SANDUCHERIA").exists()

    # 2) Nombre inválido -> 2 (ClientNameError traducida, sin excepción
    #    cruda propagada y sin residuo en clients_root).
    entries_antes_invalido = set(root.iterdir())
    exit_code_invalido = main(["client", "new", "cli/ente"])
    assert exit_code_invalido == 2

    captured_invalido = capsys.readouterr()
    assert captured_invalido.err.strip() != ""

    entries_despues_invalido = set(root.iterdir())
    assert entries_despues_invalido == entries_antes_invalido
    assert not any(p.name.startswith(".staging") for p in root.iterdir())

    # 3) Tenant existente -> 3 (TenantExistsError traducida; el tenant
    #    SANDUCHERIA creado en el paso 1 permanece intacto).
    exit_code_existente = main(["client", "new", "SANDUCHERIA"])
    assert exit_code_existente == 3

    captured_existente = capsys.readouterr()
    assert captured_existente.err.strip() != ""

    assert not any(p.name.startswith(".staging") for p in root.iterdir())


def test_create_client_import_directo_y_cli_producen_arbol_identico(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tenant_snapshot: Callable[[Path], Dict[str, int]],
) -> None:
    """Caso 11 / TSK-21 (CA-03): el resultado en disco de `create_client`
    (import directo) es **idéntico** al de `zlk client new` — mismo conjunto
    de rutas relativas Y mismo contenido byte-a-byte de cada archivo.

    La CLI no contiene lógica de negocio propia (delega en el core), por lo
    que se espera que este test pase de inmediato; sirve como red de
    seguridad de la equivalencia core<->CLI (si la CLI alguna vez divergiera
    -- p. ej. escribiendo contenido distinto o una ruta distinta -- este
    test lo detectaría).

    Regla "Datos en Bóveda" (C-01): dos `clients_root` gemelos, ambos en
    `tmp_path`; nombre de prueba sintético `SANDUCHERIA`.
    """
    root_core = tmp_path / "root_core"
    root_core.mkdir()
    root_cli = tmp_path / "root_cli"
    root_cli.mkdir()

    # Import directo del core.
    tenant_core = create_client("SANDUCHERIA", root_core)

    # Misma alta vía la fachada CLI, sobre un clients_root gemelo.
    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(root_cli))
    exit_code = main(["client", "new", "SANDUCHERIA"])
    assert exit_code == 0
    tenant_cli = root_cli / "SANDUCHERIA"

    # 1) Mismo conjunto de rutas relativas (estructura idéntica).
    snapshot_core = tenant_snapshot(tenant_core)
    snapshot_cli = tenant_snapshot(tenant_cli)
    assert snapshot_core.keys() == snapshot_cli.keys()

    # 2) Mismo contenido byte-a-byte de cada archivo (no solo mismo tamaño).
    for rel_path in snapshot_core:
        path_core = tenant_core / rel_path
        path_cli = tenant_cli / rel_path
        if path_core.is_dir():
            assert path_cli.is_dir()
            continue
        assert path_cli.is_file()
        assert path_core.read_bytes() == path_cli.read_bytes(), (
            f"Contenido divergente en {rel_path!r} entre core y CLI"
        )
