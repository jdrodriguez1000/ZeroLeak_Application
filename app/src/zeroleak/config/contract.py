"""config.contract — carga y validación de `contract_data.yaml` (D-21/D-22/D-23).

Único punto de entrada: `load_contract(path) -> Contract`. Lee el YAML del
contrato (única ruta que abre; frontera D-21), lo parsea con `yaml.safe_load`
y valida su esquema con Pydantic, devolviendo un `Contract` tipado en memoria.

Nota (paso 10, GREEN, TSK-09/TSK-13/TSK-15/TSK-17/TSK-19/TSK-20/TSK-21/TSK-22/
TSK-23/TSK-25/TSK-27/TSK-29/TSK-30/TSK-31/TSK-33/TSK-34/TSK-35/TSK-36): esta versión cubre
el camino feliz (CA-01 a CA-03:
count, orden, fidelidad de campos y los 6 tipos del enum), la traducción de
esquema para campo requerido faltante (CA-04/CA-05, fail-fast,
`_mensaje_esquema`), para `tipo` fuera del enum cerrado (CA-06), para
`columnas: []`/ausente a nivel de archivo (CA-11, `_columnas_no_vacias`,
M-07 exacto localizando el archivo por índice + nombre con
`_localizador_archivo`), para `archivos: []`/ausente/nula (CA-06/CA-07, M-04
exacto, `_archivos_no_vacia`), para `archivos` presente pero no-lista
(CA-09, M-03 exacto, guarda de tipo en `_normalizar_y_validar_lista_archivos`
antes de Pydantic), para el esquema viejo de un solo archivo (`columnas`
residual en la raíz de `contract_data` sin `archivos` utilizable, CA-08,
M-02 exacto), para el esquema híbrido (`columnas` residual en la raíz Y
`archivos` utilizable a la vez, CA-28, M-13 exacto, `_MENSAJE_HIBRIDO`, rama
complementaria y disjunta de M-02 dentro de
`_rechazar_esquema_viejo_o_hibrido`), para
`nombre` de columna duplicado por cadena exacta (`_columnas_sin_duplicados`:
la comparación ya es exacta, sin normalizar mayúsculas ni espacios), para
YAML sintácticamente inválido, que se distingue como `ContractParseError`
antes de llegar al esquema, con un mensaje accionable que antecede el
detalle crudo de PyYAML (CA-07/CA-08), y para un archivo sin `nombre` dentro
de `archivos[]` (CA-10, M-06 exacto, `_localizador_archivo` degradando
limpio a `archivo[i]` cuando no hay nombre que mostrar, D-25a), y para un
archivo que omite por completo la clave `columnas` (CA-12, M-08 exacto,
misma rama `missing` de nivel archivo que M-06, con el guard ampliado a
`loc[2] in ("nombre", "columnas")`), y para `nombre` de archivo duplicado
por cadena exacta, sobre TODA la lista de `archivos` y no solo pares
adyacentes (CA-13, M-05 exacto, `_archivos_sin_duplicados`: mismo patrón
conjunto/contador que `_columnas_sin_duplicados`, sin normalizar
mayúsculas ni espacios, D-25b/D-23e), y para un campo requerido faltante
dentro de una columna concreta de un archivo concreto (CA-15, M-09 exacto,
rama `missing` de nivel columna con `loc == ("archivos", i, "columnas", j,
campo)`), que localiza el archivo con el mismo `_localizador_archivo`
usado por las ramas de nivel archivo y le antepone `columna de índice {j}`,
de modo que el nombre del archivo aparece en el mensaje aunque Pydantic no
lo reporte en su propio `loc`, y para `tipo` fuera del enum cerrado dentro
de una columna concreta de un archivo concreto (CA-16, M-10 exacto, rama
`enum` de nivel columna con `loc == ("archivos", i, "columnas", j, "tipo")`),
que reutiliza el mismo `_localizador_archivo` y antepone `columna de índice
{j}` antes del valor inválido recibido y el mensaje nativo de Pydantic (que
ya enumera los 6 tipos permitidos), mismo patrón que la rama `missing` de
nivel columna del párrafo anterior.
Queda pendiente el fail-fast ante violaciones múltiples de distinta
naturaleza y las caracterizaciones aún no escritas de la frontera de
lectura y los fixtures sintéticos sin PII. `load_contract(path) -> Contract`
ya es invocable directo, sin fachada CLI (CA-27): su firma expone
únicamente el parámetro `path` y anota su retorno como la clase `Contract`
(módulo sin `from __future__ import annotations`, para que la anotación
cruda de `inspect.signature` no quede diferida como cadena).
"""
from collections.abc import Iterable
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, field_validator

