"""Pruebas humanas asistidas de la feature `config_contract` (paso 13).

Script autocontenido: crea YAML de contrato *sintéticos* en un directorio
temporal (nunca bajo `clients/*/data/`, C-01), ejercita `load_contract` y
verifica el comportamiento observable de cada criterio de aceptación (CA).
No modifica el repositorio ni toca datos reales.

Uso (desde la raíz del repositorio):

    py -3.13 610_features/config_contract/pruebas_humanas.py

Salida esperada: una línea `[OK]` por prueba y, al final,
`RESULTADO: 7/7 pruebas OK`. Si alguna falla, se marca `[FALLA]` con el
detalle y el script termina con código de salida != 0.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Forzar UTF-8 en consola para que los mensajes con acentos se vean bien
# (en Windows la consola puede venir en cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from zeroleak.config import (  # noqa: E402
    Contract,
    ContractParseError,
    ContractSchemaError,
    load_contract,
)

_TMP = Path(tempfile.mkdtemp(prefix="zlk_pruebas_contract_"))
_fallas: list[str] = []
_ok = 0


def _escribir(nombre: str, texto: str) -> Path:
    ruta = _TMP / f"{nombre}.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def _ok_print(titulo: str, detalle: str) -> None:
    global _ok
    _ok += 1
    print(f"[OK]    {titulo} -> {detalle}")


def _falla(titulo: str, detalle: str) -> None:
    _fallas.append(titulo)
    print(f"[FALLA] {titulo} -> {detalle}")


# --- P1 · CA-01/CA-02/CA-03 · contrato válido (camino feliz) ------------------
VALIDO = """contract_data:
  columnas:
    - nombre: test_id
      tipo: integer
      nulable: false
      llave: true
    - nombre: correo
      tipo: string
      nulable: true
      llave: false
    - nombre: monto
      tipo: float
      nulable: false
      llave: false
"""


def prueba_1_valido() -> None:
    ruta = _escribir("valido", VALIDO)
    try:
        c = load_contract(ruta)
    except Exception as exc:  # noqa: BLE001
        _falla("P1 contrato válido", f"no debía lanzar, lanzó {type(exc).__name__}: {exc}")
        return
    if not isinstance(c, Contract):
        _falla("P1 contrato válido", f"esperaba Contract, obtuvo {type(c).__name__}")
        return
    nombres = [col.nombre for col in c.columnas]
    if nombres != ["test_id", "correo", "monto"]:
        _falla("P1 contrato válido", f"orden/columnas inesperadas: {nombres}")
        return
    col0 = c.columnas[0]
    if not (col0.nombre == "test_id" and col0.tipo.value == "integer"
            and col0.nulable is False and col0.llave is True):
        _falla("P1 contrato válido", f"fidelidad de campos incorrecta en col0: {col0}")
        return
    _ok_print("P1 contrato válido (CA-01/02)", f"Contract con {len(c.columnas)} columnas en orden")


# --- P2 · CA-03 · los 6 tipos del enum ---------------------------------------
SEIS_TIPOS = """contract_data:
  columnas:
    - {nombre: c1, tipo: string,   nulable: false, llave: false}
    - {nombre: c2, tipo: integer,  nulable: false, llave: false}
    - {nombre: c3, tipo: float,    nulable: false, llave: false}
    - {nombre: c4, tipo: date,     nulable: false, llave: false}
    - {nombre: c5, tipo: datetime, nulable: false, llave: false}
    - {nombre: c6, tipo: boolean,  nulable: false, llave: false}
"""


def prueba_2_seis_tipos() -> None:
    ruta = _escribir("seis_tipos", SEIS_TIPOS)
    try:
        c = load_contract(ruta)
    except Exception as exc:  # noqa: BLE001
        _falla("P2 seis tipos", f"no debía lanzar, lanzó {type(exc).__name__}: {exc}")
        return
    tipos = [col.tipo.value for col in c.columnas]
    esperados = ["string", "integer", "float", "date", "datetime", "boolean"]
    if tipos != esperados:
        _falla("P2 seis tipos", f"esperaba {esperados}, obtuvo {tipos}")
        return
    _ok_print("P2 seis tipos del enum (CA-03)", "string/integer/float/date/datetime/boolean aceptados")


# --- P3 · CA-04 · campo requerido faltante -----------------------------------
FALTA_TIPO = """contract_data:
  columnas:
    - nombre: test_id
      tipo: integer
      nulable: false
      llave: true
    - nombre: correo
      nulable: true
      llave: false
"""


def prueba_3_falta_tipo() -> None:
    ruta = _escribir("falta_tipo", FALTA_TIPO)
    try:
        load_contract(ruta)
    except ContractSchemaError as exc:
        msg = str(exc)
        if "tipo" in msg and "1" in msg:
            _ok_print("P3 campo faltante (CA-04)", f"ContractSchemaError: {msg}")
        else:
            _falla("P3 campo faltante", f"mensaje no identifica campo/columna: {msg}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P3 campo faltante", f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}")
        return
    _falla("P3 campo faltante", "no lanzó ninguna excepción (debía fallar)")


# --- P4 · CA-06 · tipo fuera del enum ----------------------------------------
ENUM_INVALIDO = """contract_data:
  columnas:
    - nombre: test_id
      tipo: numero_magico
      nulable: false
      llave: true
