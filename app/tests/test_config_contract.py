"""Tests unitarios de `config_contract` (bucle TDD, `app/tests/test_config_contract.py`).

Cubre los criterios de aceptación `CA-xx` de `610_features/config_contract/spec.md`.
Fixtures 100% sintéticas (regla "Datos en Bóveda", C-01); ver `conftest.py`
(`write_contract_yaml`, `contrato_valido_columnas`).

Caso 1 (TSK-02, CA-01): dado un YAML válido con N columnas, `load_contract`
devuelve un `Contract` con `len(columnas) == N` y en el mismo orden declarado.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from zeroleak.config import ContractSchemaError, TipoDato, load_contract

TIPOS_PERMITIDOS = [t.value for t in TipoDato]


def test_load_contract_valido_n_columnas_orden(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
) -> None:
    """CA-01: N columnas válidas -> Contract.columnas con longitud N y mismo orden."""
    path = write_contract_yaml(columnas=contrato_valido_columnas)

    contrato = load_contract(path)

    assert len(contrato.columnas) == len(contrato_valido_columnas)
    nombres_esperados = [col["nombre"] for col in contrato_valido_columnas]
    nombres_obtenidos = [col.nombre for col in contrato.columnas]
    assert nombres_obtenidos == nombres_esperados


def test_load_contract_fidelidad_de_campos(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
) -> None:
    """CA-02: cada columna expone nombre/tipo/nulable/llave iguales a lo declarado.

    Ej.: la primera columna declarada (`test_id`/`integer`/`nulable=false`/
    `llave=true`) debe reflejarse exactamente en la `Columna` resultante,
    para las cuatro columnas del fixture (TSK-04).
    """
    path = write_contract_yaml(columnas=contrato_valido_columnas)

    contrato = load_contract(path)

    assert len(contrato.columnas) == len(contrato_valido_columnas)
    for esperado, obtenida in zip(contrato_valido_columnas, contrato.columnas):
        assert obtenida.nombre == esperado["nombre"]
        assert obtenida.tipo.value == esperado["tipo"]
        assert obtenida.nulable is esperado["nulable"]
        assert obtenida.llave is esperado["llave"]


def test_load_contract_seis_tipos_enum(
    write_contract_yaml: Callable[..., Path],
    contrato_seis_tipos_columnas: list[dict],
) -> None:
    """CA-03: YAML con los 6 tipos soportados se acepta y cada `tipo` mapea a
    su valor de enum `TipoDato` correspondiente (TSK-06).

    Fixture `contrato_seis_tipos_columnas` (conftest.py): una columna
    sintética por cada uno de los 6 tipos (`string`, `integer`, `float`,
    `date`, `datetime`, `boolean`, D-23b). Verifica no solo que se acepta el
    YAML, sino que `Columna.tipo` es una instancia de `TipoDato` cuyo `.value`
    coincide exactamente con el string declarado, y que el conjunto completo
    de valores usados cubre los 6 miembros del enum (regresión clave: el
    spike solo prototipó 5 tipos, la spec añadió `datetime`, D-23b).
    """
    path = write_contract_yaml(columnas=contrato_seis_tipos_columnas)

    contrato = load_contract(path)

    assert len(contrato.columnas) == len(contrato_seis_tipos_columnas)
    for esperado, obtenida in zip(contrato_seis_tipos_columnas, contrato.columnas):
        assert isinstance(obtenida.tipo, TipoDato)
        assert obtenida.tipo.value == esperado["tipo"]

    tipos_obtenidos = {col.tipo for col in contrato.columnas}
    assert tipos_obtenidos == set(TipoDato)


def test_load_contract_campo_tipo_faltante(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """CA-04 (Caso 4, TSK-08): columna que omite `tipo` -> `ContractSchemaError`.

    YAML sintético (sin PII, C-01) con dos columnas: la de índice 0
    (`test_id`) es válida y completa; la de índice 1 (`correo`) omite el
    campo requerido `tipo`. El mensaje de la excepción debe identificar el
    campo faltante (`tipo`) y la columna afectada por índice/posición
    (0-based, según el gate del paso 9: Pydantic reporta la ubicación como
    `columnas.<índice>.<campo>`). `load_contract` no debe retornar objeto
    (la excepción se lanza); además la excepción debe ser exactamente
    `ContractSchemaError`, no un `pydantic.ValidationError` crudo.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        "    - nombre: correo\n"
        "      nulable: true\n"
        "      llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert "tipo" in mensaje
    assert "1" in mensaje


@pytest.mark.parametrize(
    ("campo_faltante", "texto_columna_incompleta"),
    [
        (
            "nombre",
            "    - tipo: string\n"
            "      nulable: true\n"
            "      llave: false\n",
        ),
        (
            "nulable",
            "    - nombre: correo\n"
            "      tipo: string\n"
            "      llave: false\n",
        ),
        (
            "llave",
            "    - nombre: correo\n"
            "      tipo: string\n"
            "      nulable: true\n",
        ),
    ],
)
def test_load_contract_otros_campos_faltantes(
    write_contract_yaml: Callable[..., Path],
    campo_faltante: str,
    texto_columna_incompleta: str,
) -> None:
    """CA-05 (Caso 5, TSK-10): columna que omite `nombre`/`nulable`/`llave`
    (los otros tres campos requeridos, distintos de `tipo` del Caso 4) ->
    `ContractSchemaError`.

    YAML sintético (sin PII, C-01) con dos columnas: la de índice 0
    (`test_id`) es válida y completa; la de índice 1 omite el campo
    requerido bajo prueba (`nombre`, `nulable` o `llave`). El mensaje debe
    identificar el campo faltante y la columna afectada por índice (0-based);
    `load_contract` no debe retornar objeto (se lanza la excepción), y ésta
    debe ser exactamente `ContractSchemaError`, no un `pydantic.ValidationError`
    crudo.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        + texto_columna_incompleta
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert campo_faltante in mensaje
    assert "1" in mensaje


def test_load_contract_tipo_fuera_de_enum(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """CA-06 (Caso 6, TSK-12): `tipo: numero_magico` (fuera del enum de 6
    tipos) -> `ContractSchemaError`.

    YAML sintético (sin PII, C-01) con dos columnas: la de índice 0
    (`test_id`) es válida y completa; la de índice 1 (`correo`) declara un
    `tipo` que no pertenece al enum cerrado de 6 valores (D-23b). El mensaje
    de la excepción debe identificar tres cosas: (a) el **valor inválido**
    declarado (`numero_magico`), (b) la **columna afectada** por índice
    (0-based, según el gate del paso 9), y (c) enumerar los **6 valores
    permitidos** (`string`, `integer`, `float`, `date`, `datetime`,
    `boolean`). `load_contract` no debe retornar objeto (se lanza la
    excepción), y ésta debe ser exactamente `ContractSchemaError`, no un
    `pydantic.ValidationError` crudo.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        "    - nombre: correo\n"
        "      tipo: numero_magico\n"
        "      nulable: true\n"
        "      llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert "numero_magico" in mensaje
    assert "1" in mensaje
    for tipo_valido in TIPOS_PERMITIDOS:
        assert tipo_valido in mensaje