# Catálogo de mensajes congelados M-01..M-13 (spec.md §"Mensajes y textos
# congelados"). Cada texto vive en UN ÚNICO sitio nombrado aquí; el resto del
# módulo solo lo referencia (por `.format(...)` cuando lleva placeholders).
# Los tests fijan estos textos por igualdad EXACTA: no se cambia ni un
# carácter de ninguno al refactorizar, solo su ubicación (TSK-48).
_MENSAJE_YAML_INVALIDO = "el archivo YAML del contrato es sintácticamente inválido"  # M-12
_MENSAJE_RAIZ_INVALIDA = (  # M-01
    "la clave raíz 'contract_data' debe contener un mapa con la lista "
    "'archivos' (se encontró: {cuerpo!r})"
)
_MENSAJE_ESQUEMA_VIEJO = (  # M-02
    "el contrato usa el esquema anterior de un solo archivo: se "
    "encontró 'columnas' en la raíz de 'contract_data'; ahora las "
    "columnas van dentro de 'archivos[]' "
    "(contract_data.archivos[].columnas)"
)
_MENSAJE_ARCHIVOS_NO_LISTA = "'archivos' debe ser una lista (se encontró: {valor!r})"  # M-03
_MENSAJE_ARCHIVOS_VACIA = "la lista de archivos no puede estar vacía"  # M-04
_MENSAJE_ARCHIVO_DUPLICADO = "nombre de archivo duplicado: {nombres}"  # M-05
_MENSAJE_COLUMNAS_VACIA = "la lista de columnas no puede estar vacía"  # M-07
_MENSAJE_COLUMNA_DUPLICADA = "nombre de columna duplicado: {nombres}"  # M-11
_MENSAJE_HIBRIDO = (  # M-13
    "el contrato declara 'archivos[]' y además un 'columnas' "
    "residual en la raíz de 'contract_data': ese bloque no se valida "
    "ni se audita; elimínelo y deje cada columna dentro del archivo "
    "al que pertenece (contract_data.archivos[].columnas)"
)
# M-06, M-08, M-09 y M-10 no son texto fijo: son plantillas que combinan el
# localizador `archivo[i] 'nombre'` (D-25a) con el mensaje nativo de Pydantic
# (`missing`/`enum`), y viven junto a `_mensaje_esquema`, su único sitio de uso.


def _nombres_duplicados(nombres: Iterable[str]) -> str:
    """Comprime un iterable de `nombre` en 'a', 'b' con los REPETIDOS (M-05/M-11).

    Auxiliar cohesivo compartido por `_archivos_sin_duplicados` (nivel
    archivo) y `_columnas_sin_duplicados` (nivel columna, dentro de un mismo
    archivo): ambos comparan por cadena exacta, sin normalizar mayúsculas ni
    espacios (D-25b/D-23e), y solo difieren en qué lista recorren. Devuelve
    ya formateado el fragmento `'x', 'y'` a insertar en M-05/M-11 (cadena
    vacía si no hay duplicados).
    """
    vistos: set[str] = set()
    duplicados: list[str] = []
    for nombre in nombres:
        if nombre in vistos and nombre not in duplicados:
            duplicados.append(nombre)
        vistos.add(nombre)
    return ", ".join(f"'{n}'" for n in duplicados)


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


class ArchivoContrato(BaseModel):
    """Un archivo declarativo del contrato: nombre y sus columnas (D-18).

    Recibe (mudados desde `Contract`, sin reescribir su lógica ni mensajes)
    los dos `field_validator` que validan las columnas de este archivo.
    """

    nombre: str
    columnas: list[Columna]

    @field_validator("columnas")
    @classmethod
    def _columnas_no_vacias(cls, valor: list[Columna]) -> list[Columna]:
        """Rechaza `columnas: []` (CA-11, M-07); mensaje estable (D-23e)."""
        if not valor:
            raise ValueError(_MENSAJE_COLUMNAS_VACIA)
        return valor

    @field_validator("columnas")
    @classmethod
    def _columnas_sin_duplicados(cls, valor: list[Columna]) -> list[Columna]:
        """Rechaza `nombre` duplicado por cadena exacta (CA-17, M-11).

        Compara los `nombre` tal cual, sin normalizar mayúsculas ni espacios.
        """
        duplicados = _nombres_duplicados(columna.nombre for columna in valor)
        if duplicados:
            raise ValueError(_MENSAJE_COLUMNA_DUPLICADA.format(nombres=duplicados))
        return valor


