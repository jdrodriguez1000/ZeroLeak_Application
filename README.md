# ZeroLeak

**Auditor de fugas de dinero ocultas en los datos.** Detecta el *Cost of Poor
Data Quality* (COQD) —duplicados, nulos, cálculos rotos, inconsistencias— y su
propuesta de valor es la **traducción financiera**: convierte errores técnicos
en dólares perdidos y los prioriza con un Pareto financiero (80/20) accionable.

> Diagnostica y traduce a dinero; **no** limpia ni corrige los datos del cliente.

Diseño completo en [`700_architecture/system_design.md`](700_architecture/system_design.md).

## Estructura del motor (`app/src/zeroleak/`)

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
por `zlk client new <NOMBRE_CLIENTE>` (ver [Uso del CLI](#uso-del-cli)):

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

## Entorno de desarrollo

Requiere **Python 3.13+**. En Windows el `python` del PATH suele ser 3.12, así
que invoca el intérprete 3.13 explícitamente con `py -3.13` al crear el entorno.

### 1. Crear y activar el entorno virtual

```powershell
# desde la raíz del repo
py -3.13 -m venv .venv          # crea .venv/ con Python 3.13

# Activar (PowerShell):
.\.venv\Scripts\Activate.ps1     # el prompt mostrará el prefijo (.venv)
```

> Si PowerShell bloquea la activación por ExecutionPolicy, ejecuta una vez en la
> sesión: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

```bash
# Activar (Git Bash / macOS / Linux):
source .venv/Scripts/activate     # en Unix: source .venv/bin/activate
```

### 2. Instalar el paquete y las dependencias de desarrollo

```bash
pip install -e ".[dev]"   # instala el paquete (comando `zlk`) + pytest
```

### 3. Correr la suite de pruebas

```bash
pytest                     # con el entorno activado
# o sin activar el entorno:
.venv/Scripts/python.exe -m pytest app/tests -v
```

## Uso del CLI

El comando de consola es **`zlk`** (queda disponible tras `pip install -e`).

### Crear un tenant nuevo

```powershell
zlk client new MI_CLIENTE
```

Materializa de forma **atómica** el árbol canónico bajo `clients/MI_CLIENTE/`
(relativo al directorio actual; configurable con la variable de entorno
`ZEROLEAK_CLIENTS_ROOT`) e imprime la ruta creada.

El nombre debe cumplir el patrón `^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$`
(letras, dígitos, `_`, `-` y acentos/ñ; sin espacios, puntos ni símbolos).

**Códigos de salida:**

| Código | Significado |
|:---:|---|
| `0` | Éxito — imprime la ruta del tenant creado |
| `1` | Sintaxis del comando incorrecta (uso: `zlk client new <NOMBRE_CLIENTE>`) |
| `2` | Nombre de cliente inválido (no cumple el patrón) |
| `3` | El tenant ya existe (no se sobrescribe, C-06) |

Ante cualquier fallo **no queda ningún residuo** en `clients/` (validación previa
o limpieza del staging).

## Metodología

La metodología de desarrollo (Notebook → SDD+TDD) está en
[`905_guideline/methodology.md`](905_guideline/methodology.md).
