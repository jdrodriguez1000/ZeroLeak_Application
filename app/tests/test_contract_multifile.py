"""Tests unitarios de `contract_multifile` (bucle TDD, `app/tests/test_contract_multifile.py`).

Cubre los criterios de aceptación `CA-xx` de `610_features/contract_multifile/spec.md`.
Fixtures 100% sintéticas (regla "Datos en Bóveda", C-01); ver `conftest.py`
(`write_contract_yaml`, `contrato_valido_columnas`, `clientes_columnas`,
`ventas_columnas`, `catalogo_columnas`, `archivos_*`).

Renombrado (`git mv`) desde `test_config_contract.py` (CA-25, TSK-03): este
archivo consolida los 15 tests heredados de `config_contract`, migrados de
FORMA a `contract_data.archivos[].columnas` (D-18). Es una migración **en dos
tiempos** (plan.md, "Estrategia de migración de los tests"):

1. **Este caso (Caso 1, TSK-03):** migración de forma. Cada fixture crudo se
   envuelve dentro de un único archivo declarativo sintético (`archivo.csv`,
   salvo donde el propio comportamiento bajo prueba exige varios archivos) y
   toda lectura pasa de `contrato.columnas` a `contrato.archivos[i].columnas`.
   Las aserciones heredadas ya eran de **subcadena** y sobreviven al
   traductor genérico; la única excepción era la aserción de igualdad
   exacta de `columnas: []`, que en este primer tiempo se relajó
   temporalmente a subcadena. **Ya endurecida** al texto literal M-07 en
   el Caso 12 (`test_load_contract_columnas_vacias_en_archivo_m07`).
2. **Endurecimiento por caso:** cada test se reescribe al texto literal
   M-xx en el caso que especifica su comportamiento equivalente (ver el
   inventario de migración de plan.md). **No** se hace aquí.

Caso 1 (TSK-04, CA-01): dado un YAML válido con 2 archivos (`clientes.csv`
3 columnas, `ventas.csv` 4 columnas), `load_contract` devuelve un `Contract`
con `len(archivos) == 2`, nombres en el orden declarado y `[3, 4]` columnas.
"""
from __future__ import annotations

import builtins
import inspect
import re
from pathlib import Path
from typing import Callable

import pytest

from zeroleak import cli as zeroleak_cli
from zeroleak.config import (
    Contract,
    ContractParseError,
    ContractSchemaError,
    TipoDato,
    load_contract,
)

TIPOS_PERMITIDOS = [t.value for t in TipoDato]

# Nombre de archivo declarativo sintético usado por los tests migrados que
# heredan un comportamiento de **un solo** archivo (el esquema viejo no tenía
# noción de archivo; se envuelve en uno solo para preservar el comportamiento
# bajo prueba sin reescribir aserciones de contenido, TSK-03).
_NOMBRE_ARCHIVO_UNICO = "archivo.csv"


def test_load_contract_valido_dos_archivos_orden(
    write_contract_yaml: Callable[..., Path],
    archivos_dos_archivos: list[dict],
) -> None:
    """CA-01 (Caso 1, TSK-04): YAML válido de 2 archivos -> `Contract.archivos`
    con `len == 2`, nombres en el orden declarado y `[3, 4]` columnas.

    Fixture `archivos_dos_archivos` (conftest.py, TSK-02): `clientes.csv`
    (3 columnas) + `ventas.csv` (4 columnas, incl. `cliente_id` homónimo y
    `vendida_en: datetime`). Test nuevo, no heredado de `config_contract`.
    """
    path = write_contract_yaml(archivos=archivos_dos_archivos)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 2
    assert [a.nombre for a in contrato.archivos] == ["clientes.csv", "ventas.csv"]
    assert [len(a.columnas) for a in contrato.archivos] == [3, 4]


def test_load_contract_valido_n_columnas_orden(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
) -> None:
    """CA-01/CA-04 (destino final: Caso 1 / Caso 3): N columnas válidas dentro
    de un único archivo -> `archivos[0].columnas` con longitud N y mismo
    orden (TSK-03: migración de forma, envuelto en `_NOMBRE_ARCHIVO_UNICO`).
    """
    path = write_contract_yaml(
        archivos=[{"nombre": _NOMBRE_ARCHIVO_UNICO, "columnas": contrato_valido_columnas}]
    )

    contrato = load_contract(path)

    assert len(contrato.archivos) == 1
    assert len(contrato.archivos[0].columnas) == len(contrato_valido_columnas)
    nombres_esperados = [col["nombre"] for col in contrato_valido_columnas]
    nombres_obtenidos = [col.nombre for col in contrato.archivos[0].columnas]
    assert nombres_obtenidos == nombres_esperados


def test_load_contract_fidelidad_de_campos(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
) -> None:
    """CA-02 (destino final: Caso 2): cada columna expone nombre/tipo/nulable/llave
    iguales a lo declarado, dentro de su archivo (TSK-03: forma migrada).

    Ej.: la primera columna declarada (`test_id`/`integer`/`nulable=false`/
    `llave=true`) debe reflejarse exactamente en la `Columna` resultante,
    para las cuatro columnas del fixture (envuelto en un único archivo).
    """
    path = write_contract_yaml(
        archivos=[{"nombre": _NOMBRE_ARCHIVO_UNICO, "columnas": contrato_valido_columnas}]
    )

    contrato = load_contract(path)

    assert len(contrato.archivos) == 1
    columnas = contrato.archivos[0].columnas
    assert len(columnas) == len(contrato_valido_columnas)
    for esperado, obtenida in zip(contrato_valido_columnas, columnas):
        assert obtenida.nombre == esperado["nombre"]
        assert obtenida.tipo.value == esperado["tipo"]
        assert obtenida.nulable is esperado["nulable"]
        assert obtenida.llave is esperado["llave"]


def test_load_contract_fidelidad_de_campos_por_archivo(
    write_contract_yaml: Callable[..., Path],
    archivos_dos_archivos: list[dict],
) -> None:
    """CA-02 (Caso 2, TSK-06): dado el contrato de 2 archivos (`clientes.csv`
    3 columnas + `ventas.csv` 4 columnas, fixture `archivos_dos_archivos`),
    cada columna expone `nombre`/`tipo`/`nulable`/`llave` iguales a lo
    declarado y **en el orden declarado dentro de su propio archivo**.

    Ejemplo ancla del `TSK-06`: `archivos[1].columnas[0]` (primera columna
    de `ventas.csv`) debe ser exactamente `venta_id`/`integer`/`False`/`True`.
    Se verifica además la fidelidad 1:1 de las 4 columnas de `ventas.csv` y
    de las 3 de `clientes.csv`, para blindar que la fidelidad es por-archivo
    (no una coincidencia de un único archivo aplanado).
    """
    path = write_contract_yaml(archivos=archivos_dos_archivos)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 2

    # Ejemplo ancla de la spec/plan: archivos[1].columnas[0] -> venta_id.
    primera_columna_ventas = contrato.archivos[1].columnas[0]
    assert primera_columna_ventas.nombre == "venta_id"
    assert primera_columna_ventas.tipo.value == "integer"
    assert primera_columna_ventas.nulable is False
    assert primera_columna_ventas.llave is True

    # Fidelidad 1:1 completa, dentro de cada archivo, en el orden declarado.
    for archivo_esperado, archivo_obtenido in zip(archivos_dos_archivos, contrato.archivos):
        columnas_esperadas = archivo_esperado["columnas"]
        columnas_obtenidas = archivo_obtenido.columnas
        assert len(columnas_obtenidas) == len(columnas_esperadas)
        for esperada, obtenida in zip(columnas_esperadas, columnas_obtenidas):
            assert obtenida.nombre == esperada["nombre"]
            assert obtenida.tipo.value == esperada["tipo"]
            assert obtenida.nulable is esperada["nulable"]
            assert obtenida.llave is esperada["llave"]


def test_load_contract_un_archivo_caso_general(
    write_contract_yaml: Callable[..., Path],
    archivos_un_archivo: list[dict],
) -> None:
    """CA-04 (Caso 3, TSK-08): YAML válido con **un solo** archivo -> `Contract`
    con `len(archivos) == 1` y `archivos[0].columnas` contiene exactamente
    las mismas columnas (4 campos: `nombre`/`tipo`/`nulable`/`llave`, mismo
    orden) que producía `Contract.columnas` en la forma anterior (esquema de
    un solo archivo).

    Un archivo es el **caso general**, no una rama especial: `load_contract`
    no debe tratar `len(archivos) == 1` de forma distinta de N archivos. La
    fixture `archivos_un_archivo` (conftest.py, TSK-02) envuelve
    `clientes_columnas` (3 columnas, incluye `cliente_id` llave) en un único
    archivo `clientes.csv`.
    """
    path = write_contract_yaml(archivos=archivos_un_archivo)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 1

    columnas_esperadas = archivos_un_archivo[0]["columnas"]
    columnas_obtenidas = contrato.archivos[0].columnas
    assert len(columnas_obtenidas) == len(columnas_esperadas)
    for esperada, obtenida in zip(columnas_esperadas, columnas_obtenidas):
        assert obtenida.nombre == esperada["nombre"]
        assert obtenida.tipo.value == esperada["tipo"]
        assert obtenida.nulable is esperada["nulable"]
        assert obtenida.llave is esperada["llave"]


