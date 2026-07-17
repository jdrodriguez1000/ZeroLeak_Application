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
