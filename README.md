# ZeroLeak

**Auditor de fugas de dinero ocultas en los datos.** Detecta el *Cost of Poor
Data Quality* (COQD) —duplicados, nulos, cálculos rotos, inconsistencias— y su
propuesta de valor es la **traducción financiera**: convierte errores técnicos
en dólares perdidos y los prioriza con un Pareto financiero (80/20) accionable.

> Diagnostica y traduce a dinero; **no** limpia ni corrige los datos del cliente.

Diseño completo en [`700_architecture/system_design.md`](700_architecture/system_design.md).

## Estructura del motor (`src/zeroleak/`)

| Paquete | Responsabilidad |
|---|---|
| `cli.py` | Fachada de línea de comandos del Científico de Datos (comando `zlk`). |
| `core` | Pipeline, `ClientContext`, contratos y scaffolding de tenants. |
| `ingest` | Registro en bronze + manifiesto de procesamiento (`manifest.json`). |
| `vault` | "Datos en Bóveda": Drop & Detach (bronze → silver), sin PII. |
| `modules` | Categorías de error: `identity`, `structure`, `relational`, `category`. |
| `finance` | Traductor de errores a dólares (USD). |
| `report` | Data ROI Dashboard, Data Health Score y CSVs masticados → gold. |
| `llm` | Acceso a LLM encapsulado (solo datos sintéticos, nunca PII). |

## Datos del cliente (multi-tenant)

Cada cliente es un **tenant** autocontenido bajo `clients/<CLIENTE>/`, generado
por `zlk client new <NOMBRE_CLIENTE>` (feature, aún no implementada):

```
clients/<CLIENTE>/
├── client.yaml     # identidad + sector_id      [versionable]
├── input/          # YAMLs 1–3 del cliente       [versionable]
└── data/           # 🔒 datos reales — en .gitignore (C-01)
    ├── bronze/     #   originales inmutables (con PII)
    ├── silver/     #   binarizado sin PII (Drop & Detach)
    └── gold/       #   resultados: métricas, Pareto, CSVs masticados
```

`COMPANY_DEMO` es el tenant de demostración que opera sobre **datos sintéticos**.

## Desarrollo

```bash
pip install -e ".[dev]"   # instala el paquete (comando `zlk`) + pytest
pytest
```

Requiere **Python 3.13+**. La metodología de desarrollo (Notebook → SDD+TDD)
está en [`905_guideline/methodology.md`](905_guideline/methodology.md).