"""


def prueba_4_enum_invalido() -> None:
    ruta = _escribir("enum_invalido", ENUM_INVALIDO)
    try:
        load_contract(ruta)
    except ContractSchemaError as exc:
        msg = str(exc)
        if "numero_magico" in msg and "boolean" in msg:
            _ok_print("P4 tipo fuera de enum (CA-06)", f"ContractSchemaError: {msg}")
        else:
            _falla("P4 tipo fuera de enum", f"mensaje no enumera valor inválido/permitidos: {msg}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P4 tipo fuera de enum", f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}")
        return
    _falla("P4 tipo fuera de enum", "no lanzó ninguna excepción (debía fallar)")


# --- P5 · CA-11 · lista de columnas vacía ------------------------------------
LISTA_VACIA = """contract_data:
  columnas: []
"""


def prueba_5_lista_vacia() -> None:
    ruta = _escribir("lista_vacia", LISTA_VACIA)
    try:
        load_contract(ruta)
    except ContractSchemaError as exc:
        if str(exc) == "la lista de columnas no puede estar vacía":
            _ok_print("P5 lista vacía (CA-11)", f"ContractSchemaError: {exc}")
        else:
            _falla("P5 lista vacía", f"mensaje inesperado: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P5 lista vacía", f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}")
        return
    _falla("P5 lista vacía", "no lanzó ninguna excepción (debía fallar)")


# --- P6 · CA-09/CA-10 · duplicado exacto vs mayúsculas/espacios ---------------
DUPLICADO = """contract_data:
  columnas:
    - nombre: test_id
      tipo: integer
      nulable: false
      llave: true
    - nombre: test_id
      tipo: string
      nulable: true
      llave: false
"""

NO_DUPLICADO = """contract_data:
  columnas:
    - nombre: test_id
      tipo: integer
      nulable: false
      llave: true
    - nombre: Test_ID
      tipo: string
      nulable: true
      llave: false
"""


def prueba_6_duplicados() -> None:
    # 6a: duplicado exacto -> ContractSchemaError que nombra el duplicado
    ruta_dup = _escribir("duplicado", DUPLICADO)
    ok_a = False
    try:
        load_contract(ruta_dup)
        _falla("P6a duplicado exacto", "no lanzó (debía fallar por duplicado)")
    except ContractSchemaError as exc:
        if "test_id" in str(exc):
            ok_a = True
        else:
            _falla("P6a duplicado exacto", f"mensaje no nombra el duplicado: {exc}")
    except Exception as exc:  # noqa: BLE001
        _falla("P6a duplicado exacto", f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}")

    # 6b: difieren solo en mayúsculas -> NO es duplicado, debe aceptarse
    ruta_no = _escribir("no_duplicado", NO_DUPLICADO)
    ok_b = False
    try:
        c = load_contract(ruta_no)
        if isinstance(c, Contract) and len(c.columnas) == 2:
            ok_b = True
        else:
            _falla("P6b caso/espacio no es duplicado", f"resultado inesperado: {c}")
    except Exception as exc:  # noqa: BLE001
        _falla("P6b caso/espacio no es duplicado", f"no debía fallar, lanzó {type(exc).__name__}: {exc}")

    if ok_a and ok_b:
        _ok_print("P6 duplicados por cadena exacta (CA-09/10)",
                  "'test_id'/'test_id' rechazado; 'test_id'/'Test_ID' aceptado")


# --- P7 · CA-07/CA-08 · YAML sintácticamente roto ----------------------------
YAML_ROTO = """contract_data:
  columnas:
    - nombre: test_id
       tipo: integer
      nulable: false
"""


def prueba_7_yaml_roto() -> None:
    ruta = _escribir("yaml_roto", YAML_ROTO)
    try:
        load_contract(ruta)
    except ContractParseError as exc:
        msg = str(exc)
        if "YAML" in msg and "inválido" in msg:
            _ok_print("P7 YAML roto (CA-07/08)", f"ContractParseError: {msg.splitlines()[0]}")
        else:
            _falla("P7 YAML roto", f"mensaje no accionable: {msg}")
        return
    except ContractSchemaError as exc:
        _falla("P7 YAML roto", f"esperaba ContractParseError, obtuvo ContractSchemaError: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P7 YAML roto", f"esperaba ContractParseError, obtuvo {type(exc).__name__}")
        return
    _falla("P7 YAML roto", "no lanzó ninguna excepción (debía fallar)")


def main() -> int:
    print("=" * 70)
    print("Pruebas humanas asistidas — feature config_contract")
    print(f"YAML sintéticos temporales en: {_TMP}")
    print("=" * 70)
    prueba_1_valido()
    prueba_2_seis_tipos()
    prueba_3_falta_tipo()
    prueba_4_enum_invalido()
    prueba_5_lista_vacia()
    prueba_6_duplicados()
    prueba_7_yaml_roto()
    print("=" * 70)
    total = _ok + len(_fallas)
    print(f"RESULTADO: {_ok}/{total} pruebas OK")
    if _fallas:
        print("FALLARON: " + ", ".join(_fallas))
        return 1
    print("Todas las pruebas humanas pasaron. Feature lista para aprobar el PR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
