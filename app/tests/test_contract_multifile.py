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
    """Destino final: Caso 16 (CA-15, M-09): columna que omite `tipo`, dentro
    de un archivo, -> `ContractSchemaError` (TSK-03: forma migrada, raw YAML
    envuelto en `contract_data.archivos[0].columnas`).

    YAML sintético (sin PII, C-01) con dos columnas: la de índice 0
    (`test_id`) es válida y completa; la de índice 1 (`correo`) omite el
    campo requerido `tipo`. El mensaje de la excepción debe identificar el
    campo faltante (`tipo`) y la columna afectada por índice/posición
    (0-based). `load_contract` no debe retornar objeto (la excepción se
    lanza); además la excepción debe ser exactamente `ContractSchemaError`,
    no un `pydantic.ValidationError` crudo.
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

    mensaje = str(exc_info.value)
    assert "tipo" in mensaje
    assert "1" in mensaje


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
    """Destino final: Caso 16 (CA-15, M-09): columna que omite `nombre`/
    `nulable`/`llave` (los otros tres campos requeridos, distintos de `tipo`)
    -> `ContractSchemaError` (TSK-03: forma migrada).

    YAML sintético (sin PII, C-01) con dos columnas dentro de un único
    archivo: la de índice 0 (`test_id`) es válida y completa; la de índice 1
    omite el campo requerido bajo prueba (`nombre`, `nulable` o `llave`). El
    mensaje debe identificar el campo faltante y la columna afectada por
    índice (0-based); `load_contract` no debe retornar objeto (se lanza la
    excepción), y ésta debe ser exactamente `ContractSchemaError`, no un
    `pydantic.ValidationError` crudo.
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

    mensaje = str(exc_info.value)
    assert campo_faltante in mensaje
    assert "1" in mensaje


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


def test_load_contract_tipo_fuera_de_enum(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 17 (CA-16, M-10): `tipo: numero_magico` (fuera del
    enum de 6 tipos), dentro de un archivo, -> `ContractSchemaError`
    (TSK-03: forma migrada).

    YAML sintético (sin PII, C-01) con dos columnas dentro de un único
    archivo: la de índice 0 (`test_id`) es válida y completa; la de índice 1
    (`correo`) declara un `tipo` que no pertenece al enum cerrado de 6
    valores (D-23b). El mensaje de la excepción debe identificar tres cosas:
    (a) el **valor inválido** declarado (`numero_magico`), (b) la **columna
    afectada** por índice (0-based), y (c) enumerar los **6 valores
    permitidos**. `load_contract` no debe retornar objeto (se lanza la
    excepción), y ésta debe ser exactamente `ContractSchemaError`, no un
    `pydantic.ValidationError` crudo.
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
        "          tipo: numero_magico\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert "numero_magico" in mensaje
    assert "1" in mensaje
    for tipo_valido in TIPOS_PERMITIDOS:
        assert tipo_valido in mensaje


def test_load_contract_duplicados_exactos(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """Destino final: Caso 18 (CA-17, M-11): dos columnas con `nombre`
    idéntico (cadena exacta) dentro de un mismo archivo -> `ContractSchemaError`
    que nombra el duplicado (TSK-03: forma migrada).

    YAML sintético (sin PII, C-01) con dos columnas, ambas válidas y
    completas, pero con el mismo `nombre` exacto (`test_id`) declarado dos
    veces dentro de un único archivo (D-23e: comparación de cadena exacta,
    sin normalizar mayúsculas ni espacios). El mensaje de la excepción debe
    nombrar el `nombre` duplicado (`test_id`); `load_contract` no debe
    retornar objeto (se lanza la excepción), y ésta debe ser exactamente
    `ContractSchemaError`, no un `pydantic.ValidationError` crudo.
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
        "        - nombre: test_id\n"
        "          tipo: string\n"
        "          nulable: true\n"
        "          llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert "test_id" in mensaje


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

    mensaje = str(exc_info.value).lower()
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

    Tres verificaciones:

    1. **Invocación directa:** se llama `load_contract(path)` en proceso,
       reutilizando el fixture válido de camino feliz (envuelto en un único
       archivo); el resultado es una instancia de `Contract`.
    2. **Firma:** `inspect.signature(load_contract)` expone exactamente un
       parámetro llamado `path`.
    3. **Sin fachada CLI:** `zeroleak.cli` no registra ningún subcomando
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