class Contract(BaseModel):
    """Contrato validado: lista de archivos en el orden declarado (CA-01)."""

    archivos: list[ArchivoContrato]

    @field_validator("archivos")
    @classmethod
    def _archivos_no_vacia(cls, valor: list[ArchivoContrato]) -> list[ArchivoContrato]:
        """Rechaza `archivos: []` (CA-06/CA-07); mensaje estable M-04."""
        if not valor:
            raise ValueError(_MENSAJE_ARCHIVOS_VACIA)
        return valor

    @field_validator("archivos")
    @classmethod
    def _archivos_sin_duplicados(cls, valor: list[ArchivoContrato]) -> list[ArchivoContrato]:
        """Rechaza `nombre` de archivo duplicado sobre TODA la lista (CA-13, M-05).

        Recorre la lista completa acumulando un conjunto de nombres ya
        vistos (no compara solo pares adyacentes, Riesgo Técnico 7), por
        cadena exacta, sin normalizar (D-25b/D-23e).
        """
        duplicados = _nombres_duplicados(archivo.nombre for archivo in valor)
        if duplicados:
            raise ValueError(_MENSAJE_ARCHIVO_DUPLICADO.format(nombres=duplicados))
        return valor


class ContractParseError(Exception):
    """El YAML del contrato es sintácticamente inválido (no parsea)."""


class ContractSchemaError(Exception):
    """El YAML parsea pero el esquema del contrato es inválido."""


def load_contract(path: str | Path) -> Contract:
    """Lee, parsea y valida `path` como un `contract_data.yaml`.

    Única ruta que abre (frontera D-21, CA-12). Camino feliz: toma la clave
    raíz `contract_data` -> `archivos`, valida con Pydantic y devuelve el
    `Contract` tipado.
    """
    with open(path, "r", encoding="utf-8") as fh:
        try:
            crudo = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ContractParseError(
                f"{_MENSAJE_YAML_INVALIDO}: {exc}"
            ) from exc

    cuerpo = _extraer_cuerpo_contract_data(crudo)
    _rechazar_esquema_viejo_o_hibrido(cuerpo)
    archivos = _normalizar_y_validar_lista_archivos(cuerpo)
    try:
        return Contract.model_validate({"archivos": archivos})
    except ValidationError as exc:
        raise ContractSchemaError(_mensaje_esquema(exc, archivos)) from exc


def _extraer_cuerpo_contract_data(crudo: object) -> dict:
    """Extracción defensiva por tipo de `contract_data` (T-56, D-25, M-01).

    Comprueba con `isinstance` que la raíz del YAML y luego `contract_data`
    sean un mapa antes de tocarlos, para nunca encadenar `.get(...).get(...)`
    sobre un valor nulo o no-mapa y así jamás propagar un `AttributeError`
    (CA-19, CA-20).
    """
    raiz = crudo if isinstance(crudo, dict) else {}
    cuerpo = raiz.get("contract_data")
    if not isinstance(cuerpo, dict):
        raise ContractSchemaError(_MENSAJE_RAIZ_INVALIDA.format(cuerpo=cuerpo))
    return cuerpo


def _rechazar_esquema_viejo_o_hibrido(cuerpo: dict) -> None:
    """Rechaza el esquema anterior (M-02) y el híbrido (M-13, D-26).

    Si `contract_data` todavía declara `columnas` en su raíz, se bifurca por
    la utilizabilidad de `archivos` ANTES de la normalización/guarda de
    `_normalizar_y_validar_lista_archivos`, para no dejar caer el flujo en
    silencio hacia M-04 (lista vacía). Rama 'archivos' NO utilizable
    (ausente, nula o lista vacía) -> M-02 (Caso 9, TSK-21, D-25c). Rama
    'archivos' SÍ utilizable (lista no vacía) es el híbrido M-13 (Caso 10,
    TSK-23, D-26): el residual `columnas` nunca se ignora en silencio, se
    rechaza aquí mismo, contigua y disjunta de la rama M-02. No hace nada
    (sigue el flujo normal) si `columnas` no está en la raíz.
    """
    if "columnas" not in cuerpo:
        return
    archivos_residual = cuerpo.get("archivos")
    archivos_utilizable = (
        isinstance(archivos_residual, list) and len(archivos_residual) > 0
    )
    if not archivos_utilizable:
        raise ContractSchemaError(_MENSAJE_ESQUEMA_VIEJO)
    raise ContractSchemaError(_MENSAJE_HIBRIDO)


