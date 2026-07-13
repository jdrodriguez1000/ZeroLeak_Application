"""ingest — registro en bronze + manifiesto de procesamiento.

Copia los archivos nuevos del cliente a `data/bronze/` y mantiene el
`manifest.json` (ledger idempotente: dedupe por sha256, estado
pending/processed). Define el delta del modo incremental. Ver system_design §10, §11.
"""
from __future__ import annotations

from zeroleak.ingest.core import IngestResult, TenantNotFoundError, ingest_paths

__all__ = ["IngestResult", "TenantNotFoundError", "ingest_paths"]
