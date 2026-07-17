"""Pruebas humanas asistidas de la feature `contract_multifile` (paso 13).

Script autocontenido: crea YAML de contrato *sintéticos* en un directorio
temporal (nunca bajo `clients/*/data/`, C-01), ejercita `load_contract` con el
esquema **multi-archivo** (`contract_data.archivos[].{nombre, columnas}`) y
verifica el comportamiento observable de los criterios de aceptación (CA) y de
los mensajes congelados M-01…M-13. La última prueba carga la plantilla **real y
versionada** del repo (`600_template/contract_data.yaml`, CA-22), que es
sintética por definición. No modifica el repositorio ni toca datos reales.

Uso (desde la raíz del repositorio):

    py -3.13 610_features/contract_multifile/pruebas_humanas.py

Salida esperada: una línea `[OK]` por prueba y, al final,
`RESULTADO: 15/15 pruebas OK`. Si alguna falla, se marca `[FALLA]` con el
detalle (esperado vs obtenido) y el script termina con código de salida != 0.
"""
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

_TMP = Path(tempfile.mkdtemp(prefix="zlk_pruebas_multifile_"))
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


def _espera_schema_error(titulo: str, texto_yaml: str, mensaje_exacto: str) -> None:
    """Carga un YAML que debe fallar con ContractSchemaError de mensaje EXACTO."""
    ruta = _escribir(titulo.split()[0].lower(), texto_yaml)
    try:
        load_contract(ruta)
    except ContractSchemaError as exc:
        if str(exc) == mensaje_exacto:
            _ok_print(titulo, f"ContractSchemaError (mensaje exacto): {exc}")
        else:
            _falla(titulo, f"mensaje inesperado.\n   esperado: {mensaje_exacto!r}\n   obtenido: {str(exc)!r}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla(titulo, f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}: {exc}")
        return
    _falla(titulo, "no lanzó ninguna excepción (debía fallar)")


# --- P1 · CA-01/CA-02 · contrato válido de 2 archivos (camino feliz) ----------
VALIDO_DOS = """contract_data:
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
        - {nombre: correo,     tipo: string,  nulable: true,  llave: false}
        - {nombre: fecha_alta, tipo: date,    nulable: false, llave: false}
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id,   tipo: integer,  nulable: false, llave: true}
        - {nombre: cliente_id, tipo: integer,  nulable: false, llave: false}
        - {nombre: monto,      tipo: float,    nulable: false, llave: false}
        - {nombre: vendida_en, tipo: datetime, nulable: false, llave: false}
"""


def prueba_1_valido_dos_archivos() -> None:
    ruta = _escribir("valido_dos", VALIDO_DOS)
    try:
        c = load_contract(ruta)
    except Exception as exc:  # noqa: BLE001
        _falla("P1 válido 2 archivos", f"no debía lanzar, lanzó {type(exc).__name__}: {exc}")
        return
    if not isinstance(c, Contract):
        _falla("P1 válido 2 archivos", f"esperaba Contract, obtuvo {type(c).__name__}")
        return
    nombres = [a.nombre for a in c.archivos]
    if nombres != ["clientes.csv", "ventas.csv"]:
        _falla("P1 válido 2 archivos", f"orden/nombres inesperados: {nombres}")
        return
    conteos = [len(a.columnas) for a in c.archivos]
    if conteos != [3, 4]:
        _falla("P1 válido 2 archivos", f"conteo de columnas inesperado: {conteos}")
        return
    col = c.archivos[1].columnas[0]
    if not (col.nombre == "venta_id" and col.tipo.value == "integer"
            and col.nulable is False and col.llave is True):
        _falla("P1 válido 2 archivos", f"fidelidad de campos incorrecta en ventas.csv[0]: {col}")
        return
    _ok_print("P1 válido 2 archivos (CA-01/02)",
              "Contract con archivos [clientes.csv(3), ventas.csv(4)] en orden y fieles")


