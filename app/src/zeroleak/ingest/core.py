"""Core de la ingesta notarial — `zeroleak.ingest.core`.

Implementa `ingest_paths`, que registra en la capa bronze del tenant los
archivos entregados por el cliente. Ver `610_features/ingest/spec.md`
(CA-01 a CA-12) para el contrato completo; este módulo cubre CA-01 a CA-10
(la fachada CLI, CA-12, y la frontera `.gitignore`, CA-11, no viven aquí).

Pipeline de `ingest_paths` (orden real del bucle, ver también su
docstring): precondición global de tenant (CA-08) → carga del ledger
(`manifest.json`, una sola lectura) → expansión de `paths` en candidatos
planos, incluyendo el recorrido de carpetas (CA-03/CA-04) → por cada
candidato: validación de existencia/extensión/tamaño (CA-07/CA-09) → hash
`sha256` sobre los bytes crudos, sin parsear el contenido (CA-10) → dedupe
por contenido contra el manifest en memoria (CA-05) → resolución de nombre
en bronze, con sufijo `__<sha8>` ante colisión de nombre con contenido
distinto (CA-06) → copia byte a byte → entrada `pending` en el manifest
(CA-02). El procesamiento es parcial: una ruta inválida no aborta el resto
de `paths` (CA-07); el manifest se persiste en una única escritura al
final, y `IngestResult.exit_code` deriva de si hubo algún `failed`.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
"""Allow-list de extensiones (CA-03/CA-07) para candidatos a ingesta.

