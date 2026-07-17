"""Fachada CLI del Científico de Datos: comando `zlk`.

Es la primera fachada del motor (system_design §2.5, §4); mañana el frontend
web del SaaS será otra fachada sobre el mismo motor. Aquí vive únicamente el
despacho de subcomandos hacia `zeroleak.core.scaffold`, sin lógica de
negocio propia (CA-02, CA-03).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from zeroleak.config import ContractParseError, ContractSchemaError, load_contract
from zeroleak.core.scaffold import ClientNameError, TenantExistsError, create_client
from zeroleak.ingest import IngestResult, TenantNotFoundError, ingest_paths


def _clients_root() -> Path:
    """Resuelve `clients_root` desde `ZEROLEAK_CLIENTS_ROOT` (convención
    fijada por el contrato del Caso 9); si no está definida, usa `./clients`
    relativo al directorio de trabajo actual.
    """
    return Path(os.environ.get("ZEROLEAK_CLIENTS_ROOT", "clients"))


_USAGE = (
    "uso: zlk client new <NOMBRE_CLIENTE>\n"
    "     zlk ingest <CLIENTE> <ruta>...\n"
    "     zlk contract check <CLIENTE>"
)


def _parse_client_new_name(argv: list[str]) -> str | None:
    """Extrae `<NOMBRE_CLIENTE>` de `argv` si es una invocación válida de
    `client new`; retorna `None` si `argv` no corresponde a ese subcomando.
    """
    if len(argv) == 3 and argv[0] == "client" and argv[1] == "new":
        return argv[2]
    return None


def _dispatch_client_new(name: str) -> int:
    """Ejecuta `client new <name>` delegando en `create_client` y traduce
    las excepciones de dominio al exit code correspondiente (CA-02):
    éxito -> 0 (ruta impresa por stdout), `ClientNameError` -> 2,
    `TenantExistsError` -> 3 (mensaje impreso por stderr en ambos casos).
    """
    try:
        tenant_path = create_client(name, _clients_root())
    except ClientNameError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except TenantExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    print(tenant_path)
    return 0


def _parse_ingest_args(argv: list[str]) -> tuple[str, list[str]] | None:
    """Extrae `(<CLIENTE>, [<ruta>, ...])` de `argv` si es una invocación
    válida de `ingest`; retorna `None` si `argv` no corresponde a ese
    subcomando.
    """
    if len(argv) >= 3 and argv[0] == "ingest":
        return argv[1], argv[2:]
    return None


def _print_ingest_report(result: IngestResult) -> None:
    """Imprime un reporte legible OK/SKIP/FAIL con resumen de conteos
    (formato libre, CA-12: la CLI es una fachada delgada sobre `IngestResult`).
    """
    for entry in result.ingested:
        print(f"OK   {entry['file']}")
    for entry in result.duplicates:
        print(f"SKIP {entry['path']} (duplicado)")
    for entry in result.failed:
        print(f"FAIL {entry['path']} ({entry['reason']})", file=sys.stderr)
    print(
        f"Resumen: {len(result.ingested)} ingeridos, "
        f"{len(result.duplicates)} duplicados, "
        f"{len(result.failed)} fallidos"
    )


def _dispatch_ingest(client: str, paths: list[str]) -> int:
    """Ejecuta `ingest <client> <paths>...` delegando en `ingest_paths` y
    traduce el resultado/excepción de dominio al exit code correspondiente
    (CA-12): éxito total -> 0, fallo parcial -> 1, `TenantNotFoundError` -> 2.
    """
    try:
        result = ingest_paths(client, paths, _clients_root())
    except TenantNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_ingest_report(result)
    return result.exit_code


def _parse_contract_check_args(argv: list[str]) -> str | None:
    """Extrae `<CLIENTE>` de `argv` si es una invocación válida de
    `contract check`; retorna `None` si `argv` no corresponde a ese
    subcomando. La longitud es exacta (CA-14): `contract check <C> extra`
    no despacha.
    """
    if len(argv) == 3 and argv[0] == "contract" and argv[1] == "check":
        return argv[2]
    return None


def _dispatch_contract_check(client: str) -> int:
    """Ejecuta `contract check <client>`: resuelve la ruta del contrato con
    `_clients_root()`, invoca `load_contract` (motor de `contract_multifile`,
    sin modificarlo, CA-19) y traduce su veredicto al exit code
    correspondiente (camino feliz, CA-01): éxito -> 0, con el mensaje
    impreso por stdout.
    """
    clients_root = _clients_root()
    contrato = clients_root / client / "input" / "contract_data.yaml"

    contract = load_contract(contrato)
    print(f"OK  contrato válido: {client} — {contrato}")
    print(
        f"    {len(contract.archivos)} archivo(s) declarado(s): "
        + ", ".join(a.nombre for a in contract.archivos)
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la consola `zlk`.

    Soporta `zlk client new <NOMBRE_CLIENTE>`: delega en `create_client` e
    imprime por stdout la ruta del tenant creado; y `zlk ingest <CLIENTE>
    <ruta>...`: delega en `ingest_paths` e imprime un reporte OK/SKIP/FAIL.
    """
    if argv is None:
        argv = sys.argv[1:]

    name = _parse_client_new_name(argv)
    if name is not None:
        return _dispatch_client_new(name)

    ingest_args = _parse_ingest_args(argv)
    if ingest_args is not None:
        return _dispatch_ingest(*ingest_args)

    contract_check_client = _parse_contract_check_args(argv)
    if contract_check_client is not None:
        return _dispatch_contract_check(contract_check_client)

    print(_USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
