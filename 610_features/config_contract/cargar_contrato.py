"""Carga un `contract_data.yaml` escrito por un humano y muestra el resultado.

A diferencia de `pruebas_humanas.py` (que genera sus propios YAML sintéticos),
este script no inventa nada: recibe la **ruta de tu archivo**, lo carga con
`load_contract` y te muestra qué entendió el motor, o el error si el contrato
es inválido.

Uso (desde la raíz del repositorio):

    py -3.13 610_features/config_contract/cargar_contrato.py <ruta-a-tu-yaml>

Ejemplo:

    py -3.13 610_features/config_contract/cargar_contrato.py clients/COMPANY_DEMO/input/contract_data.yaml

Sale con código 0 si el contrato es válido, 1 si es inválido (con el motivo).
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from zeroleak.config import (  # noqa: E402
    ContractParseError,
    ContractSchemaError,
    load_contract,
)


def _tabla(contract) -> str:
    filas = [("#", "NOMBRE", "TIPO", "NULABLE", "LLAVE")]
    for i, col in enumerate(contract.columnas):
        filas.append((
            str(i),
            col.nombre,
            col.tipo.value,
            "sí" if col.nulable else "no",
            "sí" if col.llave else "no",
        ))
    anchos = [max(len(f[c]) for f in filas) for c in range(5)]
    lineas = []
    for n, fila in enumerate(filas):
        lineas.append("  ".join(fila[c].ljust(anchos[c]) for c in range(5)).rstrip())
        if n == 0:
            lineas.append("  ".join("-" * anchos[c] for c in range(5)))
    return "\n".join(lineas)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        print("ERROR: indica la ruta del contract_data.yaml que quieres cargar.")
        return 2

    ruta = Path(argv[1])
    print("=" * 70)
    print(f"Cargando contrato: {ruta}")
    print("=" * 70)

    if not ruta.exists():
        print(f"[ERROR] El archivo no existe: {ruta.resolve()}")
        return 1

    try:
        contract = load_contract(ruta)
    except ContractParseError as exc:
        print("[INVÁLIDO] El archivo no es YAML bien formado (ContractParseError):\n")
        print(exc)
        return 1
    except ContractSchemaError as exc:
        print("[INVÁLIDO] El YAML se parseó, pero no cumple el contrato "
              "(ContractSchemaError):\n")
        print(exc)
        return 1

    print(f"[VÁLIDO] Contrato cargado: {len(contract.columnas)} columna(s).\n")
    print(_tabla(contract))
    llaves = [c.nombre for c in contract.columnas if c.llave]
    print(f"\nLlaves: {', '.join(llaves) if llaves else '(ninguna)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
