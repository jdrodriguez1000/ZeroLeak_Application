"""Core del alta de clientes (tenants) — `zeroleak.core.scaffold`.

Implementa `create_client`, que materializa en disco la estructura canónica
de un tenant bajo `clients_root/<name>/`. Ver `610_features/client_scaffold/spec.md`
(CA-01 a CA-10) para el contrato completo.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from pathlib import Path

#: Patrón congelado (spec CA-05): allow-list explícita de caracteres
#: permitidos en el nombre del cliente, longitud 1..64. Sin `\w` Unicode
#: amplio: todo carácter fuera de esta lista es rechazado por construcción.
NAME_PATTERN = r"^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$"


class ClientNameError(Exception):
    """Nombre de cliente inválido (no cumple `NAME_PATTERN`)."""


class TenantExistsError(Exception):
    """El tenant `clients_root/name` ya existe."""


#: Placeholder mínimo genérico (spec CA-07): claves presentes con valores
#: vacíos + comentario guía. Sin datos reales ni sensibles.
_CLIENT_YAML = """\
# client.yaml — identidad del tenant (completar).
client_id:
display_name:
sector_id:
created_at:
"""

_CONTRACT_DATA_YAML = """\
# contract_data.yaml — Contrato de Datos (completar).
contract_data:
"""

_BUSINESS_RULES_YAML = """\
# business_rules.yaml — Reglas de Negocio (completar).
business_rules:
"""

_FINANCE_YAML = """\
# finance.yaml — Variables Financieras (completar).
finance:
"""

_MANIFEST_JSON = {"version": 1, "files": []}

#: Subdirectorios vacíos del árbol canónico (medallion), relativos a la raíz
#: del tenant en staging.
_EMPTY_DIRS = ("input", "data/bronze", "data/silver", "data/gold")

#: Archivos de texto del árbol canónico: ruta relativa (dentro del tenant en
#: staging) -> contenido a escribir. `manifest.json` se serializa aparte por
#: ser JSON, no un placeholder YAML.
_TEXT_FILES = {
    "client.yaml": _CLIENT_YAML,
    "input/contract_data.yaml": _CONTRACT_DATA_YAML,
    "input/business_rules.yaml": _BUSINESS_RULES_YAML,
    "input/finance.yaml": _FINANCE_YAML,
    "data/manifest.json": json.dumps(_MANIFEST_JSON),
}


def create_client(name: str, clients_root: Path) -> Path:
    """Da de alta el tenant `name` bajo `clients_root`.

    Valida `name` contra `NAME_PATTERN` **antes** de tocar el disco; si no
    cumple, lanza `ClientNameError` sin crear ningún artefacto. Si
    `clients_root/name` ya existe, lanza `TenantExistsError` sin modificar el
    tenant existente ni crear staging alguno (no idempotente, CA-06).

    La construcción es atómica (staging + rename): el árbol completo se
    materializa en `clients_root/.staging-<uuid>/` y se promueve con
    `os.replace`; ante cualquier fallo, el staging se elimina y no queda
    ningún residuo en `clients_root`.
    """
    if re.fullmatch(NAME_PATTERN, name) is None:
        raise ClientNameError(f"Nombre de cliente inválido: {name!r}")

    tenant_dir = clients_root / name

    if tenant_dir.exists():
        raise TenantExistsError(f"El tenant ya existe: {name!r}")

    staging_dir = clients_root / f".staging-{uuid.uuid4().hex}"

    try:
        _build_tenant_tree(staging_dir)
        os.replace(staging_dir, tenant_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return tenant_dir


def _build_tenant_tree(root: Path) -> None:
    """Materializa el árbol canónico del tenant bajo `root` (directorio de
    staging aún no promovido): directorios de la estructura medallion y los
    archivos de texto (placeholders YAML + manifest) definidos en
    `_TEXT_FILES`.
    """
    for rel_dir in _EMPTY_DIRS:
        (root / rel_dir).mkdir(parents=True)

    for rel_path, content in _TEXT_FILES.items():
        file_path = root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
