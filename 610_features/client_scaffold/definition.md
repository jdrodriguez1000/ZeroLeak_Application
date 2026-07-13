# Definition — client_scaffold

> Artefacto del paso 3 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `client_scaffold` (snake_case)
- **Módulo / componente:** identidad y estructura — alta de tenants en el eje multi-tenant (§11–§12 de `system_design.md`). Es el primer eslabón del ciclo de vida de un cliente: sin tenant no hay dónde ingerir, auditar ni reportar.

## Problema / Necesidad
Hoy no existe una forma consistente y segura de dar de alta un cliente nuevo en ZeroLeak. Cada tenant debe
quedar aislado en disco, con su configuración (`client.yaml`, `input/`) y su almacenamiento de datos por capas
medallion (`data/bronze|silver|gold`, `manifest.json`) listos desde el primer segundo, sin intervención manual
carpeta por carpeta y sin riesgo de exponer datos reales del cliente en el control de versiones. La feature
resuelve esa carencia: automatiza el alta de tenant como una operación única, rápida y segura por diseño.

## Alcance
**In scope:**
- Función core `create_client(name, clients_root) -> Path` que materializa la estructura canónica del tenant en disco.
- Fachada CLI `zlk client new <NOMBRE_CLIENTE>` que expone el core (la CLI no contiene lógica propia).
- Validación estricta del nombre del cliente (caracteres permitidos, no vacío, sin colisión con un tenant existente).
- Generación de placeholders versionables: `client.yaml` (identidad + `sector_id`) y los 3 YAMLs de `input/`
  (contrato, reglas, finanzas) como plantillas vacías/comentadas.
- Generación de `data/{bronze,silver,gold}` y `manifest.json` inicial vacío.
- Comportamiento no idempotente: si el tenant ya existe, la operación falla sin modificar nada (sin `--force`).
- Alta del tenant de demostración `COMPANY_DEMO` por esta misma vía.
- Cumplimiento de C-01: `data/` del tenant queda cubierta por `.gitignore` (`clients/*/data/`).

**Out of scope:**
- Ingesta de archivos reales a `bronze/` (feature `ingest`).
- Binarización Drop & Detach bronze → silver (feature `vault`).
- Cálculo de métricas, DHS, Pareto o CSVs masticados en `gold/` (features `finance`/`report`).
- Contenido "real" (más allá de placeholders válidos) de los YAMLs de `input/`.
- Idempotencia, actualización de un tenant existente o bandera `--force`.
- Registro central de clientes en base de datos: la identidad hoy es tenant + `client.yaml` (§12).

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como operador de ZeroLeak, quiero ejecutar `zlk client new <NOMBRE_CLIENTE>` para dar de alta un cliente nuevo en segundos, sin tocar código ni crear carpetas a mano. | El comando crea el tenant `clients/<NOMBRE_CLIENTE>/` con la estructura completa (`client.yaml`, `input/`, `data/{bronze,silver,gold}`, `manifest.json`) y reporta la ruta creada. |
| HU-02 | Como desarrollador del motor, quiero que la lógica de alta de tenant viva en una función core `create_client(name, clients_root) -> Path`, para que la CLI sea solo una fachada y el motor sea reutilizable/testeable como API. | `create_client` puede invocarse directamente (sin CLI) y produce el mismo resultado que `zlk client new`; la CLI delega toda la lógica a esta función. |
| HU-03 | Como operador, quiero que un nombre de cliente inválido sea rechazado con un error claro, para no terminar con tenants a medias o mal nombrados en disco. | Al invocar con un nombre inválido (vacío, caracteres no permitidos), el comando falla con un mensaje de error claro y no queda ningún artefacto parcial en `clients/`. |
| HU-04 | Como operador, quiero que el sistema me impida crear un tenant que ya existe, para no sobrescribir ni corromper accidentalmente los datos de un cliente existente. | Reintentar `zlk client new` sobre un `NOMBRE_CLIENTE` ya existente falla con un error claro; el tenant existente no se modifica ni se pierde información. |
| HU-05 | Como responsable de configurar un cliente nuevo, quiero recibir placeholders versionables de `client.yaml` y de los 3 YAMLs de `input/` (contrato, reglas, finanzas), para tener un punto de partida claro que luego completo manualmente. | Tras el alta, `client.yaml` contiene identidad + `sector_id` como placeholder, y `input/` contiene 3 archivos YAML (contrato, reglas, finanzas) vacíos/comentados y con sintaxis válida. |
| HU-06 | Como responsable de auditoría de datos, quiero que el tenant nazca con las capas medallion (`bronze/`, `silver/`, `gold/`) y un `manifest.json` vacío, para que el pipeline de ingesta tenga dónde depositar y rastrear archivos desde el primer momento. | Tras el alta, existen las carpetas `data/bronze/`, `data/silver/`, `data/gold/` y un `data/manifest.json` con un ledger inicial vacío y válido. |
| HU-07 | Como responsable de seguridad de datos, quiero que la carpeta `data/` de cada tenant quede automáticamente excluida del control de versiones, para que ningún dato real de cliente llegue jamás a git (C-01, Datos en Bóveda). | La regla `.gitignore` `clients/*/data/` está vigente y cubre la carpeta `data/` del tenant recién creado; solo `client.yaml` e `input/` quedan versionables. |
| HU-08 | Como equipo de ZeroLeak, quiero contar con un tenant de demostración `COMPANY_DEMO` creado por la misma vía oficial, para tener un ejemplo de referencia reproducible para pruebas y demos. | El tenant `clients/COMPANY_DEMO/` existe, fue generado con `create_client`/`zlk client new`, y tiene la estructura canónica completa (igual que cualquier tenant real). |

## Dependencias
- Esqueleto del motor `app/src/zeroleak/` (paquete `zeroleak`, comando `zlk`) — ya existe (T-11).
- `700_architecture/system_design.md` §11–§12 (estructura de tenant y multi-tenant) — canónico.
- `900_persistence/constraints.md` C-01 (Datos en Bóveda) — regla `.gitignore` `clients/*/data/`.
- `610_features/client_scaffold/feature_contract.md` — estrella polar de esta definición.

## Riesgos y Supuestos
- Se asume que "caracteres permitidos" para el nombre del cliente (HU-03) se acotará con precisión en `spec.md`
  (p. ej. alfanumérico + guion bajo, longitud máxima); el contrato no fija la regla exacta, solo exige que exista
  validación estricta. Queda como vacío a resolver en el paso de spec, no en definición.
- Se asume que `clients_root` es un parámetro configurable del core (no hardcodeado), coherente con que la CLI es
  fachada del core; el contrato no lo contradice pero tampoco lo detalla — se registra como supuesto razonable
  derivado de "el motor se diseña como API".
- El contrato no especifica el formato exacto ni el contenido mínimo de los placeholders YAML (más allá de
  "vacíos/comentados"); se deja abierto para `spec_writer`, siempre respetando que no debe haber datos reales ni
  sensibles en ningún placeholder.
- No se detectaron contradicciones entre el contrato y `system_design.md` §11–§12: la estructura de tenant, el
  manifiesto y la exclusión de `data/` del indexador son consistentes en ambos documentos.
