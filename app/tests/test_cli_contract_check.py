"""Tests de la fachada CLI `zlk contract check <CLIENTE>` — TSK-03 (Caso 1,
CA-01) y sucesivos (Casos 2..21 de `610_features/contract_check/plan.md`).

Contrato esperado (fijado por `tdd_tester` para que `tdd_coder` lo implemente
en la fase GREEN, TSK-05 en adelante):

- `zeroleak.cli.main(["contract", "check", "<CLIENTE>"])` resuelve
  `<clients_root>/<CLIENTE>/input/contract_data.yaml` por la convención
  vigente (`_clients_root()`), invoca `load_contract` (motor de
  `contract_multifile`, sin modificarlo, CA-19) y traduce su veredicto a
  exit code: `0` éxito, `2` precondición (tenant o contrato ausente), `3`
  `ContractParseError`, `4` `ContractSchemaError`.
- Camino feliz (este archivo, Caso 1 / CA-01): con un tenant sintético cuyo
  `input/contract_data.yaml` declara 2 archivos válidos (`clientes.csv`,
  `ventas.csv`), `main([...])` retorna exactamente `0`, escribe en stdout un
  texto no vacío y deja **stderr vacío**.

Regla "Datos en Bóveda" (C-01): `clients_root` vive siempre en `tmp_path`
(fixture `clients_root`, vía `tenant_con_contrato`); vocabulario sintético
(`clientes.csv`, `ventas.csv`; columnas `cliente_id`, `correo`, `alta`,
`venta_id`, `monto`), sin PII real.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pytest

from zeroleak.cli import main


@pytest.fixture(autouse=True)
def _clients_root_env(clients_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fija `ZEROLEAK_CLIENTS_ROOT` a la fixture `clients_root` del tests
    (misma convención que `test_cli_client_new.py` / `test_cli_ingest.py`),
    para que `_clients_root()` resuelva exactamente el árbol sintético de
    este archivo.
    """
    monkeypatch.setenv("ZEROLEAK_CLIENTS_ROOT", str(clients_root))


def test_contract_check_contrato_valido_dos_archivos_exit_0(
    tenant_con_contrato: Callable[..., Path],
    archivos_dos_archivos: list[dict],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 1 / TSK-03 (CA-01): tenant con contrato válido de 2 archivos
    (`clientes.csv`, `ventas.csv`) -> `main(["contract","check",C])` retorna
    exactamente `0`, stdout no vacío, stderr vacío.
    """
    tenant_con_contrato("PANADERIA", archivos=archivos_dos_archivos)

    exit_code = main(["contract", "check", "PANADERIA"])

    captured = capsys.readouterr()
    assert exit_code == 0, (
        f"contract check sobre un tenant con contrato válido debe retornar "
        f"exit 0; obtenido: {exit_code!r}; stderr: {captured.err!r}"
    )
    assert captured.out != "", (
        "contract check en éxito debe escribir un mensaje no vacío en stdout"
    )
    assert captured.err == "", (
        f"contract check en éxito debe dejar stderr vacío; obtenido: {captured.err!r}"
    )


def test_contract_check_stdout_f01_exacto_dos_archivos(
    clients_root: Path,
    tenant_con_contrato: Callable[..., Path],
    archivos_dos_archivos: list[dict],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 2 / TSK-06 (CA-02): con un contrato válido de 2 archivos, stdout
    es **exactamente** F-01: línea 1 `OK  contrato válido: <C> — <ruta>`
    (dos espacios tras `OK`, guion largo U+2014 rodeado de espacios,
    `<ruta> == str(clients_root/<C>/input/contract_data.yaml)`), línea 2
    `    2 archivo(s) declarado(s): clientes.csv, ventas.csv` (4 espacios de
    indentación, recuento y nombres en el orden declarado). Igualdad exacta
    contra el texto completo, no subcadena.
    """
    tenant_con_contrato("PANADERIA", archivos=archivos_dos_archivos)
    ruta = clients_root / "PANADERIA" / "input" / "contract_data.yaml"

    exit_code = main(["contract", "check", "PANADERIA"])

    captured = capsys.readouterr()
    esperado = (
        "OK  contrato válido: PANADERIA — " + str(ruta) + "\n"
        "    2 archivo(s) declarado(s): clientes.csv, ventas.csv\n"
    )
    assert exit_code == 0
    assert captured.out == esperado, (
        f"stdout de contract check debe ser exactamente F-01;\n"
        f"esperado: {esperado!r}\nobtenido: {captured.out!r}"
    )


def test_contract_check_tenant_inexistente_exit_2_stderr_f02(
    clients_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 3 / TSK-08 (CA-08): `<CLIENTE>` que no existe bajo `clients_root`
    (deliberadamente NO se crea ningún tenant `FANTASMA`) -> `main(["contract",
    "check", C])` retorna exactamente `2`, deja stdout vacío y stderr es
    **exactamente** F-02: `Tenant inexistente o incompleto: 'FANTASMA'`
    (`{client!r}`). Además, stderr no debe contener `Traceback` ni
    `FileNotFoundError`: el motor (`load_contract`, `contract.py:213`) hace
    `open(path)` sin capturar `FileNotFoundError`, así que si la fachada
    invocara el motor sin comprobar antes la precondición del tenant, este
    test capturaría el traceback sin controlar en vez del mensaje F-02.
    """
    assert not (clients_root / "FANTASMA").exists()

    exit_code = main(["contract", "check", "FANTASMA"])

    captured = capsys.readouterr()
    assert exit_code == 2, (
        f"tenant inexistente debe retornar exit 2; obtenido: {exit_code!r}; "
        f"stderr: {captured.err!r}"
    )
    assert captured.out == "", (
        f"tenant inexistente debe dejar stdout vacío; obtenido: {captured.out!r}"
    )
    assert captured.err == "Tenant inexistente o incompleto: 'FANTASMA'\n", (
        f"stderr debe ser exactamente F-02; obtenido: {captured.err!r}"
    )
    assert "Traceback" not in captured.err, (
        f"stderr no debe contener un traceback sin controlar; obtenido: {captured.err!r}"
    )
    assert "FileNotFoundError" not in captured.err, (
        f"stderr no debe filtrar el nombre de la excepción del motor; "
        f"obtenido: {captured.err!r}"
    )


def test_contract_check_stdout_f01_exacto_un_archivo(
    clients_root: Path,
    tenant_con_contrato: Callable[..., Path],
    archivos_un_archivo: list[dict],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 2 / TSK-06 (CA-02), variante de **un solo** archivo: la segunda
    línea de F-01 usa singular numérico correcto en la redacción congelada
    (`1 archivo(s) declarado(s): <nombre>` -- la forma `archivo(s)` no
    cambia con el número, solo cambia el recuento y el listado de nombres).
    """
    tenant_con_contrato("PANADERIA", archivos=archivos_un_archivo)
    ruta = clients_root / "PANADERIA" / "input" / "contract_data.yaml"

    exit_code = main(["contract", "check", "PANADERIA"])

    captured = capsys.readouterr()
    esperado = (
        "OK  contrato válido: PANADERIA — " + str(ruta) + "\n"
        "    1 archivo(s) declarado(s): clientes.csv\n"
    )
    assert exit_code == 0
    assert captured.out == esperado, (
        f"stdout de contract check (1 archivo) debe ser exactamente F-01;\n"
        f"esperado: {esperado!r}\nobtenido: {captured.out!r}"
    )
