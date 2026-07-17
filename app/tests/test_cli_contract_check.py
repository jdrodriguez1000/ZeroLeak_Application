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
from unittest import mock

import pytest

import zeroleak.cli as zeroleak_cli
from zeroleak.cli import main
from zeroleak.config import ContractSchemaError, load_contract
from zeroleak.config.contract import _MENSAJE_COLUMNAS_VACIA


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


def test_contract_check_tenant_sin_contrato_exit_2_stderr_f03(
    clients_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 4 / TSK-10 (CA-09): `<CLIENTE>` que existe como directorio bajo
    `clients_root` pero **sin** `input/contract_data.yaml` -> `main(["contract",
    "check", C])` retorna exactamente `2` (el **mismo** código que el Caso 3,
    tenant inexistente) y stderr es **exactamente** F-03:
    `El tenant 'SIN_CONTRATO' no tiene contrato: falta <ruta>` (con la ruta
    resuelta del YAML ausente). stderr no debe contener `Traceback` ni
    `FileNotFoundError`: el motor (`load_contract`, `contract.py:213`) hace
    `open(path)` sin capturar `FileNotFoundError`, así que si la fachada
    invocara el motor sin comprobar antes la precondición del contrato, este
    test capturaría el traceback sin controlar en vez del mensaje F-03.
    """
    tenant_dir = clients_root / "SIN_CONTRATO"
    tenant_dir.mkdir(parents=True)
    ruta = tenant_dir / "input" / "contract_data.yaml"
    assert tenant_dir.is_dir()
    assert not ruta.exists()

    exit_code = main(["contract", "check", "SIN_CONTRATO"])

    captured = capsys.readouterr()
    assert exit_code == 2, (
        f"tenant sin contrato debe retornar exit 2 (mismo código que el "
        f"tenant inexistente); obtenido: {exit_code!r}; stderr: {captured.err!r}"
    )
    assert captured.out == "", (
        f"tenant sin contrato debe dejar stdout vacío; obtenido: {captured.out!r}"
    )
    esperado = f"El tenant 'SIN_CONTRATO' no tiene contrato: falta {ruta}\n"
    assert captured.err == esperado, (
        f"stderr debe ser exactamente F-03; esperado: {esperado!r}; "
        f"obtenido: {captured.err!r}"
    )
    assert "Traceback" not in captured.err, (
        f"stderr no debe contener un traceback sin controlar; obtenido: {captured.err!r}"
    )
    assert "FileNotFoundError" not in captured.err, (
        f"stderr no debe filtrar el nombre de la excepción del motor; "
        f"obtenido: {captured.err!r}"
    )


def test_contract_check_f02_distinto_de_f03(
    clients_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 4 / TSK-10 (CA-09): mismo exit code `2` para las dos
    precondiciones (tenant ausente y contrato ausente), pero los mensajes de
    stderr son **distintos entre sí** (F-02 != F-03): el código no basta
    para distinguirlos, hay que mirar el texto.
    """
    tenant_sin_contrato = clients_root / "SIN_CONTRATO_2"
    tenant_sin_contrato.mkdir(parents=True)

    exit_code_inexistente = main(["contract", "check", "FANTASMA_2"])
    stderr_inexistente = capsys.readouterr().err

    exit_code_sin_contrato = main(["contract", "check", "SIN_CONTRATO_2"])
    stderr_sin_contrato = capsys.readouterr().err

    assert exit_code_inexistente == 2
    assert exit_code_sin_contrato == 2
    assert stderr_inexistente != stderr_sin_contrato, (
        "F-02 (tenant inexistente) y F-03 (contrato ausente) deben ser "
        f"mensajes distintos aunque compartan exit code 2; "
        f"F-02={stderr_inexistente!r}; F-03={stderr_sin_contrato!r}"
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


def test_contract_check_precondiciones_no_invocan_el_motor(
    clients_root: Path,
    tenant_con_contrato: Callable[..., Path],
    archivos_dos_archivos: list[dict],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 5 / TSK-12 (CA-10): parcheando `load_contract` en el namespace de
    `zeroleak.cli` con un doble que registra sus llamadas, invocar el comando
    sobre (a) un tenant inexistente y (b) un tenant sin contrato deja el
    doble con **0 llamadas** en ambos casos, y ambas invocaciones retornan
    `2` sin propagar excepción: la fachada nunca llega a tocar el motor
    cuando una precondición falla.

    Guarda de no-vacuidad (L-17): el mismo doble, sobre un tenant **con**
    contrato, registra **exactamente 1** llamada con la ruta del YAML — si
    el parche estuviera mal instalado (p. ej. importado por valor en vez de
    por nombre en el módulo `cli`), esta última aserción fallaría también en
    el caso de éxito, delatando un doble mudo.
    """
    tenant_con_contrato("PANADERIA_CON_CONTRATO", archivos=archivos_dos_archivos)
    ruta_contrato = (
        clients_root / "PANADERIA_CON_CONTRATO" / "input" / "contract_data.yaml"
    )
    tenant_sin_contrato = clients_root / "SIN_CONTRATO_CASO5"
    tenant_sin_contrato.mkdir(parents=True)

    with mock.patch.object(
        zeroleak_cli, "load_contract", wraps=zeroleak_cli.load_contract
    ) as doble:
        exit_code_inexistente = main(["contract", "check", "FANTASMA_CASO5"])
        assert exit_code_inexistente == 2
        assert doble.call_count == 0, (
            "load_contract no debe invocarse cuando el tenant no existe "
            f"(precondición 1); llamadas registradas: {doble.call_count}"
        )

        exit_code_sin_contrato = main(["contract", "check", "SIN_CONTRATO_CASO5"])
        assert exit_code_sin_contrato == 2
        assert doble.call_count == 0, (
            "load_contract no debe invocarse cuando el tenant no tiene "
            f"contrato (precondición 2); llamadas registradas: {doble.call_count}"
        )

        # Guarda de no-vacuidad (L-17): el doble sí se usa cuando el
        # contrato existe -- si no, "0 llamadas" arriba no probaría nada.
        exit_code_valido = main(["contract", "check", "PANADERIA_CON_CONTRATO"])
        assert exit_code_valido == 0
        assert doble.call_count == 1, (
            "guarda de no-vacuidad: el doble debe registrar exactamente 1 "
            "llamada cuando el contrato sí existe, o el instrumento está "
            f"muerto; llamadas registradas: {doble.call_count}"
        )
        doble.assert_called_once_with(ruta_contrato)


def test_contract_check_schema_verbatim_exit_4(
    clients_root: Path,
    tenant_con_contrato: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 6 / TSK-14 (CA-03): propiedad verbatim (esquema).

    Para un tenant cuyo `contract_data.yaml` viola el esquema (`archivos: []`,
    M-04), se compara el **mismo archivo** por dos caminos: `str(exc)`
    capturado invocando `load_contract(ruta)` **directo**, y el `stderr` del
    comando `main(["contract","check",C])`. La propiedad exigida es la
    igualdad exacta `stderr.strip() == str(exc)` -- ni prefijo, ni sufijo, ni
    reformato de la fachada (variante A, resolución del gate del paso 5) --
    además de `stdout == ""` y exit code `4`.
    """
    texto_yaml = "contract_data:\n  archivos: []\n"
    tenant_con_contrato("PANADERIA_ESQUEMA_INVALIDO", texto=texto_yaml)
    ruta = clients_root / "PANADERIA_ESQUEMA_INVALIDO" / "input" / "contract_data.yaml"
    assert ruta.is_file()

    with pytest.raises(ContractSchemaError) as excinfo:
        load_contract(ruta)
    mensaje_motor = str(excinfo.value)

    exit_code = main(["contract", "check", "PANADERIA_ESQUEMA_INVALIDO"])

    captured = capsys.readouterr()
    assert exit_code == 4, (
        f"YAML que viola el esquema debe retornar exit 4; obtenido: "
        f"{exit_code!r}; stderr: {captured.err!r}"
    )
    assert captured.out == "", (
        f"contract check en fallo de esquema debe dejar stdout vacío; "
        f"obtenido: {captured.out!r}"
    )
    assert captured.err.strip() == mensaje_motor, (
        "stderr del comando debe ser IGUAL, sin ninguna alteración, al "
        "mensaje que produce load_contract invocado directamente sobre el "
        f"mismo archivo;\nmotor: {mensaje_motor!r}\ncomando: {captured.err!r}"
    )


def test_contract_check_m07_exacto_por_la_fachada(
    tenant_con_contrato: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Caso 7 / TSK-16 (CA-04): mensaje concreto (esquema), M-07.

    `archivos[1]` (`ventas.csv`) declara `columnas: []` (lista vacía
    explícita, no ausente): el motor rechaza esto con M-07
    (`_columnas_no_vacias`, `contract.py`), localizado como
    `archivo[1] 'ventas.csv'` (D-25a). El stderr del comando debe ser
    **exactamente** ese texto compuesto -- comparado por **igualdad exacta
    contra la constante congelada `_MENSAJE_COLUMNAS_VACIA`** importada del
    motor (`zeroleak.config.contract`), nunca recopiada como literal en este
    archivo (sección "Dependencias y Contratos" del plan): si el motor
    cambiara el texto de M-07, la regresión aparecería ahí, no aquí.

    Es también la prueba de que la fachada **no tiene rama especial** para
    este error: lo traduce con la misma rama `except ContractSchemaError`
    genérica que ya cubre el Caso 6 (CA-03).
    """
    texto_yaml = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - nombre: ventas.csv\n"
        "      columnas: []\n"
    )
    tenant_con_contrato("PANADERIA_M07", texto=texto_yaml)

    exit_code = main(["contract", "check", "PANADERIA_M07"])

    captured = capsys.readouterr()
    esperado = f"archivo[1] 'ventas.csv': {_MENSAJE_COLUMNAS_VACIA}"
    assert exit_code == 4, (
        f"columnas vacías en archivos[1] debe retornar exit 4; obtenido: "
        f"{exit_code!r}; stderr: {captured.err!r}"
    )
    assert captured.out == "", (
        f"contract check en fallo de esquema debe dejar stdout vacío; "
        f"obtenido: {captured.out!r}"
    )
    assert captured.err.strip() == esperado, (
        "stderr debe ser exactamente M-07 (igualdad exacta contra la "
        f"constante del motor);\nesperado: {esperado!r}\n"
        f"obtenido: {captured.err!r}"
    )