# --- P2 · CA-05 · los 6 tipos del enum dentro de un archivo -------------------
SEIS_TIPOS = """contract_data:
  archivos:
    - nombre: catalogo.csv
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
    tipos = [col.tipo.value for col in c.archivos[0].columnas]
    esperados = ["string", "integer", "float", "date", "datetime", "boolean"]
    if tipos != esperados:
        _falla("P2 seis tipos", f"esperaba {esperados}, obtuvo {tipos}")
        return
    _ok_print("P2 seis tipos del enum (CA-05)",
              "string/integer/float/date/datetime/boolean aceptados en un archivo")


# --- P3 · CA-03 · columna homónima entre archivos distintos SE ACEPTA ---------
def prueba_3_columna_homonima() -> None:
    # cliente_id vive en clientes.csv (llave) y en ventas.csv (no-llave): legal.
    ruta = _escribir("homonima", VALIDO_DOS)
    try:
        c = load_contract(ruta)
    except Exception as exc:  # noqa: BLE001
        _falla("P3 columna homónima", f"no debía lanzar, lanzó {type(exc).__name__}: {exc}")
        return
    en_clientes = [x for x in c.archivos[0].columnas if x.nombre == "cliente_id"]
    en_ventas = [x for x in c.archivos[1].columnas if x.nombre == "cliente_id"]
    if len(en_clientes) == 1 and len(en_ventas) == 1 and en_clientes[0].llave != en_ventas[0].llave:
        _ok_print("P3 columna homónima entre archivos (CA-03)",
                  "'cliente_id' aceptada en clientes.csv y ventas.csv (duplicado por archivo, no global)")
    else:
        _falla("P3 columna homónima", f"resultado inesperado: clientes={en_clientes}, ventas={en_ventas}")


# --- P4 · CA-19 · contract_data nulo -> M-01, NUNCA AttributeError (T-56) -----
RAIZ_NULA = "contract_data:\n"


def prueba_4_raiz_nula_m01() -> None:
    ruta = _escribir("raiz_nula", RAIZ_NULA)
    try:
        load_contract(ruta)
    except AttributeError as exc:
        _falla("P4 raíz nula (T-56)", f"REGRESIÓN: propagó AttributeError: {exc}")
        return
    except ContractSchemaError as exc:
        esperado = ("la clave raíz 'contract_data' debe contener un mapa con la lista "
                    "'archivos' (se encontró: None)")
        if str(exc) == esperado:
            _ok_print("P4 raíz nula -> M-01 (CA-19, T-56)", f"ContractSchemaError: {exc}")
        else:
            _falla("P4 raíz nula", f"mensaje inesperado.\n   esperado: {esperado!r}\n   obtenido: {str(exc)!r}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P4 raíz nula", f"esperaba ContractSchemaError, obtuvo {type(exc).__name__}: {exc}")
        return
    _falla("P4 raíz nula", "no lanzó ninguna excepción (debía fallar)")


# --- P5 · CA-08 · esquema viejo (columnas en la raíz, sin archivos) -> M-02 ----
ESQUEMA_VIEJO = """contract_data:
  columnas:
    - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
    - {nombre: correo,     tipo: string,  nulable: true,  llave: false}
"""

M02 = ("el contrato usa el esquema anterior de un solo archivo: se encontró 'columnas' "
       "en la raíz de 'contract_data'; ahora las columnas van dentro de 'archivos[]' "
       "(contract_data.archivos[].columnas)")


# --- P6 · CA-28 · contrato híbrido (archivos válida + columnas residual) -> M-13
HIBRIDO = """contract_data:
  columnas:
    - {nombre: residual, tipo: string, nulable: false, llave: false}
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
"""

M13 = ("el contrato declara 'archivos[]' y además un 'columnas' residual en la raíz de "
       "'contract_data': ese bloque no se valida ni se audita; elimínelo y deje cada "
       "columna dentro del archivo al que pertenece (contract_data.archivos[].columnas)")


# --- P7 · CA-06 · archivos: [] -> M-04 ---------------------------------------
ARCHIVOS_VACIA = "contract_data:\n  archivos: []\n"
M04 = "la lista de archivos no puede estar vacía"


# --- P8 · CA-09 · archivos no-lista -> M-03 ----------------------------------
ARCHIVOS_NO_LISTA = "contract_data:\n  archivos: ventas.csv\n"
M03 = "'archivos' debe ser una lista (se encontró: 'ventas.csv')"


# --- P9 · CA-10 · archivo sin nombre -> M-06 (degrada a archivo[1]) -----------
SIN_NOMBRE = """contract_data:
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
    - columnas:
        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
"""
M06 = "archivo[1]: falta el campo requerido 'nombre' (Field required)"


# --- P10 · CA-13 · nombre de archivo duplicado -> M-05 -----------------------
ARCHIVO_DUPLICADO = """contract_data:
  archivos:
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
    - nombre: ventas.csv
      columnas:
        - {nombre: monto, tipo: float, nulable: false, llave: false}
"""
M05 = "nombre de archivo duplicado: 'ventas.csv'"


# --- P11 · CA-15 · columna sin tipo -> M-09 (localiza archivo + columna) ------
COLUMNA_SIN_TIPO = """contract_data:
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
        - {nombre: monto, nulable: false, llave: false}
"""
M09 = "archivo[1] 'ventas.csv', columna de índice 1: falta el campo requerido 'tipo' (Field required)"


# --- P12 · CA-16 · tipo fuera del enum -> M-10 -------------------------------
TIPO_INVALIDO = """contract_data:
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
        - {nombre: monto, tipo: numero_magico, nulable: false, llave: false}
