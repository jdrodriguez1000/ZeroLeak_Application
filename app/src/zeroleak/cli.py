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

from zeroleak.core.scaffold import ClientNameError, TenantExistsError, create_client


def _clients_root() -> Path:
    """Resuelve `clients_root` desde `ZEROLEAK_CLIENTS_ROOT` (convención
    fijada por el contrato del Caso 9); si no está definida, usa `./clients`
    relativo al directorio de trabajo actual.
    """
    return Path(os.environ.get("ZEROLEAK_CLIENTS_ROOT", "clients"))


_USAGE = "uso: zlk client new <NOMBRE_CLIENTE>"


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


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la consola `zlk`.

    Soporta por ahora `zlk client new <NOMBRE_CLIENTE>`: delega en
    `create_client` e imprime por stdout la ruta del tenant creado.
    """
    if argv is None:
        argv = sys.argv[1:]

    name = _parse_client_new_name(argv)
    if name is not None:
        return _dispatch_client_new(name)

    print(_USAGE, file=sys.stderr)
    return 1
