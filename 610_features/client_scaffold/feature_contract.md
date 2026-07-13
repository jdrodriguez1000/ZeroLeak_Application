# Feature Contract — client_scaffold

> Artefacto **a nivel feature**, creado por la **sesión principal** (humano + Claude Code) en el paso 2 del flujo.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de escribir la definición**.
> **Una feature = una construcción completa** (Opción A, sin bandas): un solo ciclo SDD+TDD la lleva a "terminado".

## Estrella Polar
Dar de alta un cliente nuevo en ZeroLeak en segundos: crear su **tenant** aislado en disco con la
estructura completa (config + capas medallion + manifiesto) lista para recibir sus datos, sin tocar código.

## Definición de "Terminado"
Condiciones que deben cumplirse para considerar la feature **terminada** (comportamiento end-to-end completo):
- El comando `zlk client new <NOMBRE_CLIENTE>` crea el tenant `clients/<NOMBRE_CLIENTE>/` con la estructura
  canónica de §11 del `system_design.md`:
  - `client.yaml` (identidad + `sector_id`) — placeholder versionable
  - `input/` con los 3 YAMLs de configuración del cliente (contrato, reglas, finanzas) — placeholders versionables
  - `data/` con las carpetas medallion `bronze/`, `silver/`, `gold/` y un `manifest.json` inicial vacío
- La función core `create_client(name, clients_root) -> Path` es el motor de la operación; la CLI es solo su fachada
  (P: el motor se diseña como API — la lógica no vive en la CLI).
- **Validación estricta del nombre**: nombres inválidos se rechazan con un error claro y **no** se crea nada
  (no se deja un tenant a medias).
- **Seguro por diseño (C-01)**: la carpeta `data/` del tenant queda cubierta por la regla `.gitignore`
  `clients/*/data/`; solo `client.yaml` e `input/` son versionables.
- **No idempotente**: si el tenant ya existe, el comando falla con un error claro (no sobrescribe ni fusiona).
  No hay `--force` en esta feature.
- Existe un tenant de demostración **`COMPANY_DEMO`** generado por esta misma vía, que sirve de ejemplo de referencia.

## Alcance
**In scope:**
- Core `create_client(name, clients_root) -> Path` que materializa la estructura del tenant en disco.
- Fachada CLI `zlk client new <NOMBRE_CLIENTE>`.
- Validación estricta del nombre de cliente (caracteres permitidos, no vacío, sin colisión con tenant existente).
- Generación de placeholders para `client.yaml` y los 3 YAMLs de `input/`.
- `manifest.json` inicial (ledger vacío) y carpetas medallion `bronze/`/`silver/`/`gold/`.
- Tenant de demostración `COMPANY_DEMO`.

**Out of scope (nunca, o en otra feature):**
- Ingesta de archivos reales a `bronze/` (feature `ingest`).
- Binarización Drop & Detach bronze → silver (feature `vault`).
- Cálculo de métricas, DHS, Pareto o CSVs masticados en `gold/` (features `finance`/`report`).
- Contenido "real" de los YAMLs de `input/` más allá de placeholders válidos.
- Idempotencia / actualización de un tenant existente y bandera `--force`.
- Cualquier registro central de clientes (BD): hoy la identidad es tenant + `client.yaml` (§12).

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **verificables y detallados** viven en `spec.md` como `CA-xx`.
1. Ejecutar `zlk client new <NOMBRE>` sobre un `clients_root` limpio crea el tenant con la estructura completa
   (`client.yaml`, `input/` con 3 YAMLs, `data/{bronze,silver,gold}`, `manifest.json`) y retorna/reporta su ruta.
2. Un nombre inválido es rechazado con error claro y **no** deja artefactos parciales en disco.
3. Reintentar sobre un tenant que ya existe falla con error claro y **no** modifica el tenant existente.
4. La estructura generada respeta la frontera de PII de C-01: `data/` cae bajo `.gitignore` `clients/*/data/`.
5. El tenant `COMPANY_DEMO` puede crearse por esta vía y queda con la estructura canónica.

## Dependencias
- Esqueleto del motor `app/src/zeroleak/` (paquete `zeroleak`, comando `zlk`) — ya existe (T-11).
- `700_architecture/system_design.md` §11–§12 (estructura de tenant y multi-tenant) — canónico.
- `900_persistence/constraints.md` C-01 (Datos en Bóveda) — regla `.gitignore` `clients/*/data/`.

## Relación con Hitos de Producto
- Primer **Tracer Bullet** del proyecto: valida end-to-end la metodología Notebook→SDD+TDD y el flujo de 13 pasos.
- Habilita el eje **multi-tenant** (§12): sin dar de alta un cliente no hay dónde ingerir ni auditar; es la base
  sobre la que se construyen las features posteriores (`ingest`, `vault`, `modules`, `finance`, `report`).