def _normalizar_y_validar_lista_archivos(cuerpo: dict) -> list:
    """Normaliza `archivos` nulo a `[]` (M-04) y rechaza no-lista (M-03).

    Ausente o nula (`None`) se normaliza a `[]` (TSK-17, Caso 7): así ambas
    caen en el mismo camino que la lista explícitamente vacía y producen el
    mensaje de negocio M-04, en vez de un error de tipo genérico de Pydantic
    para el caso nulo. Tras la normalización, si `archivos` sigue presente
    pero no es una lista (p. ej. una cadena), se rechaza aquí con el mensaje
    de negocio M-03 (TSK-19, Caso 8) antes de llegar a Pydantic, que solo
    reportaría un error de tipo genérico (`list_type`) no traducido por
    `_mensaje_esquema`. Una lista vacía `[]` no es no-lista y sigue su
    camino normal hacia M-04 (dentro de Pydantic, `_archivos_no_vacia`).
    """
    archivos = cuerpo.get("archivos", [])
    if archivos is None:
        archivos = []
    if not isinstance(archivos, list):
        raise ContractSchemaError(_MENSAJE_ARCHIVOS_NO_LISTA.format(valor=archivos))
    return archivos


def _localizador_archivo(indice: object, archivos_crudos: list) -> str:
    """Devuelve `archivo[i] 'nombre'`, degradando a `archivo[i]` (D-25a).

    Recupera el `nombre` del YAML crudo (no del modelo validado, que puede no
    existir todavía) por índice; si el índice no es válido, o el archivo
    crudo no declara un `nombre` que sea `str` no vacío, degrada limpio a
    `archivo[i]` sin el nombre.
    """
    archivo_crudo = None
    if isinstance(indice, int) and 0 <= indice < len(archivos_crudos):
        archivo_crudo = archivos_crudos[indice]
    nombre = None
    if isinstance(archivo_crudo, dict):
        candidato = archivo_crudo.get("nombre")
        if isinstance(candidato, str) and candidato:
            nombre = candidato
    if nombre is not None:
        return f"archivo[{indice}] '{nombre}'"
    return f"archivo[{indice}]"


# Plantillas de M-06/M-08 (missing nivel archivo), M-09 (missing nivel
# columna) y M-10 (enum nivel columna): a diferencia de M-01..M-05/M-07/M-11
# (arriba), estas no son texto fijo -- combinan el localizador
# `archivo[i] 'nombre'` (D-25a) con el `msg`/`input` nativo de Pydantic -- por
# lo que viven junto a `_mensaje_esquema`, su único sitio de uso.
_PLANTILLA_MISSING_NIVEL_ARCHIVO = "{localizador}: falta el campo requerido '{campo}' ({msg})"
_PLANTILLA_MISSING_NIVEL_COLUMNA = (
    "{localizador}, columna de índice {indice_columna}: falta el campo "
    "requerido '{campo}' ({msg})"
)
_PLANTILLA_ENUM_NIVEL_COLUMNA = (
    "{localizador}, columna de índice {indice_columna}, campo '{campo}': "
    "valor '{valor_invalido}' inválido ({msg})"
)


def _loc_nivel_raiz_lista(loc: tuple) -> bool:
    """`loc` de un `value_error` sobre `columnas` o `archivos` completos (M-04/M-07 sin archivo)."""
    return loc in (("columnas",), ("archivos",))


def _loc_nivel_archivo(loc: tuple, campos: tuple[str, ...]) -> bool:
    """`loc` de nivel archivo: `('archivos', i, campo)` con `campo` en `campos`."""
    return len(loc) == 3 and loc[0] == "archivos" and loc[2] in campos


def _loc_nivel_columna(loc: tuple) -> bool:
    """`loc` de nivel columna: `('archivos', i, 'columnas', j, campo)` (M-09/M-10)."""
    return len(loc) == 5 and loc[0] == "archivos" and loc[2] == "columnas"


