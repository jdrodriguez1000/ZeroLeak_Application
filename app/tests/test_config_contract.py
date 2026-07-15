"""Tests unitarios de `config_contract` (bucle TDD, `app/tests/test_config_contract.py`).

Cubre los criterios de aceptación `CA-xx` de `610_features/config_contract/spec.md`.
Fixtures 100% sintéticas (regla "Datos en Bóveda", C-01); ver `conftest.py`
(`write_contract_yaml`, `contrato_valido_columnas`).

Caso 1 (TSK-02, CA-01): dado un YAML válido con N columnas, `load_contract`
devuelve un `Contract` con `len(columnas) == N` y en el mismo orden declarado.
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


def test_load_contract_lista_vacia(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """CA-11 (Caso 7, TSK-14): `columnas: []` (lista vacía) -> `ContractSchemaError`.

    YAML sintético (sin PII, C-01) con `contract_data.columnas` presente pero
    vacía. La excepción debe ser exactamente `ContractSchemaError` (no un
    `pydantic.ValidationError` crudo) con el mensaje estable "la lista de
    columnas no puede estar vacía" (D-23e/plan TSK-15); `load_contract` no
    debe retornar objeto (se lanza la excepción).
    """
    texto = "contract_data:\n  columnas: []\n"
    path = write_contract_yaml(texto=texto)

    with pytest.raises(ContractSchemaError) as exc_info:
        load_contract(path)

    mensaje = str(exc_info.value)
    assert mensaje == "la lista de columnas no puede estar vacía"


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


def test_load_contract_duplicados_exactos(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """CA-09 (Caso 8, TSK-16): dos columnas con `nombre` idéntico (cadena
    exacta) -> `ContractSchemaError` que nombra el duplicado.

    YAML sintético (sin PII, C-01) con dos columnas, ambas válidas y
    completas, pero con el mismo `nombre` exacto (`test_id`) declarado dos
    veces (D-23e: comparación de cadena exacta, sin normalizar mayúsculas ni
    espacios). El mensaje de la excepción debe nombrar el `nombre` duplicado
    (`test_id`); `load_contract` no debe retornar objeto (se lanza la
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
        "    - nombre: test_id\n"
        "      tipo: string\n"
        "      nulable: true\n"
        "      llave: false\n"
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
    """CA-10 (Caso 9, TSK-18): `nombre` que difiere solo en mayúsculas o
    espacios NO se considera duplicado (comparación exacta, D-23e).

    YAML sintético (sin PII, C-01) con dos columnas válidas y completas cuyo
    `nombre` difiere únicamente en capitalización (`test_id` vs `Test_ID`) o
    en un espacio final (`test_id` vs `test_id `). `load_contract` debe
    aceptar el YAML y devolver un `Contract` con las dos columnas (no debe
    lanzar `ContractSchemaError` por duplicado); `_columnas_sin_duplicados`
    compara por cadena exacta, sin normalizar mayúsculas ni espacios.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        f"    - nombre: {nombre_a}\n"
        "      tipo: integer\n"
        "      nulable: false\n"
        "      llave: true\n"
        f"    - nombre: '{nombre_b}'\n"
        "      tipo: string\n"
        "      nulable: true\n"
        "      llave: false\n"
    )
    path = write_contract_yaml(texto=texto)

    contrato = load_contract(path)

    assert len(contrato.columnas) == 2
    assert contrato.columnas[0].nombre == nombre_a
    assert contrato.columnas[1].nombre == nombre_b


def test_load_contract_fail_fast_un_solo_error(
    write_contract_yaml: Callable[..., Path],
) -> None:
    """CA-14 (Caso 12, TSK-23): YAML que viola >1 regla simultáneamente ->
    **una única** `ContractSchemaError` con **un** primer error, sin lista
    agregada (fail-fast, D-23c).

    YAML sintético (sin PII, C-01) con tres columnas: la de índice 0
    (`test_id`) es válida y completa; la de índice 1 (`correo`) omite el
    campo requerido `tipo` (viola la regla de campo requerido, CA-04/05); y
    dos columnas (índices 0 y 2) comparten el mismo `nombre` exacto
    (`test_id`), violando también la regla de duplicados (CA-09). Es decir,
    el YAML viola **más de una** regla a la vez, tal como pide el criterio.

    El test **no** verifica cuál de los dos errores "gana" (eso lo decide
    Pydantic/el orden interno, según la nota de riesgo del plan.md); verifica
    **cardinalidad**: se lanza exactamente una excepción `ContractSchemaError`
    (nunca una `pydantic.ValidationError` cruda con su cadena "N validation
    errors for ..."), y su mensaje corresponde a **un solo** error -- no
    contiene la marca de agregación multi-error que compone Pydantic por
    defecto (p. ej. "validation error" / "errors for") ni enumera múltiples
    problemas en líneas separadas.
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
        "    - nombre: test_id\n"
        "      tipo: string\n"
        "      nulable: true\n"
        "      llave: false\n"
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
    """CA-07 (Caso 10, TSK-19): YAML sintácticamente roto -> `ContractParseError`,
    no `ContractSchemaError`.

    Texto YAML sintético (sin PII, C-01) con indentación/estructura inválida:
    una clave de mapeo (`llave: true`) aparece al mismo nivel que un elemento
    de secuencia (`- nombre: ...`) sin el guion de lista, lo que rompe la
    sintaxis YAML (`yaml.safe_load` debe lanzar `yaml.YAMLError` al parsearlo,
    antes de llegar siquiera a validar el esquema). `load_contract` debe
    traducir ese error de parseo a `ContractParseError` -- y **no** a
    `ContractSchemaError` -- distinguibles por tipo (HU-04): se verifica
    explícitamente que la excepción capturada es `ContractParseError`, que
    NO es instancia de `ContractSchemaError`, y que ambos tipos no comparten
    relación de herencia entre sí (no una subclase de la otra). `load_contract`
    no debe retornar objeto (se lanza la excepción).
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "    nulable: false\n"
        "      llave: true\n"
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
    """CA-08 (Caso 11, TSK-21): el mensaje de `ContractParseError` es claro y
    accionable -- referencia explícitamente que el YAML es sintácticamente
    inválido, en vez de propagar únicamente el texto crudo del parser
    subyacente (PyYAML).

    Reutiliza el mismo YAML sintéticamente roto del Caso 10
    (`test_load_contract_yaml_roto_parse_error`, CA-07): indentación inválida
    (una clave de mapeo al mismo nivel que un elemento de secuencia sin su
    guion de lista). No se ata al string frágil exacto que compone PyYAML
    (que hoy habla de "block collection" / "block end", sin mencionar la
    palabra "YAML" ni calificar el problema como de sintaxis inválida para un
    humano no técnico); en su lugar verifica, de forma robusta e
    insensible a mayúsculas, que el mensaje:
    - menciona "YAML" (para que quien lo lea sepa qué formato de archivo
      falló), y
    - califica el problema como de sintaxis inválida (contiene "sintax" o
      alguna variante de "inválid"/"invalid").

    El fixture se escribe deliberadamente con un `filename` sin la
    extensión ".yaml" (`contrato_roto.txt`) para que la palabra "yaml" no
    pueda colarse por accidente desde la ruta del archivo (que PyYAML
    incluye en su mensaje crudo) -- así, si la aserción sobre "yaml" pasa,
    es porque el mensaje compuesto por `load_contract` la menciona a
    propósito, no porque el nombre de archivo contenga la palabra.

    Hoy `load_contract` hace `ContractParseError(str(exc))` con el texto
    crudo de `yaml.YAMLError` (ver TSK-20, Caso 10), que no satisface lo
    anterior -- este test debe fallar en RED hasta que TSK-22 componga un
    mensaje deliberadamente accionable envolviendo ese detalle.
    """
    texto = (
        "contract_data:\n"
        "  columnas:\n"
        "    - nombre: test_id\n"
        "      tipo: integer\n"
        "    nulable: false\n"
        "      llave: true\n"
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
        # Contrato válido (camino feliz).
        (
            "contract_data:\n"
            "  columnas:\n"
            "    - nombre: test_id\n"
            "      tipo: integer\n"
            "      nulable: false\n"
            "      llave: true\n"
        ),
        # Contrato inválido (columna sin `tipo`, dispara ContractSchemaError).
        (
            "contract_data:\n"
            "  columnas:\n"
            "    - nombre: correo\n"
            "      nulable: true\n"
            "      llave: false\n"
        ),
    ],
    ids=["valido", "invalido_campo_faltante"],
)
def test_load_contract_frontera_no_toca_bronze(
    write_contract_yaml: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
    texto: str,
) -> None:
    """CA-12 (Caso 13, TSK-25): frontera D-21 -- `load_contract` no abre ni
    referencia ninguna ruta bajo `data/bronze/` ni datos reales del cliente.

    Instrumenta la apertura de archivos con un espía sobre `open` (el
    builtin usado por `zeroleak.config.contract`, que envuelve al `open`
    real registrando cada ruta abierta antes de delegar). Se ejecuta
    `load_contract` tanto sobre un fixture válido como sobre uno inválido
    (que lanza `ContractSchemaError`, capturada aquí para poder inspeccionar
    igualmente las rutas abiertas) y se verifica que:

    - se abrió exactamente **una** ruta,
    - esa única ruta abierta es el propio `path` pasado (`contract_data.yaml`
      sintético en `tmp_path`, nunca bajo `clients/*/data/`, C-01),
    - **ninguna** ruta abierta contiene el segmento `data/bronze` (ni su
      variante con separador `\\` en Windows) ni referencia datos reales
      del cliente.
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
    """CA-13 (Caso 14, TSK-26): `load_contract` es invocable **directamente**
    como función Python (sin argv, subprocess ni fachada CLI); su firma es
    `load_contract(path) -> Contract`; y **no** existe un comando
    `zlk contract validate` en esta feature (core-only, D-23d).

    Tres verificaciones:

    1. **Invocación directa:** se llama `load_contract(path)` en proceso,
       reutilizando el fixture válido de camino feliz (sin `argv`, sin
       `subprocess.run`, sin pasar por `zeroleak.cli.main`); el resultado es
       una instancia de `Contract`.
    2. **Firma:** `inspect.signature(load_contract)` expone exactamente un
       parámetro llamado `path` (nombre estable de la puerta de entrada
       pública, HU-07) y el retorno inspeccionado en (1) es `Contract`.
    3. **Sin fachada CLI:** `zeroleak.cli` no registra ningún subcomando
       `contract` (ni `contract validate`). El dispatcher de `zeroleak.cli`
       es una serie de funciones `_parse_*_args`/`_dispatch_*` explícitas
       (no hay un registro genérico de subcomandos tipo click/typer group),
       así que se inspecciona el módulo por nombre de símbolo: no debe
       existir ningún atributo cuyo nombre contenga "contract" (p. ej.
       `_parse_contract_args`, `_dispatch_contract`), y el texto de uso
       (`_USAGE`) tampoco debe mencionar la palabra "contract".
    """
    # (1) Invocación directa, sin argv/subprocess/CLI.
    path = write_contract_yaml(columnas=contrato_valido_columnas)
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
    """CA-15 (Caso 15, TSK-27): auditoría de cumplimiento C-01 -- todos los
    fixtures usados en los tests de `config_contract` (contratos válidos e
    inválidos) son YAMLs sintéticos, sin PII, y ninguno reside bajo
    `clients/*/data/`.

    CA-15 mezcla una afirmación **automáticamente verificable** (rutas de
    fixtures) con una afirmación de **higiene de contenido** (nombres de
    columna sin PII real), que sí puede blindarse con una lista blanca
    auditable aunque no exista un detector genérico de PII. Dos partes:

    (a) **Rutas.** El helper `write_contract_yaml` (conftest.py, TSK-01)
    materializa siempre el `contract_data.yaml` bajo `tmp_path` (área
    temporal aislada de pytest, nunca versionada ni real). Se comprueba, para
    un fixture generado desde columnas y otro desde texto crudo (las dos
    formas de uso del helper, usadas en todo `test_config_contract.py`), que
    la ruta resultante: (1) cuelga de `tmp_path`, y (2) no contiene el
    segmento `clients/<tenant>/data/` (ni su variante `\\` en Windows) que es
    exactamente el árbol que `.gitignore` aísla como datos reales por tenant
    (C-01, D-09/D-11) -- esa es la señal automática y estable de "no reside
    bajo clients/*/data/".

    (b) **Contenido sin PII.** Los nombres de columna usados por los dos
    fixtures reutilizables de camino feliz (`contrato_valido_columnas`,
    `contrato_seis_tipos_columnas`) deben pertenecer al set sintético
    acordado (`test_id`, `correo`, `monto`, `fecha_alta`, `activo`,
    `creado_en` -- ficticios, sin valores reales) y ninguno debe parecer un
    valor real (p. ej. contener `@`, que delataría un correo real colado como
    nombre de columna). Esto no prueba que sea imposible introducir PII en el
    futuro, pero convierte cualquier fixture nuevo con un nombre fuera de la
    lista blanca en una regresión detectable, en vez de en un supuesto no
    verificado.
    """
    # (a) Ruta del fixture generado desde columnas (camino feliz reutilizado
    # en CA-01/CA-02/CA-03).
    path_desde_columnas = write_contract_yaml(columnas=contrato_valido_columnas)
    # Ruta del fixture generado desde texto crudo (camino usado por los
    # casos de esquema/parseo inválidos, p. ej. CA-04..CA-09, CA-14).
    path_desde_texto = write_contract_yaml(
        texto="contract_data:\n  columnas: []\n",
        filename="contrato_auditoria_texto_crudo.yaml",
    )

    for path in (path_desde_columnas, path_desde_texto):
        assert path.is_relative_to(tmp_path), (
            f"el fixture de contract_data.yaml debe materializarse bajo "
            f"tmp_path (área temporal sintética de pytest); ruta observada: "
            f"{path}"
        )
        ruta_normalizada = str(path).replace("\\", "/")
        assert _PATRON_RUTA_DATOS_REALES.search(ruta_normalizada) is None, (
            f"ningún fixture de config_contract debe residir bajo "
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
