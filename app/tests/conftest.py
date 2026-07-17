"""Fixtures sintéticas compartidas para los tests de ZeroLeak.

Regla "Datos en Bóveda" (C-01): todos los datos usados en los tests son
sintéticos. `clients_root` vive siempre en `tmp_path` (aislado por pytest),
nunca sobre datos reales de un cliente.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict

import pytest


@pytest.fixture
def clients_root(tmp_path: Path) -> Path:
    """Directorio raíz de tenants, limpio, aislado en `tmp_path`.

    TSK-01: fixture mínima que necesitan los tests de `create_client`.
    """
    root = tmp_path / "clients_root"
    root.mkdir()
    return root


@pytest.fixture
def tenant_snapshot() -> Callable[[Path], Dict[str, int]]:
    """Helper de snapshot del árbol de un tenant (rutas relativas + tamaños).

    TSK-01: usado por casos posteriores (p. ej. Caso 8, no idempotencia) para
    comparar el estado de un tenant antes/después de una operación. Devuelve
    un `dict` `{ruta_relativa_posix: tamaño_en_bytes}`; los directorios se
    representan con tamaño `-1` (no tienen tamaño de archivo propio) para
    poder detectar tanto adiciones/eliminaciones de directorios como cambios
    de contenido en archivos.
    """

    def _snapshot(tenant_dir: Path) -> Dict[str, int]:
        snapshot: Dict[str, int] = {}
        for path in tenant_dir.rglob("*"):
            rel = path.relative_to(tenant_dir).as_posix()
            snapshot[rel] = -1 if path.is_dir() else path.stat().st_size
        return snapshot

    return _snapshot


@pytest.fixture
def ingestible_tenant(
    clients_root: Path,
) -> Callable[[str], Path]:
    """Factory de tenant "ingerible" (TSK-01, feature `ingest`).

    Crea, bajo `clients_root` (sintético, en `tmp_path`), la estructura mínima
    que `ingest_paths` exige como precondición global de tenant: `data/bronze/`
    y `data/manifest.json` inicial `{"version": 1, "files": []}` (formato
    producido por `client_scaffold`). Devuelve la ruta del tenant creado.

    Usado por los casos del bucle TDD de `ingest` que necesitan un tenant
    existente y "vacío" de archivos ingeridos (p. ej. Caso 2 en adelante); el
    Caso 1 (CA-08, tenant inexistente) deliberadamente NO usa esta fixture.
    """

    def _make(name: str) -> Path:
        tenant_dir = clients_root / name
        (tenant_dir / "data" / "bronze").mkdir(parents=True)
        manifest_path = tenant_dir / "data" / "manifest.json"
        manifest_path.write_text(
            json.dumps({"version": 1, "files": []}, indent=2),
            encoding="utf-8",
        )
        return tenant_dir

    return _make


@pytest.fixture
def write_contract_yaml(tmp_path: Path) -> Callable[..., Path]:
    """Factory de `contract_data.yaml` sintético (TSK-01, feature `contract_multifile`).

    Materializa un YAML de contrato en `tmp_path` (nunca bajo `clients/*/data/`,
    C-01). Migrado a la forma **multi-archivo** (D-18/CA-01): el parámetro
    `columnas=` del esquema viejo (`contract_data.columnas`, hoy inválido) se
    **retira**; la única forma generada es `archivos=`. Dos formas de uso:

    - `write_contract_yaml(texto="...")`: escribe el texto YAML crudo tal cual
      (útil para fixtures de esquema inválido, híbrido o YAML sintácticamente
      roto, que necesitan controlar la raíz byte a byte).
    - `write_contract_yaml(archivos=[{"nombre": ..., "columnas": [...]}, ...])`:
      genera el YAML a partir de una lista de archivos, cada uno con su
      `nombre` y su lista de columnas ficticias (`nombre`, `tipo`, `nulable`,
      `llave`), bajo la raíz `contract_data` -> `archivos[].columnas` (D-18),
      preservando el orden declarado de archivos y de columnas dentro de cada
      uno.

    Vocabulario ficticio de referencia (matrices de mentiras, C-01):
    `clientes.csv`/`ventas.csv`/`catalogo.csv`, columnas `cliente_id`,
    `correo`, `venta_id`, `vendida_en`, `monto`, `fecha_alta`, `activo`,
    `creado_en`, `sku`, `precio`. Sin PII real.
    """

    def _write(
        texto: str | None = None,
        archivos: list[dict] | None = None,
        filename: str = "contract_data.yaml",
    ) -> Path:
        if texto is None:
            archivos = archivos or []
            lineas = ["contract_data:", "  archivos:"]
            for archivo in archivos:
                lineas.append(f"    - nombre: {archivo['nombre']}")
                lineas.append("      columnas:")
                for col in archivo.get("columnas", []):
                    lineas.append(f"        - nombre: {col['nombre']}")
                    lineas.append(f"          tipo: {col['tipo']}")
                    lineas.append(f"          nulable: {str(col['nulable']).lower()}")
                    lineas.append(f"          llave: {str(col['llave']).lower()}")
            texto = "\n".join(lineas) + "\n"
        path = tmp_path / filename
        path.write_text(texto, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def contrato_valido_columnas() -> list[dict]:
    """Lista de columnas ficticias válidas reutilizable (TSK-01).

    Cuatro columnas sintéticas (sin PII) que cubren los campos requeridos por
    `Columna` (`nombre`, `tipo`, `nulable`, `llave`), en un orden fijo y
    verificable por los tests de camino feliz (CA-01/CA-02).
    """
    return [
        {"nombre": "test_id", "tipo": "integer", "nulable": False, "llave": True},
        {"nombre": "correo", "tipo": "string", "nulable": True, "llave": False},
        {"nombre": "monto", "tipo": "float", "nulable": True, "llave": False},
        {"nombre": "fecha_alta", "tipo": "date", "nulable": True, "llave": False},
    ]


@pytest.fixture
def contrato_seis_tipos_columnas() -> list[dict]:
    """Lista de columnas ficticias, una por cada uno de los 6 `TipoDato` (TSK-06).

    Cubre exactamente el enum cerrado de tipos soportados (D-23b): `string`,
    `integer`, `float`, `date`, `datetime`, `boolean`; una columna sintética
    por tipo (sin PII), en un orden fijo y verificable por el test de CA-03.
    """
    return [
        {"nombre": "correo", "tipo": "string", "nulable": True, "llave": False},
        {"nombre": "test_id", "tipo": "integer", "nulable": False, "llave": True},
        {"nombre": "monto", "tipo": "float", "nulable": True, "llave": False},
        {"nombre": "fecha_alta", "tipo": "date", "nulable": True, "llave": False},
        {"nombre": "creado_en", "tipo": "datetime", "nulable": True, "llave": False},
        {"nombre": "activo", "tipo": "boolean", "nulable": False, "llave": False},
    ]


@pytest.fixture
def clientes_columnas() -> list[dict]:
    """Columnas ficticias de `clientes.csv`: 3 columnas (TSK-02).

    Incluye `cliente_id` (llave), que **también** aparece como columna de
    `ventas_columnas` -- homónimo deliberado entre archivos distintos, legal
    por diseño (CA-03, D-25 hallazgo 2).
    """
    return [
        {"nombre": "cliente_id", "tipo": "integer", "nulable": False, "llave": True},
        {"nombre": "correo", "tipo": "string", "nulable": True, "llave": False},
        {"nombre": "fecha_alta", "tipo": "date", "nulable": True, "llave": False},
    ]


@pytest.fixture
def ventas_columnas() -> list[dict]:
    """Columnas ficticias de `ventas.csv`: 4 columnas (TSK-02).

    Incluye `cliente_id` (homónimo con `clientes_columnas`, legal) y
    `vendida_en` de tipo `datetime`.
    """
    return [
        {"nombre": "venta_id", "tipo": "integer", "nulable": False, "llave": True},
        {"nombre": "cliente_id", "tipo": "integer", "nulable": False, "llave": False},
        {"nombre": "vendida_en", "tipo": "datetime", "nulable": False, "llave": False},
        {"nombre": "monto", "tipo": "float", "nulable": True, "llave": False},
    ]


@pytest.fixture
def catalogo_columnas() -> list[dict]:
    """Columnas ficticias de `catalogo.csv`: 2 columnas (TSK-02).

    Usadas por la variante de **tres** archivos (Caso 3b) y por los casos que
    ejercitan N >= 3 sin cota superior (p. ej. Caso 17b, archivo del medio).
    """
    return [
        {"nombre": "sku", "tipo": "string", "nulable": False, "llave": True},
        {"nombre": "precio", "tipo": "float", "nulable": True, "llave": False},
    ]


@pytest.fixture
def archivos_un_archivo(clientes_columnas: list[dict]) -> list[dict]:
    """Variante de **un solo** archivo (TSK-02): caso general, len(archivos)==1 (CA-04)."""
    return [{"nombre": "clientes.csv", "columnas": clientes_columnas}]


@pytest.fixture
def archivos_dos_archivos(
    clientes_columnas: list[dict], ventas_columnas: list[dict]
) -> list[dict]:
    """Variante de **dos** archivos, en el orden declarado (TSK-02, CA-01)."""
    return [
        {"nombre": "clientes.csv", "columnas": clientes_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
    ]


@pytest.fixture
def archivos_tres_archivos(
    clientes_columnas: list[dict],
    ventas_columnas: list[dict],
    catalogo_columnas: list[dict],
) -> list[dict]:
    """Variante de **tres** archivos, en el orden declarado (TSK-02, Caso 3b: CA-01/CA-04)."""
    return [
        {"nombre": "clientes.csv", "columnas": clientes_columnas},
        {"nombre": "ventas.csv", "columnas": ventas_columnas},
        {"nombre": "catalogo.csv", "columnas": catalogo_columnas},
    ]


@pytest.fixture
def archivos_seis_tipos(contrato_seis_tipos_columnas: list[dict]) -> list[dict]:
    """Variante de un archivo con los 6 `TipoDato` (TSK-02, CA-05)."""
    return [{"nombre": "clientes.csv", "columnas": contrato_seis_tipos_columnas}]


def _generar_texto_contract_yaml(archivos: list[dict]) -> str:
    """Genera el texto YAML de un `contract_data.yaml` multi-archivo.

    Mismo generador que usa `write_contract_yaml` (TSK-01 de
    `contract_check`, feature `contract_check`): se replica aquí en vez de
    reutilizar directamente esa fixture porque `tenant_con_contrato` escribe
    bajo `<clients_root>/<nombre>/input/`, no en la raíz de `tmp_path`.
    """
    lineas = ["contract_data:", "  archivos:"]
    for archivo in archivos:
        lineas.append(f"    - nombre: {archivo['nombre']}")
        lineas.append("      columnas:")
        for col in archivo.get("columnas", []):
            lineas.append(f"        - nombre: {col['nombre']}")
            lineas.append(f"          tipo: {col['tipo']}")
            lineas.append(f"          nulable: {str(col['nulable']).lower()}")
            lineas.append(f"          llave: {str(col['llave']).lower()}")
    return "\n".join(lineas) + "\n"


@pytest.fixture
def tenant_con_contrato(
    clients_root: Path,
) -> Callable[..., Path]:
    """Factory de tenant con `input/contract_data.yaml` (TSK-01, `contract_check`).

    Crea `<clients_root>/<nombre>/input/` y escribe ahí el
    `contract_data.yaml`, ya sea con `texto=` crudo (para YAML roto, esquema
    inválido o el scaffold sin cuerpo), o generado desde
    `archivos=[{nombre, columnas}]` con el mismo generador que
    `write_contract_yaml` (D-18: raíz `contract_data` -> `archivos[].columnas`).
    Devuelve la ruta del tenant (no la del YAML). Todo bajo `tmp_path`
    (vía `clients_root`), vocabulario sintético (`clientes.csv`, `ventas.csv`;
    `cliente_id`, `correo`, `alta`, `venta_id`, `monto`), sin PII (C-01).
    """

    def _make(
        nombre: str,
        *,
        texto: str | None = None,
        archivos: list[dict] | None = None,
    ) -> Path:
        tenant_dir = clients_root / nombre
        input_dir = tenant_dir / "input"
        input_dir.mkdir(parents=True)
        if texto is None:
            texto = _generar_texto_contract_yaml(archivos or [])
        (input_dir / "contract_data.yaml").write_text(texto, encoding="utf-8")
        return tenant_dir

    return _make


@pytest.fixture
def escenario_contract_check(
    clients_root: Path,
    tenant_con_contrato: Callable[..., Path],
    archivos_dos_archivos: list[dict],
) -> Dict[str, Path]:
    """Escenario con los cinco tenants que `contract_check` necesita a la vez
    (TSK-02): válido (2 archivos), scaffoldeado (`contract_data:` sin cuerpo,
    texto exacto de `scaffold.py:_CONTRACT_DATA_YAML`), de esquema inválido,
    de YAML roto y sin contrato; más, en el tenant válido, un
    `data/bronze/clientes.csv` sintético y un `data/manifest.json`.

    Devuelve un `dict` con `clients_root` y la ruta de cada tenant, sujeto de
    las auditorías de solo-lectura (CA-16) y de frontera (CA-17).
    """
    valido = tenant_con_contrato("VALIDO", archivos=archivos_dos_archivos)
    scaffoldeado = tenant_con_contrato(
        "SCAFFOLDEADO",
        texto="# contract_data.yaml — Contrato de Datos (completar).\ncontract_data:\n",
    )
    esquema_invalido = tenant_con_contrato(
        "ESQUEMA_INVALIDO",
        texto="contract_data:\n  archivos: \"no soy lista\"\n",
    )
    yaml_roto = tenant_con_contrato(
        "YAML_ROTO",
        texto="contract_data:\n  archivos: [\n",
    )
    sin_contrato_dir = clients_root / "SIN_CONTRATO"
    sin_contrato_dir.mkdir(parents=True)

    bronze_dir = valido / "data" / "bronze"
    bronze_dir.mkdir(parents=True)
    (bronze_dir / "clientes.csv").write_text(
        "cliente_id,correo,alta\n1,a@b.test,2024-01-01\n", encoding="utf-8"
    )
    manifest_path = valido / "data" / "manifest.json"
    manifest_path.write_text(
        json.dumps({"version": 1, "files": []}, indent=2), encoding="utf-8"
    )

    return {
        "clients_root": clients_root,
        "valido": valido,
        "scaffoldeado": scaffoldeado,
        "esquema_invalido": esquema_invalido,
        "yaml_roto": yaml_roto,
        "sin_contrato": sin_contrato_dir,
    }


@pytest.fixture
def read_manifest() -> Callable[[Path], dict]:
    """Helper de lectura del `manifest.json` de un tenant (TSK-01).

    Recibe la ruta del tenant y devuelve el contenido parseado de
    `data/manifest.json` como `dict`.
    """

    def _read(tenant_dir: Path) -> dict:
        manifest_path = tenant_dir / "data" / "manifest.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    return _read