def _mensaje_esquema(exc: ValidationError, archivos_crudos: list) -> str:
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
    - `value_error` en el campo raíz `archivos` completo (`loc ==
      ("archivos",)`): CA-06/CA-07, el `field_validator` `_archivos_no_vacia`
      (M-04). Mismo trato que `columnas`: el mensaje ya es el texto estable
      del validador, se propaga tal cual.
    - `value_error` de nivel archivo en el campo `columnas` completo (`loc ==
      ("archivos", i, "columnas")`): CA-11, M-07. El `field_validator`
      `_columnas_no_vacias` mudado a `ArchivoContrato` rechaza la lista vacía
      *de ese archivo*; se antepone `_localizador_archivo(i, archivos_crudos)`
      al mensaje del validador, sin la envoltura genérica de "columna de
      índice ..., campo ..." que no aplica (el error no es de una columna
      concreta, sino del campo `columnas` del archivo entero).
    - `missing` de nivel archivo (`loc == ("archivos", i, "nombre")` o `loc ==
      ("archivos", i, "columnas")`): CA-10 (M-06, falta `nombre`) y CA-12
      (M-08, falta la clave `columnas` por completo, a diferencia de CA-11
      donde la clave está presente pero vacía). Ambos casos se localizan con
      `_localizador_archivo(i, archivos_crudos)`; para `nombre` degrada
      limpio a `archivo[i]` (D-25a) porque justo el campo que falta es el
      `nombre`.
    - `missing` de nivel columna (`loc == ("archivos", i, "columnas", j,
      campo)`): CA-15, M-09. Cualquier campo requerido de `Columna` (`nombre`,
      `tipo`, `nulable`, `llave`) ausente en la columna `j` del archivo `i`;
      se localiza con `_localizador_archivo(i, archivos_crudos)` y se agrega
      `columna de índice {j}` antes de nombrar el campo faltante.
    - `enum` de nivel columna (`loc == ("archivos", i, "columnas", j,
      "tipo")`): CA-16, M-10. `tipo` fuera del enum cerrado en la columna `j`
      del archivo `i`; mismo patrón de localización que la rama `missing` de
      nivel columna de arriba (`_localizador_archivo(i, archivos_crudos)` +
      `columna de índice {j}`), agregando el valor inválido recibido
      (`primer_error["input"]`) y el mensaje nativo de Pydantic (que ya
      enumera los 6 valores permitidos).
    - fallback genérico: cualquier otro `type` de error de Pydantic no
      cubierto arriba todavía.
    """
    primer_error = exc.errors()[0]
    loc = primer_error.get("loc", ())
    campo = loc[-1] if loc else "?"
    indice = loc[1] if len(loc) > 1 else "?"
    tipo_error = primer_error.get("type", "")
    msg = primer_error.get("msg", "")
    msg_sin_prefijo = msg.removeprefix("Value error, ")

    if tipo_error == "value_error" and _loc_nivel_raiz_lista(loc):
        return msg_sin_prefijo
    if tipo_error == "value_error" and _loc_nivel_archivo(loc, ("columnas",)):
        localizador = _localizador_archivo(indice, archivos_crudos)
        return f"{localizador}: {msg_sin_prefijo}"
    if tipo_error == "missing" and _loc_nivel_archivo(loc, ("nombre", "columnas")):
        localizador = _localizador_archivo(indice, archivos_crudos)
        return _PLANTILLA_MISSING_NIVEL_ARCHIVO.format(
            localizador=localizador, campo=campo, msg=msg
        )
    if tipo_error == "missing" and _loc_nivel_columna(loc):
        localizador = _localizador_archivo(indice, archivos_crudos)
        return _PLANTILLA_MISSING_NIVEL_COLUMNA.format(
            localizador=localizador, indice_columna=loc[3], campo=campo, msg=msg
        )
    if tipo_error == "missing":
        return (
            f"falta el campo requerido '{campo}' en la columna de índice {indice} "
            f"({msg})"
        )
    if tipo_error == "enum" and _loc_nivel_columna(loc):
        localizador = _localizador_archivo(indice, archivos_crudos)
        return _PLANTILLA_ENUM_NIVEL_COLUMNA.format(
            localizador=localizador,
            indice_columna=loc[3],
            campo=campo,
            valor_invalido=primer_error.get("input", "?"),
            msg=msg,
        )
    if tipo_error == "enum":
        valor_invalido = primer_error.get("input", "?")
        return (
            f"columna de índice {indice}, campo '{campo}': valor '{valor_invalido}' "
            f"inválido ({msg})"
        )
    return f"columna de índice {indice}, campo '{campo}': {msg}"
