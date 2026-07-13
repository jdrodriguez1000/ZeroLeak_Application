"""Core de la ingesta notarial — `zeroleak.ingest.core`.

Implementa `ingest_paths`, que registra en la capa bronze del tenant los
archivos entregados por el cliente. Ver `610_features/ingest/spec.md`
(CA-01 a CA-12) para el contrato completo.

TSK-03 (Caso 1, CA-08): precondición global de tenant (verificación de
`data/bronze/` + `data/manifest.json`) y la excepción `TenantNotFoundError`.

TSK-05 (Caso 2, CA-01): camino feliz de `ingest_paths` — cada `path` de
`paths` es tratado como un archivo válido: se calcula su `sha256`, se copia
byte a byte a `data/bronze/<file>` y se agrega una entrada `pending` al
`manifest.json` (una sola escritura al final).

TSK-09 (Caso 4, CA-09): validación de archivo vacío — antes de copiar, se
descarta cualquier `path` de 0 bytes, reportándolo en `result.failed` con el
motivo `REASON_EMPTY_FILE`. El resto de la validación (existencia de ruta,
extensión fuera de allow-list), colisión de nombre, carpetas y
procesamiento parcial se implementa en casos posteriores del bucle TDD.

TSK-11 (Caso 5, CA-05): dedupe por `sha256` (idempotencia). Antes de copiar
un `path` válido, se compara su `sha256` (calculado por `_hash_file`)
contra los ya presentes en el manifest en memoria (que incluye tanto el
ledger previo cargado al inicio como las entradas ya agregadas en la
corrida actual). Si coincide, el `path` se reporta en `result.duplicates`
(status `"duplicate"`) y no se copia a bronze ni se agrega entrada nueva
al manifest.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


REASON_EMPTY_FILE = "archivo vacío"
"""Motivo de fallo (CA-09) para un `path` que pesa 0 bytes.

Constante de texto estable para que los tests puedan referenciarla sin
acoplarse a una redacción frágil (ver `spec.md`, "Motivos de fallo")."""


class TenantNotFoundError(Exception):
    """El tenant `clients_root/client` no tiene la estructura mínima
    requerida (`data/bronze/` y `data/manifest.json`)."""


@dataclass
class IngestResult:
    """Resultado observable de una invocación a `ingest_paths` (CA-01).

    `exit_code` es una propiedad derivada: `0` si `failed` está vacío, `1`
    si hay ≥ 1 ruta fallida. Los duplicados no afectan el código.
    """

    ingested: list[dict] = field(default_factory=list)
    """Entradas `{"file", "sha256", "ingested_at", "status": "pending"}`."""

    duplicates: list[dict] = field(default_factory=list)
    """Rutas no-op por dedupe (CA-05): `{"path", "sha256", "status": "duplicate"}`."""

    failed: list[dict] = field(default_factory=list)
    """Rutas rechazadas en validación (CA-09): `{"path", "reason"}`."""

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0


def ingest_paths(
    client: str,
    paths: list[str],
    clients_root: str | Path,
) -> IngestResult:
    """Ingiere `paths` en la capa bronze del tenant `client`.

    Precondición global (CA-08): antes de tocar cualquier ruta, se verifica
    que el tenant `clients_root/client` exista con su estructura mínima
    (`data/bronze/` y `data/manifest.json`). Si falta, se lanza
    `TenantNotFoundError` sin crear ni modificar ningún artefacto en disco.

    Camino feliz (CA-01): cada `path` se copia byte a byte a
    `data/bronze/<nombre>`, se calcula su `sha256` y se agrega una entrada
    `{"file", "sha256", "ingested_at", "status": "pending"}` al manifest,
    que se persiste en una sola escritura al final.

    Validación básica por archivo (CA-09): si `path` pesa 0 bytes, se
    reporta en `result.failed` con motivo `REASON_EMPTY_FILE` y no se copia
    a bronze ni se agrega entrada al manifest (deriva `exit_code == 1`).

    Dedupe por contenido (CA-05): si el `sha256` de `path` ya está en el
    manifest (ledger previo o entradas ya acumuladas en esta misma
    invocación), se reporta en `result.duplicates` (no-op, no cuenta como
    fallo) sin copiar a bronze ni agregar entrada nueva.
    """
    tenant_dir = Path(clients_root) / client
    bronze_dir, manifest_path = _resolve_tenant_paths(tenant_dir)

    if not bronze_dir.is_dir() or not manifest_path.is_file():
        raise TenantNotFoundError(f"Tenant inexistente o incompleto: {client!r}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    known_sha256 = {entry["sha256"] for entry in manifest["files"]}

    result = IngestResult()

    for path_str in paths:
        source = Path(path_str)

        reason = _validate_file(source)
        if reason is not None:
            result.failed.append({"path": path_str, "reason": reason})
            continue

        sha256 = _hash_file(source)

        if sha256 in known_sha256:
            result.duplicates.append(
                {"path": path_str, "sha256": sha256, "status": "duplicate"}
            )
            continue

        destination = bronze_dir / source.name
        shutil.copyfile(source, destination)

        entry = _build_manifest_entry(name=source.name, sha256=sha256)
        manifest["files"].append(entry)
        known_sha256.add(sha256)
        result.ingested.append(entry)

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return result


def _resolve_tenant_paths(tenant_dir: Path) -> tuple[Path, Path]:
    """Resuelve `data/bronze/` y `data/manifest.json` bajo `tenant_dir`.

    No verifica su existencia; esa es responsabilidad de quien llama (la
    precondición global de tenant en `ingest_paths`, CA-08).
    """
    return tenant_dir / "data" / "bronze", tenant_dir / "data" / "manifest.json"


def _validate_file(source: Path) -> str | None:
    """Valida un `path` candidato a ingesta (CA-09).

    Retorna el motivo de fallo (para `result.failed`) si la validación no
    pasa, o `None` si el archivo es válido para continuar el camino feliz.
    Cubre, por ahora, solo la validación de tamaño > 0 (archivo vacío); el
    resto de las validaciones de la allow-list (existencia de ruta,
    extensión) se suman aquí en casos posteriores del bucle TDD.
    """
    if source.stat().st_size == 0:
        return REASON_EMPTY_FILE
    return None


def _hash_file(source: Path) -> str:
    """Calcula el `sha256` de `source` sobre sus bytes tal cual (CA-05/CA-10).

    Se usa tanto para el chequeo de dedupe como para la entrada de manifest
    del archivo ingerido; nunca abre ni parsea el contenido como dato.
    """
    return hashlib.sha256(source.read_bytes()).hexdigest()


def _build_manifest_entry(name: str, sha256: str) -> dict:
    """Construye la entrada `pending` del manifest para un archivo ingerido.

    Emite exactamente `{"file", "sha256", "ingested_at", "status"}`
    (`ingested_at` con precisión de segundos, CA-02).
    """
    return {
        "file": name,
        "sha256": sha256,
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pending",
    }
