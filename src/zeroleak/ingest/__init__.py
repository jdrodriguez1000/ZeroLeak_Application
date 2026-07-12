"""ingest — registro en bronze + manifiesto de procesamiento.

Copia los archivos nuevos del cliente a `data/bronze/` y mantiene el
`manifest.json` (ledger idempotente: dedupe por sha256, estado
pending/processed). Define el delta del modo incremental. Ver system_design §10, §11.
"""