def test_load_contract_valido_tres_archivos_orden(
    write_contract_yaml: Callable[..., Path],
    archivos_tres_archivos: list[dict],
) -> None:
    """CA-01/CA-04 (Caso 3b, TSK-08b): YAML válido de **3** archivos ->
    `Contract.archivos` con `len == 3`, nombres en el orden declarado y
    `[3, 4, 2]` columnas.

    Cierra el hueco de cobertura de **N >= 3** detectado en el gate (paso 9,
    riesgo técnico 7 del plan): el diseño no acota `archivos` (la única
    restricción es "no vacía", M-04), pero ningún caso previo del bucle
    ejercitaba más de 2 archivos, así que N archivos como caso general (sin
    rama especial ni cota superior) no estaba probado. Fixture
    `archivos_tres_archivos` (conftest.py, TSK-02): `clientes.csv` (3
    columnas), `ventas.csv` (4) y `catalogo.csv` (2). Reutiliza
    `write_contract_yaml` (TSK-01); sin fixtures nuevos en disco.

    Lado de código: TSK-09 (`(car?)`, ya `cancelada_suspendida` en el Caso 3
    -- `load_contract` usa una única ruta para 1 o N archivos desde TSK-05).
    """
    path = write_contract_yaml(archivos=archivos_tres_archivos)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 3
    assert [a.nombre for a in contrato.archivos] == [
        "clientes.csv",
        "ventas.csv",
        "catalogo.csv",
    ]
    assert [len(a.columnas) for a in contrato.archivos] == [3, 4, 2]


def test_load_contract_columna_homonima_en_dos_archivos(
    write_contract_yaml: Callable[..., Path],
    archivos_dos_archivos: list[dict],
) -> None:
    """CA-03 (Caso 4, TSK-10): `cliente_id` como columna de `clientes.csv` **y**
    de `ventas.csv` se acepta SIN error -- el duplicado de columna es **por
    archivo, no global** (D-25, hallazgo 2): el validador de duplicados
    reside en `ArchivoContrato`, así que dos archivos distintos pueden
    declarar columnas homónimas.

    Fixture `archivos_dos_archivos` (conftest.py, TSK-02): `clientes.csv`
    (3 columnas, incl. `cliente_id` llave) + `ventas.csv` (4 columnas, incl.
    `cliente_id` homónimo deliberado, no llave). `load_contract` no debe
    lanzar `ContractSchemaError`; ambos archivos deben conservar su propia
    columna `cliente_id`, con sus propios campos fieles a lo declarado.
    """
    path = write_contract_yaml(archivos=archivos_dos_archivos)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 2

    clientes_csv = next(a for a in contrato.archivos if a.nombre == "clientes.csv")
    ventas_csv = next(a for a in contrato.archivos if a.nombre == "ventas.csv")

    cliente_id_en_clientes = next(
        c for c in clientes_csv.columnas if c.nombre == "cliente_id"
    )
    cliente_id_en_ventas = next(
        c for c in ventas_csv.columnas if c.nombre == "cliente_id"
    )

    # Ambas columnas homónimas existen, cada una fiel a su propia
    # declaración (distinto valor de `llave` a propósito, ver fixtures).
    assert cliente_id_en_clientes.llave is True
    assert cliente_id_en_ventas.llave is False


def test_load_contract_seis_tipos_enum(
    write_contract_yaml: Callable[..., Path],
    contrato_seis_tipos_columnas: list[dict],
) -> None:
    """CA-05 (Caso 5, TSK-12, "seis-tipos-dentro-de-archivo"): YAML con los 6
    tipos soportados, uno por columna dentro de un único archivo, se acepta
    y cada `tipo` mapea a su valor de enum `TipoDato` correspondiente.

    Fixture `contrato_seis_tipos_columnas` (conftest.py): una columna
    sintética por cada uno de los 6 tipos (`string`, `integer`, `float`,
    `date`, `datetime`, `boolean`, D-23b), envuelta en un único archivo.

    Candidato a caracterización (L-13/L-14): este test ya existía desde la
    migración de forma del Caso 1 (TSK-03) y pasa en VERDE de inmediato,
    efecto colateral de que el enum `TipoDato` de 6 valores se reutiliza sin
    cambios dentro de `ArchivoContrato.columnas` (TSK-05). Honestidad
    verificada por inyección/reversión temporal (L-10): se comentó
    momentáneamente el miembro `BOOLEAN` de `TipoDato` en
    `config/contract.py` -> el test pasó a FAILED (`ContractSchemaError`:
    valor 'boolean' inválido, ya no pertenece al enum de 5 restantes),
    confirmando que el test SÍ detecta el defecto y no es vacuo; se revirtió
    la inyección de inmediato (verificado con `git diff`: sin rastro de la
    inyección). TSK-13 (`tdd_coder`) queda candidata a
    `cancelada_suspendida` sin entregable.
    """
    path = write_contract_yaml(
        archivos=[
            {"nombre": _NOMBRE_ARCHIVO_UNICO, "columnas": contrato_seis_tipos_columnas}
        ]
    )

    contrato = load_contract(path)

    assert len(contrato.archivos) == 1
    columnas = contrato.archivos[0].columnas
    assert len(columnas) == len(contrato_seis_tipos_columnas)
    for esperado, obtenida in zip(contrato_seis_tipos_columnas, columnas):
        assert isinstance(obtenida.tipo, TipoDato)
        assert obtenida.tipo.value == esperado["tipo"]

    tipos_obtenidos = {col.tipo for col in columnas}
    assert tipos_obtenidos == set(TipoDato)


@pytest.mark.parametrize(
    ("texto", "repr_encontrado"),
    [
        (
            "contract_data:\n",
            "None",
        ),
        (
            "contract_data: pendiente_de_completar\n",
            "'pendiente_de_completar'",
        ),
    ],
    ids=["raiz_nula", "raiz_no_mapa_cadena"],
)
def test_load_contract_raiz_nula_o_no_mapa_m01(
    write_contract_yaml: Callable[..., Path],
    texto: str,
    repr_encontrado: str,
) -> None:
    """Caso 6 (TSK-14, CA-19/CA-20, T-56): `contract_data:` nulo o no-mapa ->
    `ContractSchemaError` con el texto literal **M-01**, nunca `AttributeError`.

    Dos entradas sintéticas (sin PII, C-01):

    1. `contract_data:` sin valor (parsea a `None` con PyYAML) -> plantilla
       vacía real (T-56 original). `repr(None)` es `'None'`.
    2. `contract_data: pendiente_de_completar` -> valor **no-mapa** (una
       cadena), hallazgo 1 de D-25 que amplía T-56 más allá de solo `None`.
       `repr('pendiente_de_completar')` es `"'pendiente_de_completar'"`.

    El texto M-01 (spec.md, catálogo de mensajes) es contrato literal, fijado
    por **igualdad exacta** (no subcadena):
    `la clave raíz 'contract_data' debe contener un mapa con la lista
    'archivos' (se encontró: <repr>)`.

    El código vigente (`contract.py:126`) encadena
    `(crudo or {}).get("contract_data", {}).get("archivos", [])`: con
    `contract_data` nulo o no-mapa, el primer `.get(...)` devuelve `None` o la
    cadena `'pendiente_de_completar'`, y el **segundo** `.get(...)` revienta
    con `AttributeError` (`None`/`str` no tienen `.get`) en vez de dar M-01 --
    exactamente el bug T-56 que esta feature cierra (TSK-15, extracción
    defensiva por `isinstance`, GREEN).

    El test verifica EXPLÍCITAMENTE que la excepción capturada es
    `ContractSchemaError` (tipo exacto) y no `AttributeError`: si
    `pytest.raises(ContractSchemaError)` deja escapar un `AttributeError`, la
    aserción de tipo la reporta pytest mismo (no captura), lo cual es
    precisamente el RED esperado en esta fase mientras el bug siga vivo.
    """
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    excepcion = exc_info.value
    assert type(excepcion) is ContractSchemaError, (
        f"se esperaba exactamente ContractSchemaError, no "
        f"{type(excepcion).__name__!r} (T-56: nunca debe propagarse "
        f"AttributeError)"
    )
    assert not isinstance(excepcion, AttributeError)

    mensaje_esperado = (
        "la clave raíz 'contract_data' debe contener un mapa con la lista "
        f"'archivos' (se encontró: {repr_encontrado})"
    )
    assert str(excepcion) == mensaje_esperado


