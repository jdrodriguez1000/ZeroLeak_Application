"""config — eje de configuración de ZeroLeak (contratos por-YAML, D-21/D-22).

Primer tracer bullet: `contract_data.yaml` -> `load_contract`. Ver
system_design §5.
"""
from __future__ import annotations

from zeroleak.config.contract import (
    Columna,
    Contract,
    ContractParseError,
    ContractSchemaError,
    TipoDato,
    load_contract,
)

__all__ = [
    "load_contract",
    "Contract",
    "Columna",
    "TipoDato",
    "ContractParseError",
    "ContractSchemaError",
]