"""
M10 = ("archivo[1] 'ventas.csv', columna de índice 1, campo 'tipo': valor 'numero_magico' "
       "inválido (Input should be 'string', 'integer', 'float', 'date', 'datetime' or 'boolean')")


# --- P13 · CA-17 · columna duplicada dentro de un archivo -> M-11 ------------
COLUMNA_DUPLICADA = """contract_data:
  archivos:
    - nombre: clientes.csv
      columnas:
        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}
    - nombre: ventas.csv
      columnas:
        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}
        - {nombre: venta_id, tipo: string,  nulable: true,  llave: false}
"""
M11 = "archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'"


# --- P14 · CA-18 · YAML sintácticamente roto -> ContractParseError (M-12) -----
YAML_ROTO = """contract_data:
  archivos:
    - nombre: ventas.csv
       columnas:
      - {nombre: x, tipo: integer, nulable: false, llave: false}
"""


def prueba_14_yaml_roto() -> None:
    ruta = _escribir("yaml_roto", YAML_ROTO)
    try:
        load_contract(ruta)
    except ContractParseError as exc:
        if str(exc).startswith("el archivo YAML del contrato es sintácticamente inválido"):
            _ok_print("P14 YAML roto -> M-12 (CA-18)", f"ContractParseError: {str(exc).splitlines()[0]}")
        else:
            _falla("P14 YAML roto", f"mensaje no accionable: {exc}")
        return
    except ContractSchemaError as exc:
        _falla("P14 YAML roto", f"esperaba ContractParseError, obtuvo ContractSchemaError: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        _falla("P14 YAML roto", f"esperaba ContractParseError, obtuvo {type(exc).__name__}: {exc}")
        return
    _falla("P14 YAML roto", "no lanzó ninguna excepción (debía fallar)")


# --- P15 · CA-22 · la plantilla REAL del repo carga sin error -----------------
def prueba_15_plantilla_real() -> None:
    raiz_repo = Path(__file__).resolve().parents[2]
    plantilla = raiz_repo / "600_template" / "contract_data.yaml"
    if not plantilla.exists():
        _falla("P15 plantilla real", f"no existe la plantilla esperada: {plantilla}")
        return
    try:
        c = load_contract(plantilla)
    except Exception as exc:  # noqa: BLE001
        _falla("P15 plantilla real", f"no debía lanzar, lanzó {type(exc).__name__}: {exc}")
        return
    if not isinstance(c, Contract) or len(c.archivos) < 1:
        _falla("P15 plantilla real", f"esperaba Contract con >=1 archivo, obtuvo {c}")
        return
    if not all(a.nombre and len(a.columnas) >= 1 for a in c.archivos):
        _falla("P15 plantilla real", "algún archivo de la plantilla no tiene nombre o columnas")
        return
    nombres = [a.nombre for a in c.archivos]
    _ok_print("P15 plantilla real 600_template (CA-22)",
              f"carga sin error, archivos={nombres}")


def main() -> int:
    print("=" * 78)
    print("Pruebas humanas asistidas — feature contract_multifile (esquema multi-archivo)")
    print(f"YAML sintéticos temporales en: {_TMP}")
    print("=" * 78)
    prueba_1_valido_dos_archivos()
    prueba_2_seis_tipos()
    prueba_3_columna_homonima()
    prueba_4_raiz_nula_m01()
    _espera_schema_error("P5 esquema viejo -> M-02 (CA-08)", ESQUEMA_VIEJO, M02)
    _espera_schema_error("P6 híbrido -> M-13 (CA-28)", HIBRIDO, M13)
    _espera_schema_error("P7 archivos vacía -> M-04 (CA-06)", ARCHIVOS_VACIA, M04)
    _espera_schema_error("P8 archivos no-lista -> M-03 (CA-09)", ARCHIVOS_NO_LISTA, M03)
    _espera_schema_error("P9 archivo sin nombre -> M-06 (CA-10)", SIN_NOMBRE, M06)
    _espera_schema_error("P10 archivo duplicado -> M-05 (CA-13)", ARCHIVO_DUPLICADO, M05)
    _espera_schema_error("P11 columna sin tipo -> M-09 (CA-15)", COLUMNA_SIN_TIPO, M09)
    _espera_schema_error("P12 tipo inválido -> M-10 (CA-16)", TIPO_INVALIDO, M10)
    _espera_schema_error("P13 columna duplicada -> M-11 (CA-17)", COLUMNA_DUPLICADA, M11)
    prueba_14_yaml_roto()
    prueba_15_plantilla_real()
    print("=" * 78)
    total = _ok + len(_fallas)
    print(f"RESULTADO: {_ok}/{total} pruebas OK")
    if _fallas:
        print("FALLARON: " + ", ".join(_fallas))
        return 1
    print("Todas las pruebas humanas pasaron. Feature lista para aprobar el PR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