@pytest.mark.parametrize(
    "texto",
    [
        "contract_data:\n  archivos: []\n",
        "contract_data:\n  descripcion: sin archivos declarados\n",
        "contract_data:\n  archivos:\n",
    ],
    ids=["archivos_vacia", "archivos_ausente", "archivos_nula"],
)
def test_load_contract_archivos_vacia_ausente_nula_m04(
    write_contract_yaml: Callable[..., Path],
    texto: str,
) -> None:
    """Caso 7 (TSK-16, CA-06/CA-07): `archivos: []` / ausente / nula (sin
    `columnas` en la raíz de `contract_data`) -> `ContractSchemaError` con el
    texto literal **M-04** (`la lista de archivos no puede estar vacía`);
    `load_contract` no debe retornar objeto.

    Tres entradas sintéticas (sin PII, C-01), deliberadamente **sin**
    `columnas` en la raíz (para no disparar M-02/M-13, fuera de alcance de
    este caso, Casos 9/10):

    1. `archivos: []` -- lista explícitamente vacía.
    2. clave `archivos` **ausente** -- `contract_data` es un mapa válido pero
       no declara `archivos` en absoluto.
    3. `archivos:` **nula** -- la clave está presente pero sin valor (parsea
       a `None` con PyYAML).

    Hoy (antes de TSK-17) `Contract.archivos` no tiene ningún
    `field_validator` que rechace la lista vacía, y `load_contract`
    (`contract.py:136`) hace `cuerpo.get("archivos", [])`, que normaliza el
    caso **ausente** (2) igual que el **vacío** (1) a `[]` -- pero **no** el
    caso **nulo** (3), porque `.get(..., default)` solo aplica el default
    cuando la clave falta, no cuando su valor es `None`. Por eso el fallo
    esperado en RED difiere por variante:

    - Variantes 1 y 2 (`archivos` termina en `[]`): `Contract.model_validate
      ({"archivos": []})` **no** lanza ninguna excepción hoy (una lista
      vacía es una lista `list[ArchivoContrato]` válida sin el validador de
      TSK-17) -- `load_contract` devuelve un `Contract` con
      `archivos == []`, así que `pytest.raises(ContractSchemaError)` falla
      con `DID NOT RAISE` porque no existe la regla de negocio "no vacía"
      todavía.
    - Variante 3 (`archivos` es `None`): Pydantic sí rechaza `None` como
      valor de un campo `list[ArchivoContrato]` (error de tipo, no la regla
      de negocio M-04) y `_mensaje_esquema` (que hoy no conoce
      `loc == ("archivos",)`) cae al `fallback` genérico
      (`columna de índice ?, campo 'archivos': ...`), así que sí se lanza
      `ContractSchemaError` pero con un mensaje que **no** coincide con el
      texto literal M-04 -- la aserción de igualdad exacta del mensaje falla.

    Este es el RED legítimo que espera TSK-17 (GREEN): normalizar
    ausente/nula a `[]` y añadir el `field_validator` `_archivos_no_vacia`
    con el mensaje estable M-04.
    """
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = "la lista de archivos no puede estar vacía"
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_archivos_no_lista_m03(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 8 (TSK-18, CA-09): `archivos: ventas.csv` (valor NO-lista, una
    cadena) -> `ContractSchemaError` con el texto literal **M-03** exacto
    (`'archivos' debe ser una lista (se encontró: 'ventas.csv')`);
    `load_contract` no debe retornar objeto.

    Camino distinto del Caso 7 (`archivos` ausente/nula, ya normalizada a
    `[]`): aquí la clave `archivos` está **presente** y con un valor de tipo
    no-lista. Sin `columnas` en la raíz de `contract_data` (para no disparar
    M-02/M-13, fuera de alcance de este caso).

    Este caso **espera código real** (no es caracterización, plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23): hoy no existe ninguna
    guarda de tipo sobre `archivos` antes de Pydantic. `load_contract`
    (`contract.py:150`) toma `archivos = cuerpo.get("archivos", [])` sin
    comprobar su tipo y se lo pasa tal cual a
    `Contract.model_validate({"archivos": archivos})`. Pydantic sí rechaza
    una cadena como valor de `list[ArchivoContrato]` (error de tipo
    `list_type`, `loc == ("archivos",)`) y sí se lanza `ContractSchemaError`
    -- pero `_mensaje_esquema` no conoce hoy esa forma de error (solo trata
    `value_error` en `loc in (("columnas",), ("archivos",))`, `missing` y
    `enum`) y cae al `fallback` genérico
    (`columna de índice ?, campo 'archivos': Input should be a valid list`),
    que **no** coincide con el texto literal M-03 -- la aserción de
    igualdad exacta de mensaje falla. No es un `ImportError` ni un error de
    sintaxis del test: es exactamente el defecto que TSK-19 (`tdd_coder`,
    GREEN) debe cerrar con una guarda de tipo explícita antes de Pydantic.
    """
    texto = "contract_data:\n  archivos: ventas.csv\n"
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = "'archivos' debe ser una lista (se encontró: 'ventas.csv')"
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_esquema_viejo_m02(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 9 (TSK-20, CA-08): YAML en el **esquema viejo**
    (`contract_data.columnas` con columnas válidas, **sin** clave `archivos`)
    -> `ContractSchemaError` con el texto literal **M-02** exacto (orienta a
    la forma nueva `archivos[].columnas`), y explícitamente **no** el
    mensaje genérico M-04 (`la lista de archivos no puede estar vacía`),
    que sería engañoso aquí porque el problema no es que falten archivos:
    es que el contrato sigue declarando el bloque `columnas` de la raíz que
    ya no existe en el esquema nuevo (D-25c).

    YAML sintético (sin PII, C-01), deliberadamente **sin** la clave
    `archivos` (para no disparar M-13/híbrido, Caso 10, fuera de alcance de
    este caso): `contract_data` declara únicamente `columnas` en su raíz,
    con dos columnas válidas y completas.

    Este caso **espera código real** (no es caracterización, plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23): hoy no existe ninguna
    comprobación pre-Pydantic del residual `columnas` en la raíz de
    `contract_data` (TSK-21, diferida). `load_contract` (`contract.py`)
    simplemente hace `archivos = cuerpo.get("archivos", [])`, que -- al no
    encontrar la clave `archivos` -- normaliza a `[]` exactamente igual que
    el Caso 7 (`archivos` ausente), y de ahí cae en el `field_validator`
    `_archivos_no_vacia` (TSK-17, ya GREEN), lanzando `ContractSchemaError`
    con el mensaje **M-04** (`la lista de archivos no puede estar vacía`)
    en vez de **M-02**. El bloque `columnas` residual de la raíz se ignora
    en silencio: ni se audita ni se denuncia, justo la fuga silenciosa que
    D-25c prohíbe. No es un `ImportError` ni un error de sintaxis del test:
    es exactamente el defecto que TSK-21 (`tdd_coder`, GREEN) debe cerrar
    con una rama pre-Pydantic que, ante `columnas` en la raíz sin `archivos`
    utilizable, lance M-02 en vez de dejar caer el flujo a M-04.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        "    - nombre: correo\n"
        "      tipo: string\n"
        "      nulable: true\n"
        "      llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "el contrato usa el esquema anterior de un solo archivo: se "
        "encontró 'columnas' en la raíz de 'contract_data'; ahora las "
        "columnas van dentro de 'archivos[]' "
        "(contract_data.archivos[].columnas)"
    )
    assert str(exc_info.value) == mensaje_esperado
    assert str(exc_info.value) != "la lista de archivos no puede estar vacía"


def test_load_contract_hibrido_archivos_y_columnas_residual_m13(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 10 (TSK-22, CA-28): YAML **híbrido** -- `contract_data.archivos`
    es una lista **no vacía** que, por sí sola, cargaría sin error (un
    archivo declarativo sintético con una columna válida y completa) --
    **y además** `contract_data` declara en su raíz un bloque `columnas`
    residual del esquema viejo. `load_contract` debe lanzar
    `ContractSchemaError` con el texto literal **M-13** exacto (avisa de
    los dos bloques y de qué hacer) y **no** retornar ningún objeto
    `Contract`; el residual **nunca** se ignora en silencio (D-26).

    Caso disjunto de CA-08/Caso 9 (`test_load_contract_esquema_viejo_m02`):
    allí `archivos` está ausente (no hay `archivos` utilizable) y el
    mensaje es M-02; aquí sí hay una `archivos` utilizable (lista no
    vacía) y el mensaje es M-13. El test verifica explícitamente que
    ambos fixtures producen mensajes **distintos** (disyunción exigida
    por TSK-22/D-26).

    Este caso **espera código real** (no es caracterización; plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23; TSK-23 es la única
    tarea de la feature sin código prototipado en el spike, nota de
    riesgo de D-26). Hoy `load_contract` (`contract.py`) solo bifurca por
    `"columnas" in cuerpo` para lanzar M-02 cuando `archivos` **no** es
    utilizable (TSK-21, Caso 9); cuando `archivos` **sí** es una lista no
    vacía, esa rama simplemente no bloquea y el flujo cae directo a
    `Contract.model_validate({"archivos": archivos})`, que valida bien
    (una columna sintética completa) y devuelve un `Contract` -- el
    bloque `columnas` residual de la raíz se ignora en silencio, sin
    lanzar ninguna excepción. Por tanto `pytest.raises(ContractSchemaError)`
    debe fallar hoy con `DID NOT RAISE` (no `ImportError` ni error de
    sintaxis del test): es exactamente el defecto que TSK-23 (`tdd_coder`,
    GREEN) debe cerrar con la rama pre-Pydantic contigua y disjunta de
    M-02, condicionada a `archivos_utilizable`.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "  columnas:\n"
        "    - nombre: residual_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "el contrato declara 'archivos[]' y además un 'columnas' "
        "residual en la raíz de 'contract_data': ese bloque no se valida "
        "ni se audita; elimínelo y deje cada columna dentro del archivo "
        "al que pertenece (contract_data.archivos[].columnas)"
    )
    assert str(exc_info.value) == mensaje_esperado

    texto_esquema_viejo = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        "    - nombre: correo\n"
        "      tipo: string\n"
        "      nulable: true\n"
        "      llave: false\n"
    )
    path_esquema_viejo = write_contract_yaml(texto=texto_esquema_viejo)
    with pytest.raises(ContractSchemaError) as exc_info_esquema_viejo:
        load_contract(path_esquema_viejo)

    assert str(exc_info_esquema_viejo.value) != mensaje_esperado


def test_load_contract_archivo_sin_nombre_m06(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 11 (TSK-24, CA-10): YAML de **2** archivos donde el **segundo**
    (índice 1) omite la clave `nombre` -> `ContractSchemaError` con el texto
    literal **M-06** exacto (`archivo[1]: falta el campo requerido 'nombre'
    (Field required)`): el localizador **degrada limpio al índice** cuando
    no hay `nombre` con qué identificar el archivo (D-25a).

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es válido
    y completo (nombre + una columna completa); `archivos[1]` declara
    `columnas` (una columna válida y completa) pero **no** declara `nombre`.
    Sin `columnas` residual en la raíz de `contract_data` (para no disparar
    M-02/M-13, fuera de alcance de este caso).

    Este caso **espera código real** (no es caracterización; plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23): hoy `_mensaje_esquema` no
    conoce ningún localizador `archivo[i]` -- la rama `missing` de nivel
    archivo (`loc == ("archivos", i, "nombre")`) no existe todavía (TSK-25,
    diferida) -- así que Pydantic sí rechaza el archivo sin `nombre`
    (`ValidationError`, `type == "missing"`, `loc == ("archivos", 1,
    "nombre")`) y `load_contract` sí lanza `ContractSchemaError`, pero el
    traductor cae al `fallback` genérico (`columna de índice ?, campo
    'nombre': Field required`), que **no** coincide con el texto literal
    M-06 -- la aserción de igualdad exacta de mensaje falla. No es un
    `ImportError` ni un error de sintaxis del test: es exactamente el
    defecto que TSK-25 (`tdd_coder`, GREEN) debe cerrar con
    `_localizador_archivo(indice, archivos_crudos)` + la rama `missing` de
    nivel archivo del traductor.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - columnas:\n"
        "        - nombre: venta_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = "archivo[1]: falta el campo requerido 'nombre' (Field required)"
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_campo_tipo_faltante(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 16 (TSK-33, CA-15, M-09, endurecido): columna que omite `tipo`,
    dentro de un archivo, -> `ContractSchemaError` con el texto literal
    **M-09** exacto (`archivo[0] 'archivo.csv', columna de índice 1: falta
    el campo requerido 'tipo' (Field required)`).

    Endurecido desde la aserción de subcadena heredada de la migración de
    forma (TSK-03, Caso 1) al texto literal reordenado M-09 (plan.md,
    "Estrategia de migración de los tests"): la frase vigente antes de este
    caso era `falta el campo requerido 'tipo' en la columna de índice 1`
    (sin el archivo); M-09 antepone el localizador de archivo
    (`archivo[i] '<nombre>'`) y usa una coma antes de "columna de índice".

    YAML sintético (sin PII, C-01) con dos columnas dentro de un único
    archivo declarativo (`archivo.csv`, índice 0): la de índice 0
    (`test_id`) es válida y completa; la de índice 1 (`correo`) omite el
    campo requerido `tipo`. `load_contract` no debe retornar objeto (la
    excepción se lanza); además la excepción debe ser exactamente
    `ContractSchemaError`, no un `pydantic.ValidationError` crudo.

    Este caso **espera código real** (TSK-34): hoy `_mensaje_esquema(exc,
    archivos_crudos)` no tiene ninguna rama `missing` de **nivel columna**
    (`loc == ('archivos', i, 'columnas', j, campo)`); cae al fallback
    genérico de columna (`falta el campo requerido '{campo}' en la columna
    de índice {indice} ({msg})`, con `indice = loc[1]` = **índice de
    archivo**, no de columna) -- que además, al no tener el localizador de
    archivo, difiere del texto M-09 exacto. La aserción de igualdad exacta
    de mensaje falla por contenido, no por `ImportError` ni `DID NOT RAISE`.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "        - nombre: correo\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        f"archivo[0] '{_NOMBRE_ARCHIVO_UNICO}', columna de índice 1: "
        "falta el campo requerido 'tipo' (Field required)"
    )
    assert str(exc_info.value) == mensaje_esperado


@pytest.mark.parametrize(
    ("campo_faltante", "texto_columna_incompleta"),
    [
        (
            "nombre",
            "        - tipo: string\n"
            "          nulable: true\n"
            "          llave: false\n",
        ),
        (
            "nulable",
            "        - nombre: correo\n"
            "          tipo: string\n"
            "          llave: false\n",
        ),
        (
            "llave",
            "        - nombre: correo\n"
            "          tipo: string\n"
            "          nulable: true\n",
        ),
    ],
)
def test_load_contract_otros_campos_faltantes(
    write_contract_yaml: Callable[..., Path],
    campo_faltante: str,
    texto_columna_incompleta: str,
) -> None:
    """Caso 16 (TSK-33, CA-15, M-09, endurecido): columna que omite `nombre`/
    `nulable`/`llave` (los otros tres campos requeridos, distintos de `tipo`)
    -> `ContractSchemaError` con el texto literal **M-09** exacto
    (`archivo[0] 'archivo.csv', columna de índice 1: falta el campo
    requerido '<campo>' (Field required)`).

    Endurecido desde la aserción de subcadena heredada de la migración de
    forma (TSK-03, Caso 1) al texto literal M-09 (mismo endurecimiento que
    `test_load_contract_campo_tipo_faltante`, solo que aquí varía el campo
    requerido bajo prueba).

    YAML sintético (sin PII, C-01) con dos columnas dentro de un único
    archivo declarativo (`archivo.csv`, índice 0): la de índice 0
    (`test_id`) es válida y completa; la de índice 1 omite el campo
    requerido bajo prueba (`nombre`, `nulable` o `llave`). `load_contract`
    no debe retornar objeto (se lanza la excepción), y ésta debe ser
    exactamente `ContractSchemaError`, no un `pydantic.ValidationError`
    crudo.

    Este caso **espera código real** (TSK-34), misma razón que
    `test_load_contract_campo_tipo_faltante`: falta la rama `missing` de
    nivel columna del traductor que compone M-09 con el localizador de
    archivo + índice de columna.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        + texto_columna_incompleta
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        f"archivo[0] '{_NOMBRE_ARCHIVO_UNICO}', columna de índice 1: "
        f"falta el campo requerido '{campo_faltante}' (Field required)"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_columna_sin_tipo_m09(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 16 (TSK-33, CA-15): YAML de **2** archivos donde la columna de
    índice 1 de `ventas.csv` (índice 1 de `archivos`) omite `tipo` ->
    `ContractSchemaError` con el texto literal **M-09** exacto
    (`archivo[1] 'ventas.csv', columna de índice 1: falta el campo
    requerido 'tipo' (Field required)`): el nombre del archivo aparece
    **aunque Pydantic no lo reporte** en el `ValidationError` (D-25, hallazgo
    3) -- se recupera del YAML crudo por índice, igual que en M-06/M-07/M-08.

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es válido
    y completo (nombre + una columna completa); `archivos[1]`
    (`ventas.csv`) declara dos columnas -- la de índice 0 (`venta_id`) es
    válida y completa, la de índice 1 (`monto`) omite el campo requerido
    `tipo`. Sin `columnas` residual en la raíz de `contract_data` (para no
    disparar M-02/M-13, fuera de alcance de este caso).

    Este caso **espera código real** (no es caracterización; plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23): hoy `_mensaje_esquema`
    (`contract.py`) no tiene ninguna rama de **nivel columna** que use
    `_localizador_archivo` -- solo las ramas de nivel archivo (`len(loc) ==
    3`) lo invocan. Con `loc == ('archivos', 1, 'columnas', 1, 'tipo')`
    (`len(loc) == 5`), el `type == 'missing'` cae al `fallback` genérico
    (`falta el campo requerido 'tipo' en la columna de índice {indice}
    ({msg})`, con `indice = loc[1] == 1` -- el índice de **archivo**, no de
    columna, por coincidencia numérica igual a 1 en este fixture, pero sin
    el localizador `archivo[i] '<nombre>'` ni la coma que exige M-09). La
    aserción de igualdad exacta de mensaje falla por contenido (formato
    distinto, sin el prefijo de archivo); no es un `ImportError` ni un
    error de sintaxis del test, ni un `DID NOT RAISE` (sí se lanza
    `ContractSchemaError`, solo que con el mensaje equivocado). Es
    exactamente el defecto que TSK-34 (`tdd_coder`, GREEN) debe cerrar con
    el cambio de firma `_mensaje_esquema(exc, archivos_crudos)` (ya
    vigente desde el Caso 9) y una rama `missing` de nivel columna nueva
    (`loc == ('archivos', i, 'columnas', j, campo)`) que componga M-09 con
    `_localizador_archivo(i, archivos_crudos)` + `columna de índice {j}`.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - nombre: ventas.csv\n"
        "      columnas:\n"
        "        - nombre: venta_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "        - nombre: monto\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv', columna de índice 1: falta el campo "
        "requerido 'tipo' (Field required)"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_columnas_vacias_en_archivo_m07(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 12 (TSK-26, CA-11): `archivos[1]` (`ventas.csv`) declara
    `columnas: []` -> `ContractSchemaError` con el texto literal **M-07**
    exacto (`archivo[1] 'ventas.csv': la lista de columnas no puede estar
    vacía`): el localizador identifica el archivo por **índice y nombre**
    (D-25a), no solo por índice como en M-06 (Caso 11, archivo sin
    `nombre`).

    **Endurece a igualdad exacta** la aserción de subcadena que TSK-03
    (Caso 1, migración de forma) dejó deliberadamente relajada en este
    mismo test (entonces `test_load_contract_lista_vacia`, ver
    plan.md "Estrategia de migración de los tests" e inventario de
    migración). Reemplaza ese test: mismo comportamiento (`columnas: []`),
    ahora con el fixture de **2** archivos que exige el texto literal
    (`archivos[0]` válido, `archivos[1]` con `columnas` vacía) en vez del
    de un solo archivo (que solo probaba la subcadena).

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es
    válido y completo (nombre + una columna completa); `archivos[1]`
    (`ventas.csv`) declara `nombre` pero su `columnas` es la lista vacía.
    Sin `columnas` residual en la raíz de `contract_data` (para no disparar
    M-02/M-13, fuera de alcance de este caso). La excepción debe ser
    exactamente `ContractSchemaError` (no un `pydantic.ValidationError`
    crudo); `load_contract` no debe retornar objeto.

    Este caso **espera código real** (no es caracterización; plan.md lo
    lista junto a 1/6/7/8/9/10/11/12/14/16/17/23): el `field_validator`
    `_columnas_no_vacias` (mudado a `ArchivoContrato` desde TSK-05, Caso 1)
    sí rechaza la lista vacía y sí lanza `ContractSchemaError`, pero
    `_mensaje_esquema` de hoy solo reconoce el `loc` plano `("columnas",)`
    para propagar el mensaje del validador sin envoltura (línea vigente
    `loc in (("columnas",), ("archivos",))`); en la forma multi-archivo,
    Pydantic reporta `loc == ("archivos", 1, "columnas")` (anidado dentro
    de `ArchivoContrato`), que **no** coincide con ese `loc` plano y por lo
    tanto cae al `fallback` genérico de columna (`columna de índice ?,
    campo 'columnas': ...`), sin el localizador `archivo[i] '<nombre>'` que
    exige M-07. La aserción de igualdad exacta de mensaje falla: no es un
    `ImportError` ni un error de sintaxis del test, sino exactamente el
    defecto que TSK-27 (`tdd_coder`, GREEN) debe cerrar añadiendo la rama
    `value_error` de **nivel archivo** (`loc == ("archivos", i,
    "columnas")`) que antepone `_localizador_archivo` (TSK-25, ya
    implementado) al mensaje del validador mudado.
    """
    texto = (
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
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_archivo_sin_columnas_m08(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 13 (TSK-28, CA-12): `archivos[1]` (`ventas.csv`) **omite la
    clave** `columnas` (a diferencia del Caso 12, donde la clave está
    presente pero vacía) -> `ContractSchemaError` con el texto literal
    **M-08** exacto (`archivo[1] 'ventas.csv': falta el campo requerido
    'columnas' (Field required)`).

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es válido
    y completo (nombre + una columna completa); `archivos[1]` declara
    `nombre: ventas.csv` pero **no** declara la clave `columnas` en
    absoluto. Sin `columnas` residual en la raíz de `contract_data` (para no
    disparar M-02/M-13, fuera de alcance de este caso).

    `plan.md` marca TSK-29 (lado de código) como `(car?)` -- candidata a
    caracterización, "probablemente ya satisfecha por TSK-25, que solo
    difiere en el campo" -- pero **no** lo es: `_localizador_archivo` (TSK-25)
    solo se invoca hoy desde dos ramas del traductor, ambas con guarda
    explícita sobre `loc[2]`: la rama `missing` de nivel archivo exige
    `loc[2] == "nombre"` (TSK-25, Caso 11) y la rama `value_error` de nivel
    archivo exige `loc[2] == "columnas"` **con** `tipo_error == "value_error"`
    (TSK-27, Caso 12, columna presente pero vacía). Aquí Pydantic reporta
    `type == "missing"` con `loc == ("archivos", 1, "columnas")` (la clave
    falta, no está vacía): ese `loc` no coincide con ninguna de las dos
    guardas -- `loc[2] == "columnas"` pero `tipo_error != "value_error"`, y
    `loc[2] != "nombre"` para la rama `missing`-- así que cae al `fallback`
    genérico de columna (`columna de índice ?, campo 'columnas': Field
    required`), sin el localizador `archivo[i] '<nombre>'` que exige M-08.
    Verificado con inyección temporal (L-10): revirtiendo a mano el guard de
    la rama `missing` de nivel archivo a `loc[2] in ("nombre", "columnas")`
    el test pasa a verde, confirmando que el defecto real es la ausencia de
    esa generalización (o de una rama `missing` propia) en el traductor
    vigente -- no un defecto de `_localizador_archivo` en sí, que ya
    funciona igual en ambos casos. La aserción de igualdad exacta de mensaje
    falla por contenido (`fallback` genérico obtenido vs M-08 esperado); no
    es un `ImportError` ni un error de sintaxis del test, ni un `DID NOT
    RAISE` (sí se lanza `ContractSchemaError`, solo que con el mensaje
    equivocado). Este caso **espera código real**: TSK-29 debe quedar
    `implementada`, no `cancelada_suspendida`.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - nombre: ventas.csv\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv': falta el campo requerido 'columnas' "
        "(Field required)"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_archivo_duplicado_no_adyacente_m05(
    write_contract_yaml: Callable[..., Path],
    clientes_columnas: list[dict],
    ventas_columnas: list[dict],
) -> None:
    """Caso 14 (TSK-30, CA-13): contrato de **3** archivos con la colisión de
    `nombre` **no adyacente** (`ventas.csv` en el índice 0, `clientes.csv`
    válido y distinto en el índice 1, `ventas.csv` de nuevo en el índice 2)
    -> `ContractSchemaError` con el texto literal **M-05** exacto
    (`nombre de archivo duplicado: 'ventas.csv'`), error de **nivel raíz**
    (sin prefijo `archivo[i]`); `load_contract` no retorna objeto.

    La no adyacencia es **deliberada** (endurecimiento del gate, paso 9,
    Riesgo Técnico 7 de `plan.md`): con dos `ventas.csv` **contiguos** en una
    lista de 2, un detector defectuoso que solo compare el par vecino
    (`archivos[i].nombre == archivos[i+1].nombre`) pasaría en verde sin ver
    el duplicado. Al separar las dos apariciones de `ventas.csv` con un
    archivo válido y distinto (`clientes.csv`) en medio, este test **mata**
    esa implementación por pares adyacentes: solo un detector que recorra
    **toda la lista** (p. ej. acumulando un conjunto/contador de los
    nombres ya vistos) detecta la colisión de los índices 0 y 2.

    Reutiliza `write_contract_yaml` (TSK-01) vía `archivos=` (sin fixtures
    nuevos en disco, C-01): las columnas de cada archivo son las fixtures
    sintéticas ya existentes (`ventas_columnas`, `clientes_columnas`),
    reutilizadas dos veces para las dos apariciones de `ventas.csv` -- el
    contenido de `columnas` es irrelevante para este comportamiento (la
    colisión se decide por `nombre` de archivo, cadena exacta, D-25b); lo
    único que importa es que ambas entradas declaren `nombre: ventas.csv`.

    Estado de producción al momento de escribir este test (RED esperado):
    `Contract` aún no tiene ningún `field_validator` sobre `archivos` que
    detecte nombres duplicados (`_archivos_sin_duplicados`, TSK-31, no
    implementado) -- un YAML de 3 archivos sintácticamente válido con
    `nombre` repetido hoy carga **sin excepción**, así que se espera que
    `pytest.raises(ContractSchemaError)` falle con `DID NOT RAISE` (o
    equivalente), no con un `ImportError` ni un error de sintaxis del test.
    """
    archivos = [
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
        {"nombre": "clientes.csv", "columnas": clientes_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
    ]
    path = write_contract_yaml(archivos=archivos)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = "nombre de archivo duplicado: 'ventas.csv'"
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_tipo_fuera_de_enum_archivo_del_medio(
    write_contract_yaml: Callable[..., Path],
    clientes_columnas: list[dict],
    catalogo_columnas: list[dict],
) -> None:
    """Caso 17b (TSK-35b, CA-16, M-10): contrato de **3** archivos donde el
    defecto (`tipo: numero_magico`) vive en `archivos[1]` (`ventas.csv`, el
    archivo del **medio**), con `catalogo.csv` **válido detrás**, en
    `archivos[2]` -> `ContractSchemaError` con el MISMO texto literal M-10
    de la spec (`archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo':
    valor 'numero_magico' inválido (Input should be 'string', 'integer',
    'float', 'date', 'datetime' or 'boolean')`).

    Cierra el hueco de cobertura de N >= 3 sobre el localizador de nivel
    columna (gate paso 9, riesgo técnico 7 del plan): el Caso 17 solo
    ejercitaba `archivos[1]` cuando 1 era **también** el índice del último
    archivo de una lista de 2, así que un off-by-one o una implementación
    que reporte "el último archivo" en vez del archivo realmente defectuoso
    pasaba igual. Aquí el índice reportado (1) ya NO coincide con el del
    último archivo (2, `catalogo.csv`, válido): si el localizador reportara
    el último en vez del índice real del error, el mensaje apuntaría a
    `archivo[2] 'catalogo.csv'` en vez de `archivo[1] 'ventas.csv'` y la
    aserción de igualdad exacta fallaría.

    `ventas.csv` reutiliza la misma forma de 2 columnas que el Caso 17
    (`venta_id` válido en índice 0, `monto` con `tipo: numero_magico` en
    índice 1) para conservar el M-10 literal exacto de la spec. `clientes.csv`
    (`clientes_columnas`) y `catalogo.csv` (`catalogo_columnas`) son válidos y
    completos. Reutiliza `write_contract_yaml` (TSK-01) vía `archivos=`; sin
    fixtures nuevos en disco (C-01).

    Candidato serio a **caracterización** (L-13/L-14, nota del plan): el lado
    de código (TSK-25, localizador `_localizador_archivo`; TSK-36, rama enum
    de nivel columna en `_mensaje_esquema`) ya existe del Caso 17 y ya usa el
    índice real del error (`loc[1]`), no "el último archivo". Si `pytest`
    confirma verde inmediato, la honestidad de este test se verifica por
    inyección/reversión temporal (L-10) de una localización espuria por
    "último archivo" (`len(archivos_crudos) - 1`) y no se fuerza un RED
    artificial.
    """
    ventas_defectuoso = [
        {"nombre": "venta_id", "tipo": "integer", "nulable": False, "llave": True},
        {"nombre": "monto", "tipo": "numero_magico", "nulable": True, "llave": False},
    ]
    archivos = [
        {"nombre": "clientes.csv", "columnas": clientes_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_defectuoso},
        {"nombre": "catalogo.csv", "columnas": catalogo_columnas},
    ]
    path = write_contract_yaml(archivos=archivos)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor "
        "'numero_magico' inválido (Input should be 'string', 'integer', "
        "'float', 'date', 'datetime' or 'boolean')"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_mayusculas_no_son_duplicado(
    write_contract_yaml: Callable[..., Path],
    ventas_columnas: list[dict],
) -> None:
    """Caso 15 (TSK-32, CA-14): `Ventas.csv` y `ventas.csv` difieren **solo**
    en mayúsculas -> cargan **sin error**, `len(archivos) == 2`.

    `_archivos_sin_duplicados` (TSK-31, Caso 14) compara por **cadena
    exacta**, sin normalizar (D-25b/D-23e): `"Ventas.csv" != "ventas.csv"`
    como cadenas Python, así que el conjunto de nombres vistos no los trata
    como colisión. Este test congela ese comportamiento como contrato: el
    **riesgo aceptado** de colisión física entre los dos nombres en el
    sistema de archivos (case-insensitive en Windows/macOS por defecto)
    queda **diferido a `load_data`** (T-59); esta feature no lo resuelve ni
    lo detecta -- de hecho, por diseño, los **acepta**.

    Reutiliza `write_contract_yaml` (TSK-01) vía `archivos=` y la fixture
    sintética `ventas_columnas` ya existente, reutilizada dos veces (el
    contenido de las columnas es irrelevante para este comportamiento; lo
    único que importa es el par de nombres que solo difieren en caja) --
    sin fixtures nuevos en disco (C-01).

    Candidato serio a **caracterización** (L-13/L-14, nota del plan): dado
    que `_archivos_sin_duplicados` ya compara por cadena exacta desde el
    Caso 14 (TSK-31), este par probablemente ya carga sin error como efecto
    colateral del diseño, sin necesitar ningún cambio de producción nuevo
    (TSK-32 es la única tarea de este caso; no hay tarea de código
    hermana). Si `pytest` confirma verde inmediato, la honestidad de este
    test se verifica por inyección/reversión temporal de una comparación
    normalizada (case-insensitive) en `_archivos_sin_duplicados`
    (`app/src/zeroleak/config/contract.py`) y no se fuerza un RED
    artificial.
    """
    archivos = [
        {"nombre": "Ventas.csv", "columnas": ventas_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
    ]
    path = write_contract_yaml(archivos=archivos)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 2
    assert [a.nombre for a in contrato.archivos] == ["Ventas.csv", "ventas.csv"]


def test_load_contract_tipo_fuera_de_enum(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Caso 17 (TSK-35, CA-16, M-10, endurecido): YAML de **2** archivos
    donde la columna de índice 1 de `ventas.csv` (índice 1 de `archivos`)
    declara `tipo: numero_magico`, fuera del enum cerrado de 6 valores
    (D-23b) -> `ContractSchemaError` con el texto literal **M-10** exacto
    (`archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor
    'numero_magico' inválido (Input should be 'string', 'integer', 'float',
    'date', 'datetime' or 'boolean')`).

    Endurecimiento (TSK-03, forma migrada -> forma final): la forma migrada
    solo verificaba subcadenas (`numero_magico`, `1`, los 6 tipos sueltos en
    el mensaje). Esta forma exige **igualdad exacta** con M-10, que compone
    el localizador de archivo (`archivo[1] 'ventas.csv'`), el índice de
    columna (`columna de índice 1`), el campo (`campo 'tipo'`), el valor
    inválido (`valor 'numero_magico' inválido`) y el mensaje nativo de
    Pydantic que ya enumera los 6 tipos permitidos entre paréntesis -- igual
    patrón de composición que M-09 (Caso 16).

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es válido
    y completo (nombre + una columna completa); `archivos[1]` (`ventas.csv`)
    declara dos columnas -- la de índice 0 (`venta_id`) es válida y
    completa, la de índice 1 (`monto`) declara `tipo: numero_magico`, fuera
    del enum. Sin `columnas` residual en la raíz de `contract_data` (para no
    disparar M-02/M-13, fuera de alcance de este caso).

    Este caso **espera código real** (TSK-36, `tdd_coder`, GREEN): hoy
    `_mensaje_esquema` (`contract.py`) no tiene ninguna rama de **nivel
    columna** para `type == 'enum'` -- solo el `fallback` genérico atrapa el
    error de enum, sin componer el localizador de archivo ni el índice de
    columna. La aserción de igualdad exacta de mensaje falla por contenido
    (formato distinto, sin el prefijo de archivo); no es un `ImportError` ni
    un error de sintaxis del test, ni un `DID NOT RAISE` (sí se lanza
    `ContractSchemaError`, solo que con el mensaje equivocado).
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - nombre: ventas.csv\n"
        "      columnas:\n"
        "        - nombre: venta_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "        - nombre: monto\n"
        "          tipo: numero_magico\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor "
        "'numero_magico' inválido (Input should be 'string', 'integer', "
        "'float', 'date', 'datetime' or 'boolean')"
    )
    assert str(exc_info.value) == mensaje_esperado


def test_load_contract_duplicados_exactos(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 18 (CA-17, M-11, endurecido): `ventas.csv`
    declara dos veces la columna `venta_id` dentro de un YAML de **2**
    archivos -> `ContractSchemaError` con el texto literal **M-11** exacto
    (`archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'`).

    Endurecimiento (TSK-37, forma migrada -> forma final): la forma migrada
    solo verificaba `"test_id" in mensaje` (subcadena, con un fixture de un
    solo archivo, sin localizador). Esta forma exige **igualdad exacta** con
    M-11, que compone el localizador de archivo (`archivo[1] 'ventas.csv'`,
    D-25a) antepuesto al mensaje del validador mudado a `ArchivoContrato`
    (`_columnas_sin_duplicados`), mismo patrón de composición que M-07
    (Caso 12): ambos comparten la rama `value_error` de nivel archivo con
    `loc == ("archivos", i, "columnas")` en `_mensaje_esquema`.

    YAML sintético (sin PII, C-01): `archivos[0]` (`clientes.csv`) es válido
    y completo (nombre + una columna completa); `archivos[1]` (`ventas.csv`)
    declara dos columnas con el mismo `nombre` exacto (`venta_id`, D-23e:
    comparación de cadena exacta, sin normalizar mayúsculas ni espacios).

    Candidato a **caracterización** (nota del plan, L-13/L-14): el
    validador `_columnas_sin_duplicados` ya vive en `ArchivoContrato` desde
    el Caso 1 (TSK-05) y la rama `value_error` de nivel archivo de
    `_mensaje_esquema` ya antepone `_localizador_archivo` desde el Caso 12
    (TSK-27, M-07). Es probable que el mensaje M-11 ya salga correcto por
    efecto colateral de ambos, sin código de producción nuevo (TSK-38 queda
    `(car?)`). Si `pytest` confirma verde inmediato, no es un `ImportError`
    ni un error de sintaxis del test: es una aserción de igualdad exacta que
    ya se cumple con el código vigente.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: clientes.csv\n"
        "      columnas:\n"
        "        - nombre: cliente_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "    - nombre: ventas.csv\n"
        "      columnas:\n"
        "        - nombre: venta_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "        - nombre: venta_id\n"
        "          tipo: string\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje_esperado = (
        "archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'"
    )
    assert str(exc_info.value) == mensaje_esperado


@pytest.mark.parametrize(
    ("nombre_a", "nombre_b"),
    [
        ("test_id", "Test_ID"),
        ("test_id", "test_id "),
    ],
    ids=["mayusculas", "espacio_final"],
)
def test_load_contract_no_duplicado_por_caso_o_espacio(
    write_contract_yaml: Callable[..., Path],
    nombre_a: str,
    nombre_b: str,
) -> None:
    """Destino final: Caso 18, regresión (CA-25): `nombre` que difiere solo en
    mayúsculas o espacios NO se considera duplicado (comparación exacta,
    D-23e; TSK-03: forma migrada).

    YAML sintético (sin PII, C-01) con dos columnas válidas y completas,
    dentro de un único archivo, cuyo `nombre` difiere únicamente en
    capitalización (`test_id` vs `Test_ID`) o en un espacio final (`test_id`
    vs `test_id `). `load_contract` debe aceptar el YAML y devolver un
    `Contract` con las dos columnas dentro de ese archivo (no debe lanzar
    `ContractSchemaError` por duplicado); el validador mudado a
    `ArchivoContrato` compara por cadena exacta, sin normalizar.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
        "      columnas:\n"
        f"        - nombre: {nombre_a}\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        f"        - nombre: '{nombre_b}'\n"
        "          tipo: string\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    contrato = load_contract(path)

    assert len(contrato.archivos) == 1
    columnas = contrato.archivos[0].columnas
    assert len(columnas) == 2
    assert columnas[0].nombre == nombre_a
    assert columnas[1].nombre == nombre_b


def test_load_contract_fail_fast_un_solo_error(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 20 (CA-21): YAML que viola >1 regla simultáneamente,
    dentro de un archivo, -> **una única** `ContractSchemaError` con **un**
    primer error, sin lista agregada (fail-fast, D-23c; TSK-03: forma migrada).

    YAML sintético (sin PII, C-01) con tres columnas dentro de un único
    archivo: la de índice 0 (`test_id`) es válida y completa; la de índice 1
    (`correo`) omite el campo requerido `tipo`; y dos columnas (índices 0 y
    2) comparten el mismo `nombre` exacto (`test_id`), violando también la
    regla de duplicados. Es decir, el YAML viola **más de una** regla a la
    vez, tal como pide el criterio.

    El test **no** verifica cuál de los dos errores "gana"; verifica
    **cardinalidad**: se lanza exactamente una excepción `ContractSchemaError`
    (nunca una `pydantic.ValidationError` cruda con su cadena "N validation
    errors for ..."), y su mensaje corresponde a **un solo** error.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "          nulable: false\n"
        "          llave: true\n"
        "        - nombre: correo\n"
        "          nulable: true\n"
        "          llave: false\n"
        "        - nombre: test_id\n"
        "          tipo: string\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    excepciones = exc_info.value
    # Cardinalidad: una única excepción (no una colección/lista de errores).
    assert isinstance(excepciones, ContractSchemaError)
    assert not isinstance(excepciones, (list, tuple))

    mensaje = str(excepciones)
    mensaje_normalizado = mensaje.lower()
    # No debe colarse la cadena de agregación multi-error nativa de Pydantic
    # (p. ej. "2 validation errors for Contract").
    assert "validation error" not in mensaje_normalizado
    assert "errors for" not in mensaje_normalizado
    # Un solo error legible: sin múltiples líneas de detalle apiladas.
    assert mensaje.count("\n") == 0


def test_load_contract_yaml_roto_parse_error(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 19 (CA-18, M-12): YAML sintácticamente roto ->
    `ContractParseError`, no `ContractSchemaError` (sin cambios de forma:
    el parseo ocurre antes de la extracción de `archivos[]`).

    Texto YAML sintético (sin PII, C-01) con indentación/estructura inválida:
    una clave de mapeo (`llave: true`) aparece al mismo nivel que un elemento
    de secuencia (`- nombre: ...`) sin el guion de lista, lo que rompe la
    sintaxis YAML (`yaml.safe_load` debe lanzar `yaml.YAMLError` al
    parsearlo, antes de llegar siquiera a validar el esquema). `load_contract`
    debe traducir ese error de parseo a `ContractParseError` -- y **no** a
    `ContractSchemaError` -- distinguibles por tipo (HU-07): se verifica
    explícitamente que la excepción capturada es `ContractParseError`, que
    NO es instancia de `ContractSchemaError`, y que ambos tipos no comparten
    relación de herencia entre sí. `load_contract` no debe retornar objeto.
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: archivo.csv\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "        nulable: false\n"
        "          llave: true\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractParseError) as exc_info:
        load_contract(path)

    excepcion = exc_info.value
    assert isinstance(excepcion, ContractParseError)
    assert not isinstance(excepcion, ContractSchemaError)
    assert not issubclass(ContractParseError, ContractSchemaError)
    assert not issubclass(ContractSchemaError, ContractParseError)


def test_load_contract_parse_error_mensaje_accionable(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 19 (CA-18): el mensaje de `ContractParseError` es
    claro y accionable -- referencia explícitamente que el YAML es
    sintácticamente inválido, en vez de propagar únicamente el texto crudo
    del parser subyacente (PyYAML). Sin cambios de forma respecto del
    esquema viejo (el parseo ocurre antes de `archivos[]`).

    Reutiliza el mismo YAML sintéticamente roto del test anterior
    (indentación inválida: una clave de mapeo al mismo nivel que un elemento
    de secuencia sin su guion de lista). No se ata al string frágil exacto
    que compone PyYAML; en su lugar verifica, de forma robusta e
    insensible a mayúsculas, que el mensaje menciona "YAML" y califica el
    problema como de sintaxis inválida.

    El fixture se escribe deliberadamente con un `filename` sin la
    extensión ".yaml" (`contrato_roto.txt`) para que la palabra "yaml" no
    pueda colarse por accidente desde la ruta del archivo.

    Endurecimiento (Caso 19, M-12): el mensaje debe **anteponer** el prefijo
    literal `el archivo YAML del contrato es sintácticamente inválido` antes
    del detalle crudo de PyYAML (no se fija el detalle completo porque varía
    entre versiones de PyYAML, pero el prefijo accionable sí es exacto).
    """
    texto = (
        "contract_data:\n"
        "  archivos:\n"
        "    - nombre: archivo.csv\n"
        "      columnas:\n"
        "        - nombre: test_id\n"
        "          tipo: integer\n"
        "        nulable: false\n"
        "          llave: true\n"
    )
    path = write_contract_yaml(texto=texto, filename="contrato_roto.txt")

    with pytest.raises(ContractParseError) as exc_info:
        load_contract(path)

    mensaje_original = str(exc_info.value)
    prefijo_esperado = (
        "el archivo YAML del contrato es sintácticamente inválido: "
    )
    assert mensaje_original.startswith(prefijo_esperado), (
        f"el mensaje de ContractParseError debe anteponer el prefijo "
        f"literal M-12 {prefijo_esperado!r}; mensaje actual: "
        f"{mensaje_original!r}"
    )

    mensaje = mensaje_original.lower()
    assert "yaml" in mensaje, (
        f"el mensaje de ContractParseError debe mencionar 'YAML' de forma "
        f"accionable; mensaje actual: {mensaje!r}"
    )
    assert "sintax" in mensaje or "inválid" in mensaje or "invalid" in mensaje, (
        f"el mensaje de ContractParseError debe calificar el problema como "
        f"de sintaxis inválida; mensaje actual: {mensaje!r}"
    )


@pytest.mark.parametrize(
    "texto",
    [
        # Contrato válido (camino feliz), un solo archivo.
        (
            "contract_data:\n"
            "  archivos:\n"
            f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
            "      columnas:\n"
            "        - nombre: test_id\n"
            "          tipo: integer\n"
            "          nulable: false\n"
            "          llave: true\n"
        ),
        # Contrato inválido (columna sin `tipo`, dispara ContractSchemaError).
        (
            "contract_data:\n"
            "  archivos:\n"
            f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
            "      columnas:\n"
            "        - nombre: correo\n"
            "          nulable: true\n"
            "          llave: false\n"
        ),
    ],
    ids=["valido", "invalido_campo_faltante"],
)
def test_load_contract_frontera_no_toca_bronze(
    write_contract_yaml: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
    texto: str,
) -> None:
    """Destino final: Caso 24 (CA-23, guarda L-17): frontera D-21 -- `load_contract`
    no abre ni referencia ninguna ruta bajo `data/bronze/` ni datos reales
    del cliente (TSK-03: forma migrada).

    Instrumenta la apertura de archivos con un espía sobre `open`. Se
    ejecuta `load_contract` tanto sobre un fixture válido como sobre uno
    inválido (capturada aquí para poder inspeccionar igualmente las rutas
    abiertas) y se verifica que: se abrió exactamente **una** ruta (guarda de
    no-vacuidad, L-17), esa única ruta abierta es el propio `path`, y
    **ninguna** ruta abierta contiene el segmento `data/bronze`.
    """
    path = write_contract_yaml(texto=texto)

    rutas_abiertas: list[str] = []
    open_real = builtins.open

    def open_espia(archivo, *args, **kwargs):
        rutas_abiertas.append(str(archivo))
        return open_real(archivo, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", open_espia)

    try:
        load_contract(path)
    except ContractSchemaError:
        # El fixture inválido debe seguir ejerciendo la frontera de lectura
        # aunque falle la validación de esquema (la apertura ya ocurrió).
        pass

    assert rutas_abiertas == [str(path)], (
        f"load_contract debe abrir únicamente su propio contract_data.yaml "
        f"({path}); rutas abiertas observadas: {rutas_abiertas}"
    )
    for ruta in rutas_abiertas:
        ruta_normalizada = ruta.replace("\\", "/")
        assert "data/bronze" not in ruta_normalizada, (
            f"load_contract no debe abrir ninguna ruta bajo data/bronze/ "
            f"(frontera D-21); ruta observada: {ruta!r}"
        )


def test_load_contract_core_invocable_sin_cli(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
) -> None:
    """Destino final: Caso 22 (CA-27): `load_contract` es invocable
    **directamente** como función Python (sin argv, subprocess ni fachada
    CLI); su firma es `load_contract(path) -> Contract`; y **no** existe un
    comando `zlk contract validate` en esta feature (core-only, D-23d;
    TSK-03: forma migrada).

    Cuatro verificaciones:

    1. **Invocación directa:** se llama `load_contract(path)` en proceso,
       reutilizando el fixture válido de camino feliz (envuelto en un único
       archivo); el resultado es una instancia de `Contract`.
    2. **Firma — parámetros:** `inspect.signature(load_contract)` expone
       exactamente un parámetro llamado `path` (**sin** `estilo`, que era
       solo del spike, D-23d/CA-27).
    3. **Firma — anotación de retorno:** `inspect.signature(load_contract)
       .return_annotation` es exactamente la clase `Contract` (no `Any`,
       no ausente, no una cadena/forward-ref sin resolver).
    4. **Sin fachada CLI:** `zeroleak.cli` no registra ningún subcomando
       `contract`, ni el texto de uso (`_USAGE`) menciona la palabra
       "contract".
    """
    # (1) Invocación directa, sin argv/subprocess/CLI.
    path = write_contract_yaml(
        archivos=[{"nombre": _NOMBRE_ARCHIVO_UNICO, "columnas": contrato_valido_columnas}]
    )
    contrato = load_contract(path)
    assert isinstance(contrato, Contract)

    # (2) Firma: único parámetro `path`.
    firma = inspect.signature(load_contract)
    nombres_parametros = list(firma.parameters.keys())
    assert nombres_parametros == ["path"], (
        f"load_contract debe declarar exactamente el parámetro 'path'; "
        f"parámetros observados: {nombres_parametros}"
    )

    # (3) Firma: la anotación de retorno es exactamente la clase `Contract`.
    assert firma.return_annotation is Contract, (
        f"load_contract debe anotar su retorno como 'Contract' exactamente; "
        f"anotación observada: {firma.return_annotation!r}"
    )

    # (3) Sin fachada CLI: ningún símbolo ni el texto de uso mencionan "contract".
    simbolos_cli = dir(zeroleak_cli)
    simbolos_contract = [s for s in simbolos_cli if "contract" in s.lower()]
    assert simbolos_contract == [], (
        f"zeroleak.cli no debe registrar ningún subcomando 'contract' "
        f"(core-only, D-23d); símbolos encontrados: {simbolos_contract}"
    )
    assert "contract" not in zeroleak_cli._USAGE.lower(), (
        "el texto de uso de zeroleak.cli no debe mencionar 'contract' "
        "(no existe zlk contract validate, D-23d)"
    )


# Nombres de columna ficticios acordados para esta feature (matrices de
# mentiras del spike, ver plan.md "Estrategia de Test" y conftest.py). Sirve
# de lista blanca auditable: si algún fixture futuro introduce un nombre de
# columna fuera de este set (p. ej. un correo real, un nombre completo), este
# test lo detecta como regresión de C-01.
_NOMBRES_COLUMNA_SINTETICOS_PERMITIDOS = {
    "test_id",
    "correo",
    "monto",
    "fecha_alta",
    "activo",
    "creado_en",
    "cliente_id",
    "venta_id",
    "vendida_en",
    "sku",
    "precio",
}

# Patrón de la ruta "prohibida" de C-01: cualquier segmento `clients/<algo>/data/`
# (o su variante con separador `\`), que es exactamente lo que `.gitignore`
# aísla como Bóveda de datos reales por tenant (Medallion, decisions.md D-09/D-11).
_PATRON_RUTA_DATOS_REALES = re.compile(r"clients[\\/][^\\/]+[\\/]data[\\/]")


def test_load_contract_fixtures_sinteticos_sin_pii(
    write_contract_yaml: Callable[..., Path],
    contrato_valido_columnas: list[dict],
    contrato_seis_tipos_columnas: list[dict],
    tmp_path: Path,
) -> None:
    """Destino final: Caso 26 (CA-26): auditoría de cumplimiento C-01 -- todos
    los fixtures usados en los tests de `contract_multifile` (contratos
    válidos e inválidos, de uno y de varios archivos) son YAMLs sintéticos,
    sin PII, y ninguno reside bajo `clients/*/data/` (TSK-03: forma migrada).

    Dos partes: (a) rutas materializadas siempre bajo `tmp_path`, nunca bajo
    `clients/<tenant>/data/`; (b) nombres de columna dentro de la lista
    blanca sintética acordada, sin PII.
    """
    # (a) Ruta del fixture generado desde archivos (camino feliz reutilizado).
    path_desde_archivos = write_contract_yaml(
        archivos=[{"nombre": _NOMBRE_ARCHIVO_UNICO, "columnas": contrato_valido_columnas}]
    )
    # Ruta del fixture generado desde texto crudo (camino usado por los
    # casos de esquema/parseo inválidos).
    path_desde_texto = write_contract_yaml(
        texto=(
            "contract_data:\n"
            "  archivos:\n"
            f"    - nombre: {_NOMBRE_ARCHIVO_UNICO}\n"
            "      columnas: []\n"
        ),
        filename="contrato_auditoria_texto_crudo.yaml",
    )

    for path in (path_desde_archivos, path_desde_texto):
        assert path.is_relative_to(tmp_path), (
            f"el fixture de contract_data.yaml debe materializarse bajo "
            f"tmp_path (área temporal sintética de pytest); ruta observada: "
            f"{path}"
        )
        ruta_normalizada = str(path).replace("\\", "/")
        assert _PATRON_RUTA_DATOS_REALES.search(ruta_normalizada) is None, (
            f"ningún fixture de contract_multifile debe residir bajo "
            f"clients/*/data/ (C-01, Bóveda de datos reales); ruta "
            f"observada: {path}"
        )

    # (b) Nombres de columna dentro de la lista blanca sintética, sin PII.
    for columnas in (contrato_valido_columnas, contrato_seis_tipos_columnas):
        for col in columnas:
            nombre = col["nombre"]
            assert nombre in _NOMBRES_COLUMNA_SINTETICOS_PERMITIDOS, (
                f"columna ficticia fuera de la lista blanca sintética "
                f"acordada (posible PII sin auditar): {nombre!r}"
            )
            assert "@" not in nombre, (
                f"el nombre de columna {nombre!r} parece un correo real, no "
                f"un identificador de columna ficticio"
            )


def test_load_contract_fail_fast_cardinalidad_agnostico_al_orden(
    write_contract_yaml: Callable[..., Path],
    ventas_columnas: list[dict],
) -> None:
    """Caso 20 (TSK-40, CA-21): YAML que viola **dos** reglas a la vez --
    dos archivos `ventas.csv` (nombre duplicado, M-05) **y** un `tipo`
    inválido (`numero_magico`) en una columna del **segundo** `ventas.csv`
    (M-10) -- produce **exactamente una** `ContractSchemaError` con **un
    solo** mensaje, sin lista agregada de errores de Pydantic (fail-fast,
    D-23c).

    **Agnóstico al orden (D-26b, gate paso 7 aprobado)**: la spec relajó
    deliberadamente este CA para no acoplar el test al orden interno de
    ejecución de los `field_validator` de Pydantic (los de lista corren
    DESPUÉS de los de ítem, D-25 hallazgo 4). Este test **no fija** cuál de
    los dos mensajes gana: acepta **M-05 o M-10** como igualmente
    conformes. Lo que sí verifica es la propiedad de fail-fast en sí misma:
    cardinalidad (una sola excepción) y ausencia de agregación (el mensaje
    no es una concatenación/lista de varios errores -- no contiene ambos
    fragmentos M-05 y M-10 a la vez, ni el patrón de PyDantic de "N
    validation errors for").

    El segundo `ventas.csv` reutiliza `ventas_columnas` (TSK-02) con la
    columna de índice 1 (`cliente_id`) mudada a `tipo: numero_magico`, para
    que el M-10 esperado (si gana) sea `archivo[1] 'ventas.csv', columna de
    índice 1, campo 'tipo': valor 'numero_magico' inválido (...)` --
    coherente con el estilo ya congelado en los Casos 16/17. Reutiliza
    `write_contract_yaml` (TSK-01) vía `archivos=`; sin fixtures nuevos en
    disco (C-01).

    Candidato a **caracterización** (marcado `(car?)` en el plan, L-13/L-14):
    el fail-fast ya vigente en `_mensaje_esquema` (que toma `exc.errors()[0]`,
    heredado de `config_contract`, D-23c) ya limita a un solo mensaje por
    diseño, sin necesitar código nuevo. Si `pytest` confirma verde
    inmediato, la honestidad de este test se verifica por inyección/
    reversión temporal (L-10): se inyecta un defecto en `_mensaje_esquema`
    (`app/src/zeroleak/config/contract.py`) que agregue **todos** los
    mensajes de `exc.errors()` en vez de solo el primero, se confirma que
    el test pasa a FAILED, y se revierte de inmediato dejando `contract.py`
    sin diff nuevo.
    """
    ventas_defectuoso = [
        dict(ventas_columnas[0]),
        {**ventas_columnas[1], "tipo": "numero_magico"},
        dict(ventas_columnas[2]),
        dict(ventas_columnas[3]),
    ]
    archivos = [
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_defectuoso},
    ]
    path = write_contract_yaml(archivos=archivos)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)

    mensaje_m05 = "nombre de archivo duplicado: 'ventas.csv'"
    mensaje_m10 = (
        "archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor "
        "'numero_magico' inválido (Input should be 'string', 'integer', "
        "'float', 'date', 'datetime' or 'boolean')"
    )

    assert mensaje in (mensaje_m05, mensaje_m10), (
        f"el único mensaje debe ser exactamente M-05 o exactamente M-10 "
        f"(agnóstico al orden, D-26b), nunca otra cosa; mensaje observado: "
        f"{mensaje!r}"
    )

    # Ausencia de agregación: cardinalidad de un solo error, no una lista.
    assert "\n" not in mensaje, (
        f"el mensaje no debe contener múltiples líneas (indicio de lista "
        f"agregada de errores de Pydantic); mensaje observado: {mensaje!r}"
    )
    assert not ("validation error" in mensaje.lower()), (
        f"el mensaje no debe exponer el resumen agregado nativo de Pydantic "
        f"('N validation errors for ...'); mensaje observado: {mensaje!r}"
    )
    assert not (mensaje_m05 in mensaje and mensaje_m10 in mensaje), (
        f"el mensaje no debe concatenar M-05 y M-10 a la vez (eso sería "
        f"agregación, no fail-fast); mensaje observado: {mensaje!r}"
    )


def test_contract_no_expone_columnas(
    write_contract_yaml: Callable[..., Path],
    archivos_dos_archivos: list[dict],
) -> None:
    """Caso 21 (TSK-41, CA-24): `Contract` **no** expone `columnas` -- ni
    como campo del modelo (`'columnas' not in Contract.model_fields`) ni
    como atributo accesible en una instancia (`AttributeError`). La única
    vía para llegar a las columnas es `archivos[i].columnas` (D-25d, sin
    atajo de compatibilidad hacia el esquema viejo de un solo archivo).

    Candidato a **caracterización** (marcado `(car?)` en el plan, L-13/L-14):
    desde el Caso 1 (TSK-05) `Contract.columnas` ya fue reemplazado por
    `Contract.archivos: list[ArchivoContrato]` sin propiedad de
    compatibilidad, así que se espera verde inmediato. Si es así, la
    honestidad de este test se verifica por inyección/reversión temporal
    (L-10): se inyecta temporalmente en `Contract`
    (`app/src/zeroleak/config/contract.py`) una propiedad de compatibilidad
    `columnas` (p. ej. `@property` que aplane `archivos`), se confirma que
    el test pasa a FAILED, y se revierte de inmediato dejando `contract.py`
    sin diff nuevo.
    """
    assert "columnas" not in Contract.model_fields, (
        "Contract.model_fields no debe declarar 'columnas' (D-25d): la "
        "única vía de acceso a las columnas es archivos[i].columnas; "
        f"campos observados: {sorted(Contract.model_fields)!r}"
    )

    path = write_contract_yaml(archivos=archivos_dos_archivos)
    contrato = load_contract(path)

    with pytest.raises(AttributeError):
        contrato.columnas

    assert not hasattr(contrato, "columnas"), (
        "Contract(...).columnas no debe existir como atributo accesible "
        "(D-25d); hasattr reporta presencia inesperada del atributo"
    )
