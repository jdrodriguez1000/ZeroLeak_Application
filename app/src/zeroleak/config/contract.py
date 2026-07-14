"""config.contract — carga y validación de `contract_data.yaml` (D-21/D-22/D-23).

Único punto de entrada: `load_contract(path) -> Contract`. Lee el YAML del
contrato (única ruta que abre; frontera D-21), lo parsea con `yaml.safe_load`
y valida su esquema con Pydantic, devolviendo un `Contract` tipado en memoria.

Nota (paso 10, GREEN, TSK-09/TSK-13/TSK-15/TSK-17/TSK-20/TSK-22): esta
versión cubre el camino feliz (CA-01 a CA-03: count, orden, fidelidad de
campos y los 6 tipos del enum), la traducción de esquema para campo
requerido faltante (CA-04/CA-05, fail-fast, `_mensaje_esquema`), para `tipo`
fuera del enum cerrado (CA-06), para `columnas: []`/ausente (CA-11,
`_columnas_no_vacias`), para `nombre` de columna duplicado por cadena exacta
(CA-09, `_columnas_sin_duplicados`, con CA-10 caracterizado sobre el mismo
validador: la comparación ya es exacta, sin normalizar mayúsculas ni
espacios) y para YAML sintácticamente inválido, que se distingue como
`ContractParseError` antes de llegar al esquema, con un mensaje accionable
que antecede el detalle crudo de PyYAML (CA-07/CA-08). Queda pendiente el
fail-fast ante violaciones múltiples de distinta naturaleza (CA-14) y las
caracterizaciones aún no escritas de la frontera de lectura (CA-12), la
invocación directa sin CLI (CA-13) y los fixtures sintéticos sin PII
(CA-15).
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, field_validator


class TipoDato(str, Enum):
    """Enum cerrado de 6 tipos soportados por una columna (D-23b)."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class Columna(BaseModel):
    """Una columna del contrato: nombre, tipo, nulabilidad y llave (CA-02).

    Los cuatro campos se mapean 1:1 desde el YAML, sin transformación.
    """

    nombre: str
    tipo: TipoDato
    nulable: bool
    llave: bool


class Contract(BaseModel):
    """Contrato validado: lista de columnas en el orden declarado (CA-01)."""

    columnas: list[Columna]

    @field_validator("columnas")
    @classmethod
    def _columnas_no_vacias(cls, valor: list[Columna]) -> list[Columna]:
        """Rechaza `columnas: []` (CA-11); mensaje estable (D-23e)."""
        if not valor:
            raise ValueError("la lista de columnas no puede estar vacía")
        return valor

    @field_validator("columnas")
    @classmethod
    def _columnas_sin_duplicados(cls, valor: list[Columna]) -> list[Columna]:
        """Rechaza `nombre` duplicado por cadena exacta (CA-09, D-23e).

        Compara los `nombre` tal cual, sin normalizar mayúsculas ni espacios.
        """
        vistos: set[str] = set()
        duplicados: list[str] = []
        for columna in valor:
            if columna.nombre in vistos and columna.nombre not in duplicados:
                duplicados.append(columna.nombre)
            vistos.add(columna.nombre)
        if duplicados:
            nombres = ", ".join(f"'{n}'" for n in duplicados)
            raise ValueError(f"nombre de columna duplicado: {nombres}")
        return valor


_MENSAJE_YAML_INVALIDO = "el archivo YAML del contrato es sintácticamente inválido"


class ContractParseError(Exception):
    """El YAML del contrato es sintácticamente inválido (no parsea)."""


class ContractSchemaError(Exception):
    """El YAML parsea pero el esquema del contrato es inválido."""


def load_contract(path: str | Path) -> Contract:
    """Lee, parsea y valida `path` como un `contract_data.yaml`.

    Única ruta que abre (frontera D-21, CA-12). Camino feliz: toma la clave
    raíz `contract_data` -> `columnas`, valida con Pydantic y devuelve el
    `Contract` tipado.
    """
    with open(path, "r", encoding="utf-8") as fh:
        try:
            crudo = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ContractParseError(
                f"{_MENSAJE_YAML_INVALIDO}: {exc}"
            ) from exc

    # Clave raíz `contract_data` -> `columnas` (CA-01); ausencia de la clave
    # o YAML vacío se trata más adelante como esquema mal formado (CA-11).
    columnas = (crudo or {}).get("contract_data", {}).get("columnas", [])
    try:
        return Contract.model_validate({"columnas": columnas})
    except ValidationError as exc:
        raise ContractSchemaError(_mensaje_esquema(exc)) from exc


def _mensaje_esquema(exc: ValidationError) -> str:
    """Traduce el primer error de Pydantic a un mensaje legible (fail-fast).

    Toma `exc.errors()[0]` (D-23c: un solo primer error, sin lista agregada) y
    extrae campo y columna (índice 0-based) a partir de `loc`, según el
    formato `columnas.<índice>.<campo>` que reporta Pydantic; esa extracción
    es común a todas las ramas de abajo, que solo difieren en cómo componen
    el mensaje final:

    - `missing` (campo requerido faltante): CA-04 y, sin cambios, CA-05 para
      el resto de campos faltantes de la columna.
    - `enum` (`tipo` fuera del enum cerrado): CA-06; agrega el valor
      inválido recibido (`primer_error["input"]`) al mensaje nativo de
      Pydantic, que ya enumera los 6 valores permitidos.
    - `value_error` en el campo `columnas` completo (no por columna, `loc ==
      ("columnas",)`): CA-11, el `field_validator` de lista vacía. El mensaje
      ya es el texto estable definido por el validador; se propaga tal cual,
      sin la envoltura genérica "columna de índice ..., campo ...:" que no
      aplica porque el error no es de una columna concreta.
    - fallback genérico: cualquier otro `type` de error de Pydantic no
      cubierto arriba todavía.
    """
    primer_error = exc.errors()[0]
    loc = primer_error.get("loc", ())
    campo = loc[-1] if loc else "?"
    indice = loc[1] if len(loc) > 1 else "?"
    tipo_error = primer_error.get("type", "")
    msg = primer_error.get("msg", "")

    if tipo_error == "value_error" and loc == ("columnas",):
        return msg.removeprefix("Value error, ")
    if tipo_error == "missing":
        return (
            f"falta el campo requerido '{campo}' en la columna de índice {indice} "
            f"({msg})"
        )
    if tipo_error == "enum":
        valor_invalido = primer_error.get("input", "?")
        return (
            f"columna de índice {indice}, campo '{campo}': valor '{valor_invalido}' "
            f"inválido ({msg})"
        )
    return f"columna de índice {indice}, campo '{campo}': {msg}"