Comparación case-insensitive contra `Path(p).suffix.lower()`. Se usa tanto
para filtrar (en silencio) el recorrido plano de una carpeta (`_expand_paths`)
como para validar (reportando en `result.failed`) un archivo suelto pasado
directamente a `ingest_paths` (`_validate_file`)."""


# Motivos de fallo (CA-07/CA-09): constantes de texto estable para que los
# tests puedan referenciarlas sin acoplarse a una redacción frágil (ver
# `spec.md`, "Motivos de fallo"). Ordenadas igual que las guardas de
# `_validate_file`: existencia → extensión → tamaño.

REASON_PATH_NOT_FOUND = "la ruta no existe"
"""Motivo de fallo (CA-07) para un `path` que no existe en disco."""

REASON_EXTENSION_NOT_ALLOWED = "extensión fuera de allow-list"
"""Motivo de fallo (CA-07) para un archivo suelto con extensión fuera de
`ALLOWED_EXTENSIONS`. No aplica a los candidatos ya filtrados dentro de una
carpeta (esos nunca llegan aquí con extensión inválida, ver `_expand_paths`)."""

REASON_EMPTY_FILE = "archivo vacío"
"""Motivo de fallo (CA-09) para un `path` que pesa 0 bytes."""


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
    """Rutas rechazadas en validación (CA-07/CA-09): `{"path", "reason"}`."""

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

    Cada elemento de `paths` (archivo suelto o carpeta, en cualquier
    combinación, CA-04) se procesa de forma independiente y parcial
    (CA-07): una ruta inválida no aborta el resto. Una carpeta se expande a
    sus archivos de primer nivel con extensión en `ALLOWED_EXTENSIONS`
    (recorrido plano, sin recursión, CA-03); subcarpetas y extensiones no
    permitidas dentro de ella se ignoran en silencio (no van a
    `result.failed`). Cada candidato resultante pasa por:

    - **Validación** (CA-07/CA-09): ruta inexistente
      (`REASON_PATH_NOT_FOUND`), extensión fuera de `ALLOWED_EXTENSIONS`
      (`REASON_EXTENSION_NOT_ALLOWED`) o archivo de 0 bytes
      (`REASON_EMPTY_FILE`) se reportan en `result.failed` con su motivo y
      no se copian ni se anotan (deriva `exit_code == 1`).
    - **Dedupe por contenido** (CA-05): si el `sha256` del archivo ya está
      en el manifest (ledger previo o entradas acumuladas en esta misma
      invocación), se reporta en `result.duplicates` (no-op, no cuenta
      como fallo) sin copiar ni agregar entrada nueva.
    - **Copia + nombrado** (CA-01/CA-06): el archivo se copia byte a byte a
      `data/bronze/<nombre>`. Si ya existe en bronze un archivo con ese
      nombre pero contenido distinto, se almacena con sufijo
      `<stem>__<sha8><suffix>` en vez de sobrescribir el original.
    - **Manifest** (CA-02): se agrega una entrada
      `{"file", "sha256", "ingested_at", "status": "pending"}` en memoria,
      persistida en una sola escritura al final de la invocación.
    """
    tenant_dir = Path(clients_root) / client
    bronze_dir, manifest_path = _resolve_tenant_paths(tenant_dir)

    if not bronze_dir.is_dir() or not manifest_path.is_file():
        raise TenantNotFoundError(f"Tenant inexistente o incompleto: {client!r}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    known_sha256 = {entry["sha256"] for entry in manifest["files"]}

    result = IngestResult()

    for path_str in _expand_paths(paths):
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

        stored_name, destination = _resolve_destination(source, sha256, bronze_dir)

        shutil.copyfile(source, destination)

        entry = _build_manifest_entry(name=stored_name, sha256=sha256)
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


def _expand_paths(paths: list[str]) -> list[str]:
    """Despacha cada `path` de `paths` a la lista plana de candidatos (CA-03/CA-04).

    Itera `paths` en orden, tratando archivo suelto y carpeta como orígenes
    combinables en la misma invocación (CA-04). Un `path` que no es carpeta
    se agrega tal cual (camino de archivo suelto, sin filtrar por
    allow-list). Un `path` que es carpeta se recorre en plano (`iterdir()`,
    solo primer nivel, sin recursión) y solo se agregan sus entradas que son
    archivo con extensión en `ALLOWED_EXTENSIONS` (case-insensitive);
    subcarpetas y extensiones fuera de la allow-list se ignoran en silencio
    (no llegan a `result.failed`).
    """
    candidates: list[str] = []
    for path_str in paths:
        source = Path(path_str)
        if source.is_dir():
            for entry in sorted(source.iterdir()):
                if entry.is_file() and entry.suffix.lower() in ALLOWED_EXTENSIONS:
                    candidates.append(str(entry))
        else:
            candidates.append(path_str)
    return candidates


def _validate_file(source: Path) -> str | None:
    """Valida un `path` candidato a ingesta (CA-07/CA-09).

    Retorna el motivo de fallo (para `result.failed`) si la validación no
    pasa, o `None` si el archivo es válido para continuar el camino feliz.
    Orden de validación (CA-07): primero existencia de ruta, luego extensión
    fuera de allow-list, luego tamaño > 0 (archivo vacío). Los candidatos
    provenientes del recorrido plano de una carpeta (`_expand_paths`) ya
    fueron filtrados por extensión ahí, así que nunca fallan aquí por esa
    causa.
    """
    if not source.is_file():
        return REASON_PATH_NOT_FOUND
    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        return REASON_EXTENSION_NOT_ALLOWED
    if source.stat().st_size == 0:
        return REASON_EMPTY_FILE
    return None


def _resolve_destination(source: Path, sha256: str, bronze_dir: Path) -> tuple[str, Path]:
    """Resuelve el nombre y la ruta de destino en bronze para `source` (CA-06).

    Por defecto usa `source.name`. Si ya existe un archivo con ese nombre en
    `bronze_dir` y su `sha256` difiere de `sha256` (colisión de nombre con
    contenido distinto, no capturada por el dedupe de CA-05), se usa en su
    lugar `<stem>__<sha8><suffix>` para no sobrescribir el original.
    """
    stored_name = source.name
    destination = bronze_dir / stored_name
    if destination.is_file() and _hash_file(destination) != sha256:
        stored_name = f"{source.stem}__{sha256[:8]}{source.suffix}"
        destination = bronze_dir / stored_name
    return stored_name, destination


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
