# System Design — ZeroLeak

> Documento de diseño de arquitectura del sistema. Describe **qué** construimos y **cómo** se organiza, antes de escribir código. Es un documento vivo: el alcance y el flujo se afinarán al construir cada feature.

**Versión:** 0.2 · **Fecha:** 2026-07-12
**Fuente de dominio:** `980_documents/Salud de datos.docx`
**Restricciones vinculantes:** `900_persistence/constraints.md` (C-01 🔒 Datos en Bóveda, C-02 solo diagnostica, C-03 merge humano).

> **Cambios v0.2:** los datos del cliente pasan a vivir **dentro del tenant** (`clients/<CLIENTE>/`) con **capas medallion** (bronze/silver/gold) y un **manifiesto de procesamiento** que rastrea qué archivo ya se auditó y cuál no; la carpeta de configuración del cliente se renombra de `config/` a **`input/`**. Ver §11.

---

## Índice
1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Principios de Diseño](#2-principios-de-diseño)
3. [Restricciones y Decisiones Base](#3-restricciones-y-decisiones-base)
4. [Visión General de la Arquitectura](#4-visión-general-de-la-arquitectura)
5. [Modelo de Configuración: los 4 YAMLs](#5-modelo-de-configuración-los-4-yamls)
6. [Categorías de Error y Traducción Financiera](#6-categorías-de-error-y-traducción-financiera)
7. [Arquitectura de Seguridad "Datos en Bóveda"](#7-arquitectura-de-seguridad-datos-en-bóveda)
8. [Data Health Score](#8-data-health-score)
9. [Salida: Data ROI Dashboard](#9-salida-data-roi-dashboard)
10. [Modos de Operación: Histórico vs Incremental](#10-modos-de-operación-histórico-vs-incremental)
11. [Estructura de Carpetas y Capas Medallion](#11-estructura-de-carpetas-y-capas-medallion)
12. [Multi-tenant y Aislamiento por Cliente](#12-multi-tenant-y-aislamiento-por-cliente)
13. [Encapsulamiento del LLM](#13-encapsulamiento-del-llm)
14. [Camino de Evolución a SaaS](#14-camino-de-evolución-a-saas)
15. [Alcance MVP: Retail Moderno](#15-alcance-mvp-retail-moderno)
16. [Puntos Abiertos y Futuro](#16-puntos-abiertos-y-futuro)

---

## 1. Contexto y Objetivo

Las empresas pierden dinero silenciosamente por la **mala calidad de sus datos** (COQD — *Cost of Poor Data Quality*): duplicados, nulos, valores centinela, cálculos rotos, inconsistencias entre sistemas. El fenómeno es la **"ceguera de datos"**: como nadie ve una factura que diga *"Costo por datos repetidos: $5,000"*, la gerencia asume que el costo es cero. Firmas como Gartner e IDC estiman pérdidas del **10%–25% de los ingresos** por esta causa.

**ZeroLeak** es un **auditor de fugas de dinero ocultas en los datos**. Su propuesta de valor no es el diagnóstico técnico, sino la **traducción financiera**: convierte errores técnicos en dólares perdidos y los prioriza con un **Pareto financiero** (80/20) accionable.

**Posicionamiento:** ZeroLeak es una herramienta de **Inteligencia de Negocios / Auditoría**, no de TI. Es el *médico que muestra la radiografía del tumor financiero*, no el cirujano que opera. **Diagnostica y traduce a dinero; no limpia ni corrige** los datos del cliente (C-02).

**Evolución del producto (Servicio → SaaSw → SaaS):**
- **Hoy (Fase Servicio):** un **script de Python local** (`validador.py`) que ejecuta el **Científico de Datos** sobre los archivos del cliente en su propia máquina (blindaje "Datos en Bóveda", C-01).
- **Mañana (SaaSw → SaaS):** una **plataforma web multi-tenant** donde el cliente carga sus archivos y consulta su *Data ROI Dashboard*, con conectores automáticos a sus sistemas.

> **Principio fundacional:** *lo que se construye hoy como script local debe ser el motor (backend) del software del mañana.* Cada decisión de arquitectura de este documento se toma para **habilitar esa evolución sin reescribir el núcleo** (ver §2 y §14).

---

## 2. Principios de Diseño

1. **Determinista y local por defecto.** El motor de auditoría es Python puro y reproducible, corre 100% en la máquina del DS. El resultado no depende de un LLM en tiempo de ejecución.
2. **Diagnostica, no limpia (C-02).** ZeroLeak audita y traduce a dinero; entrega los errores "masticados" (CSVs) para que el equipo del cliente los resuelva. La limpieza queda **fuera de alcance** de forma explícita y recurrente.
3. **Datos en Bóveda (C-01, inviolable).** El LLM solo ve **datos sintéticos**; ningún dato real del cliente sale de la máquina local. La seguridad es **por diseño**, no por configuración opcional (ver §7).
4. **Configuración sobre código (config-driven).** La estructura de los datos, las reglas de negocio, las variables financieras y las plantillas de sector viven en **archivos YAML**, no en el código Python. Un cliente o un sector nuevo **no requiere reprogramar el motor** (ver §5).
5. **El motor se diseña como una API.** La lógica de auditoría se desacopla de la interfaz: entra por un **contrato de entrada** y sale por un **contrato de salida** (JSON + CSVs). La CLI del DS es solo la **primera fachada**; el frontend web del SaaS será otra fachada sobre el mismo motor.
6. **Escalabilidad en dos ejes ortogonales:**
   - **Eje clientes (multi-tenant):** aislamiento por cliente desde el día 1; la identidad cliente/sector es explícita y externalizada a config → mañana son filas en una base de datos.
   - **Eje arquitectura (Servicio → SaaSw → SaaS):** cada componente local tiene una **costura** documentada hacia su equivalente en la nube (ver §14).
7. **Módulos de error independientes.** Cada una de las 4 categorías de error (§6) es un módulo de código autónomo y componible, de modo que el alcance de una auditoría se arma activando/desactivando módulos.
8. **Trazabilidad del cálculo.** Toda pérdida reportada es auditable: el cliente puede ver *"esto se calculó multiplicando X por Y"* y ajustar la variable. Blinda contra la "alucinación de costos" (ver §16, premortem).

---

## 3. Restricciones y Decisiones Base

| # | Restricción / Decisión | Valor |
|---|---|---|
| R1 | Lenguaje | Python 3.13+ |
| R2 | Interfaz (hoy) | Script / CLI ejecutado por el Científico de Datos |
| R3 | Configuración | Archivos **YAML** (4 tipos, ver §5) |
| R4 | Entrada de datos del cliente | Archivos **CSV / Excel** (exportaciones estándar de sus sistemas) |
| R5 | Salida de resultados | **JSON** (máquina) + **CSVs "masticados"** (para el cliente) + reporte ejecutivo |
| R6 | Persistencia | Sistema de archivos, **tenant (carpeta) por cliente** con capas medallion (bronze/silver/gold) + manifiesto de procesamiento; sin BD por ahora |
| R7 | Motor | 100% **local** en la máquina del DS (C-01) |
| R8 | Datos que ve el LLM | **Solo sintéticos** ("matrices de mentiras", 3–5 filas falsas) — C-01 |
| R9 | Alcance funcional | **Diagnóstico + traducción financiera**; **no** limpieza (C-02) |
| R10 | Integración a `main` | Solo vía **PR con merge humano** (C-03) |
| R11 | Librerías base previstas | Pandas, NumPy, Pydantic (validación de contratos) |

---

## 4. Visión General de la Arquitectura

ZeroLeak es un **motor de auditoría** que consume **datos del cliente** (CSV/Excel) + **configuración** (YAML) y produce un **diagnóstico financiero** (JSON + CSVs + reporte). El motor está separado de la interfaz por una frontera limpia.

```
   ┌──────────────────────── FACHADA (hoy: CLI del DS) ─────────────────────────┐
   │  zeroleak audit <cliente> --periodo 2026-Q3-Q1                             │
   └───────────────────────────────────┬───────────────────────────────────────┘
                                        │  contrato de entrada
                                        ▼
   ┌──────────────── MOTOR (validador.py — "como una API") ─────────────────────┐
   │                                                                            │
   │  load_config      ── lee los 4 YAMLs (contrato, reglas, finanzas, sector)  │
   │  ingest           ── registra archivos nuevos en bronze + manifest (§11)   │
   │  load_data        ── lee bronze PENDIENTE (LOCAL, en Bóveda)               │
   │  vault (§7)       ── Drop & Detach: bronze → silver (banderas 1/0, sin PII)│
   │  validate         ── módulos de error (§6): Identidad·Estructura·          │
   │                      Relacional·Categorización                            │
   │  translate        ── multiplica errores × variables financieras → USD      │
   │  score            ── Data Health Score (§8)                               │
   │  report           ── Pareto financiero + CSVs masticados (§9)             │
   │                                                                            │
   └───────────────────────────────────┬───────────────────────────────────────┘
                                        │  contrato de salida (JSON + CSV + reporte)
                                        ▼
                        clients/<CLIENTE>/  (aislamiento en disco)
```

**Componentes de código previstos (`app/src/zeroleak/`):**
- **`cli`** — fachada de línea de comandos para el DS; interpreta comandos y llama al motor. *→ Evolución: se reemplaza/complementa por una API web + frontend; el motor no cambia.*
- **`core`** — el motor: orquestación del pipeline, `ClientContext`, contratos de entrada/salida, resolución de rutas.
- **`ingest`** — registra los archivos que entran a **bronze** y mantiene el **manifiesto de procesamiento** (qué se procesó y qué no) (§11).
- **`vault`** — la lógica "Datos en Bóveda": lee bronze y produce **silver** (binarización Drop & Detach, PII eliminada) (§7).
- **`modules`** — un módulo por categoría de error (§6), componibles.
- **`finance`** — traductor de errores a dólares usando las variables financieras del cliente.
- **`report`** — construcción del Data ROI Dashboard y exportación de CSVs masticados.
- **`llm`** — acceso a LLM encapsulado, **solo para diseño/desarrollo con datos sintéticos**, nunca en el camino de datos reales (§13).

---

## 5. Modelo de Configuración: los 4 YAMLs

La inteligencia de ZeroLeak vive en **configuración declarativa**, no en el código. Esto permite auditar 1 archivo o 100 tablas, y atender un cliente o un sector nuevo, **sin tocar Python**. Hay cuatro YAMLs con responsabilidades distintas:

| # | YAML | Naturaleza | Responsabilidad | Cambia con… |
|---|---|---|---|---|
| 1 | **Contrato de Datos** | Estructura | Valida que el archivo esté bien formado: columnas, tipos, nulos permitidos, llaves. Si falla, el análisis se detiene. | cada archivo del cliente |
| 2 | **Reglas de Negocio** | Lógica del dinero | Define las validaciones que cuestan dinero (cálculos derivados, rangos, integridad referencial) y a qué **tipo de impacto** se asocian. | el sector / caso |
| 3 | **Variables Financieras** | Multiplicadores | Guarda el valor monetario/temporal de los procesos del cliente (salario/hora, costo de envío, ticket promedio, tasa de conversión…). Es el diccionario que traduce errores a USD. | cada cliente |
| 4 | **Maestro de Sectores** | Plantillas de inteligencia | Propiedad de ZeroLeak. Define, por industria, qué archivos se piden, qué dolores tiene y qué reglas se sugieren. | evolución del producto |

**Cómo se integran (ejemplo del flujo):**
1. **YAML 3 (Finanzas)** identifica al cliente y su `sector_id`, y extrae sus multiplicadores.
2. **YAML 4 (Sectores)** activa, para ese `sector_id`, los archivos típicos y las reglas sugeridas.
3. **YAML 1 (Contrato)** verifica que el archivo cargado tenga la estructura esperada.
4. **YAML 2 (Reglas)** ejecuta las validaciones; cada error detectado se multiplica por el multiplicador correspondiente del YAML 3.

> **→ Evolución a SaaS:** en la Fase 3, los 4 YAMLs se convierten en **tablas relacionales**: el Maestro de Sectores es una tabla global; contrato, reglas y variables financieras se vinculan al perfil del cliente por llaves foráneas. El motor sigue leyendo "config"; solo cambia el *origen* (archivo → BD) detrás de `load_config`.

---

## 6. Categorías de Error y Traducción Financiera

El motor clasifica los errores en **4 grupos**, de lo más simple (un campo) a lo más complejo (relación entre archivos). Cada grupo es un **módulo de código independiente** (§2.7) y tiene un impacto financiero directo.

| # | Categoría | Qué detecta | Impacto financiero típico |
|---|---|---|---|
| 1 | **Identidad y Duplicación** | Filas repetidas; mismo cliente con dos IDs (fuzzy matching "Juan Pérez" vs "Juan Perez Sr."). | Envíos/llamadas dobles, presupuesto de pauta quemado, conteos inflados. |
| 2 | **Integridad y Estructura** | Nulos en campos obligatorios, valores centinela (9999), formatos rotos, y **cálculos derivados** (`precio × cantidad ≠ total`). | Parálisis operativa; **descuadre contable real** (dinero que falta o sobra en caja). |
| 3 | **Consistencia Relacional** | (multi-archivo) Integridad referencial: productos fantasma (venta con `id_producto` inexistente), órdenes zombi, inconsistencias de precio entre tablas. | Fugas críticas: pérdida de inventario, descuadres severos, sospecha de fraude. |
| 4 | **Categorización y Contexto** | Datos bien escritos pero mal clasificados: "Sr/Señor/Senior", categorías mezcladas, texto libre en el POS. | Segmentación rota, reportes sesgados, inventario que no descarga insumos. |

**Traducción financiera — el motor produce un "cuarteto de métricas":**

*Métricas de dinero:*
- **Fuga de dinero / pérdida directa** — desembolso presente por el error (duplicados en envío, cobros de menos). `Σ registros_erróneos × costo_unitario`.
- **Disminución de ingresos / costo de oportunidad** — dinero que no entró (leads con contacto nulo). `leads_perdidos × %conversión × ticket_promedio`.

*Métricas de tiempo:*
- **Tiempo no productivo** — salario pagado por limpieza manual. `n_personas × horas_mes × salario_hora`.
- **Costo por retraso** — decisiones tardías por reportes que no salen a tiempo.

> **→ Evolución:** los módulos son la unidad de composición del producto. En SaaS, activar/desactivar módulos por plan de suscripción o por sector es directo, sin tocar el core.

---

## 7. Arquitectura de Seguridad "Datos en Bóveda"

Restricción **C-01 (inviolable)**. La protección no depende de encriptar archivos, sino de una **separación absoluta de responsabilidades** entre la IA que diseña el código y el entorno local que procesa la información real.

```
[ Motor de IA / LLM (Nube) ] ── enseña y programa ──► [ Estructuras + código ]
   (solo ve datos SINTÉTICOS)                                   │
                                                        (el código baja a la máquina)
                                                                 │
                                                                 ▼
[ Máquina local del DS (Bóveda) ] ◄── procesa datos REALES ── [ validador.py ]
```

**Cuatro capas de blindaje:**

1. **El LLM solo diseña, no procesa.** El proveedor de IA actúa como arquitecto/ingeniero de software: solo ve estructuras, YAMLs y **datos sintéticos** ("matrices de mentiras", 3–5 filas con `test1@correo.com`, `Usuario 1`). Ningún modelo en la nube toca los CSV/Excel reales.
2. **La Bóveda local.** `validador.py` se ejecuta 100% local. La lectura de filas reales, la detección de errores y el cálculo de pérdidas ocurren en la RAM y el procesador de la máquina del DS. Ningún dato real sale hacia servidores de IA.
3. **Binarización — técnica Drop & Detach.** Para auditar campos sensibles (correo, nombre, teléfono): el motor crea columnas **bandera** (`flag_email_faltante = 1|0`) analizando el dato real localmente, e **inmediatamente elimina la columna de texto original**. Toda la matemática del Pareto se calcula **sumando unos y ceros**, eliminando la PII de raíz.
4. **Aislamiento del indexador.** Los datos reales viven en el **tenant de cada cliente**, en `clients/<CLIENTE>/data/` (capas medallion, §11), y esa subcarpeta se mantiene **fuera del indexador**: regla `.gitignore` `clients/*/data/` + exclusión de contexto de los agentes de IA. Solo `client.yaml` e `input/` (config sin datos reales) se versionan. La seguridad queda **automatizada por diseño**.

> **Frontera física de PII (medallion, §11):** la PII solo existe en **bronze**. Desde **silver** en adelante —y por tanto en **gold** y en todo output— no hay PII: la separación de capas hace el cumplimiento de C-01 **auditable** (se puede verificar que silver/gold no contienen columnas de texto sensible).

> **Verificación:** el cumplimiento de C-01 se comprueba en `verification.md` de cada feature. Ningún artefacto que el LLM vea puede contener datos reales.
>
> **→ Evolución a SaaS:** el reto de la Fase 3 (conectar la BD del cliente) choca con Legal/Ciberseguridad (ver premortem §16). La arquitectura de Bóveda —binarización temprana y cómputo sobre banderas— es la base del argumento de privacidad que habilita esa conversación.

---

## 8. Data Health Score

El **Data Health Score (DHS)** es el indicador global de salud que hiere el orgullo del gerente y ancla la conversación. **No** se calcula de forma puramente técnica (un archivo con 90% de filas con "Sr/Senior" mal escrito puede estar financieramente sano). El motor soporta **dos métodos** y elige según los datos disponibles del cliente:

**A. DHS Financiero** *(preferido cuando el cliente entrega su facturación)*
```
DHS = ( 1 − Pérdida Económica Total Detectada / Facturación del Periodo ) × 100
```
Ejemplo: pérdida $7,000 sobre facturación $100,000 → **DHS = 93%** ("tus datos capturan el 93% de tus ingresos; hay una fuga del 7% evaporándose").

**B. DHS Operativo ponderado** *(cuando el cliente no comparte su facturación)*
Promedio ponderado del % de filas limpias por categoría, con pesos por gravedad:
```
DHS_op = ( %limpios_Rel×4 + %limpios_Dup×3 + %limpios_Est×2 + %limpios_Cat×1 ) / 10
```
Pesos: Relacional=4, Identidad/Duplicados=3, Estructura/Cálculos=2, Categorización=1. Una relación rota (productos fantasma) desploma el score; categorías mal escritas casi no lo mueven.

> **Decisión de diseño:** el motor implementa **ambos**; `report` selecciona el método según si el YAML 3 (Variables Financieras) incluye o no la facturación del periodo. Esto mantiene el mismo motor válido para clientes celosos y para clientes abiertos, y es directo de exponer como opción en el SaaS.

---

## 9. Salida: Data ROI Dashboard

La salida aplica el **Principio de Pareto (80/20) a la yugular del gerente**: no se entregan 500 errores, se entrega una **hoja de ruta masticada**. Tres niveles de lectura, de lo general a lo específico:

**Nivel 1 — Resumen Ejecutivo (el gancho).**
- **Data Health Score** (§8), p. ej. 74%.
- **Contador de pérdida total:** 🔴 *Impacto financiero del periodo: $8,450 USD tirados a la basura.*

**Nivel 2 — Pareto de Retorno (la idea estrella).**
Gráfico de Pareto donde el eje vertical mide **dólares perdidos**, no cantidad de errores. Ordena los errores por impacto financiero acumulado y marca el 80/20:
> *"Si tu equipo soluciona los 2 errores principales, eliminas el 82% del impacto financiero trabajando solo sobre el 15% de tus datos."*

Esto invierte la intuición del cliente: 4,000 filas de "Sr/Senior" ($950) importan menos que 120 filas de cálculo roto ($4,900).

**Nivel 3 — Desglose Operativo (para los analistas del cliente).**
Los **CSVs "masticados"** — la "receta de cocina" que ZeroLeak sí entrega (aunque no limpie, C-02): archivos exactos con las filas a corregir (`productos_fantasma_para_arreglar.csv`, `duplicados_para_fusionar.csv`, `ventas_con_cobro_menor.csv`), listos para que el ingeniero del cliente los resuelva en horas, no semanas. Se acompañan de "especificaciones técnicas para tu equipo de IT".

> **→ Evolución:** en la Fase 1 esto es un reporte (PDF/tabla) que arma el DS; en la Fase 3, es la **pantalla principal** del SaaS, con un botón por barra del Pareto: *[🤖 Corregir este 20%]* (integración futura, fuera del alcance de diagnóstico).

---

## 10. Modos de Operación: Histórico vs Incremental

ZeroLeak opera en **dos modos**, y el paso del primero al segundo es lo que convierte una consultoría de un solo uso en un negocio de ingresos recurrentes (el "antivirus" de los datos).

**Modo Histórico (auditoría inicial — el gancho).**
Analiza toda la data entregada de un periodo. Produce el Data ROI Dashboard completo. Es la "radiografía" que abre los ojos del gerente ("el año pasado perdiste $50,000").

**Modo Incremental / Quincenal (monitoreo — la suscripción).**
No re-analiza toda la historia: mide el **Delta de errores** del último periodo.
```
[Datos nuevos del periodo] → [Motor de Validación] → [Errores NUEVOS] → [Alerta express]
```
El **manifiesto de procesamiento** (§11) define el delta sin ambigüedad: son los archivos en `bronze/` con estado `pending`. El motor nunca reprocesa lo ya marcado `processed`, garantizando idempotencia. El reporte es corto y accionable: *"En esta quincena entraron 12 errores nuevos → fuga potencial $320 USD. Descarga el micro-CSV con esas 12 filas para arreglarlas antes del cierre."* Incluye un **"Top Ofensores"** (qué canal/empleado originó la basura), lo que permite corrección en caliente y educación del personal.

> **→ Evolución:** el modo incremental es la base del **MRR** del SaaS. En Fase 3 se dispara automáticamente (ej. cada lunes 8:00 AM) sobre los datos que entran por conectores. El motor de cálculo del delta es el mismo; cambia el disparador (manual → agendado).

---

## 11. Estructura de Carpetas y Capas Medallion

Cada cliente es un **tenant**: una carpeta autocontenida bajo `clients/<CLIENTE>/` que reúne **toda** su información (configuración + datos + resultados). Los datos reales se organizan en **capas medallion** dentro del tenant.

```
ZeroLeak_Application/
├── app/                           # código y activos versionables del motor
│   ├── src/zeroleak/              # paquete Python — el MOTOR
│   │   ├── cli.py                 # fachada CLI (hoy)
│   │   ├── core/                  # pipeline, ClientContext, contratos, rutas
│   │   ├── ingest/                # registro en bronze + manifiesto de procesamiento
│   │   ├── vault/                 # Datos en Bóveda: Drop & Detach (bronze → silver), §7
│   │   ├── modules/               # un módulo por categoría de error (§6)
│   │   │   ├── identity/  structure/  relational/  category/
│   │   ├── finance/               # traductor de errores → USD
│   │   ├── report/                # Data ROI Dashboard + CSVs masticados → gold
│   │   └── llm/                   # acceso LLM (solo sintéticos, §13)
│   ├── config/
│   │   └── sectors/               # YAML 4: Maestro de Sectores (global, propiedad de ZeroLeak)
│   ├── data_synthetic/            # "matrices de mentiras" que ve el LLM (falsas, §7) [versionable]
│   └── tests/                     # suite de pruebas (pytest)
│
├── clients/                       # ← multi-tenant: un tenant (carpeta) por cliente
│   └── SANDUCHERIA/               # === TENANT DEL CLIENTE (todo lo suyo aquí) ===
│       ├── client.yaml            # identidad + sector_id                  [versionable]
│       ├── input/                 # YAMLs 1–3 del cliente (config)         [versionable]
│       │   ├── contrato_*.yaml    #   YAML 1: Contrato de Datos (por archivo)
│       │   ├── reglas_*.yaml      #   YAML 2: Reglas de Negocio
│       │   └── finanzas.yaml      #   YAML 3: Variables Financieras
│       └── data/                  # 🔒 datos reales — EN .gitignore + excluido de IA (C-01)
│           ├── bronze/            #   🥉 originales inmutables (con PII), tal cual llegan
│           ├── silver/            #   🥈 binarizado Drop & Detach (banderas 1/0, SIN PII)
│           ├── gold/              #   🥇 resultados: métricas, Pareto, CSVs masticados
│           └── manifest.json      #   ledger: qué archivo se procesó y cuál no
│
├── 600_template/  610_features/  700_architecture/  900_persistence/   # metodología, diseño, seguimiento
```

**Capas Medallion (adaptadas a ZeroLeak).** ZeroLeak **no limpia** (C-02), por lo que "silver" **no** significa "datos limpios": significa el dato **seguro** para calcular.

| Capa | Contenido | Escrita por | Regla |
|---|---|---|---|
| 🥉 **bronze** | Copia **inmutable** de los CSV/Excel originales del cliente (con PII). | `ingest` | Nunca se altera; evidencia fiel de lo recibido. Se **agregan** archivos, no se sobreescriben. |
| 🥈 **silver** | Representación **binarizada y sin PII** (Drop & Detach): banderas 1/0 + campos no sensibles. | `vault` | Frontera física de PII: de aquí en adelante no hay datos personales (§7). |
| 🥇 **gold** | Resultados: métricas financieras, DHS, Pareto y **CSVs masticados** para el cliente. | `finance` / `report` | Es lo que se entrega; se calcula sobre silver, nunca sobre bronze directamente. |

> **Decisión:** silver se **mantiene como capa física** (se persiste en disco), porque hace el cumplimiento de C-01 **auditable** —se puede verificar que silver/gold no contienen PII.

**Manifiesto de procesamiento (`manifest.json`) — responde "¿cuál trabajo?".**
El motor **no** navega carpetas por fecha para adivinar qué procesar. Mantiene un **ledger** que registra cada archivo que entra a bronze:

```json
{
  "files": [
    {
      "file": "ventas_pos_2026-07-Q1.csv",
      "sha256": "a1b2…",                // identidad por CONTENIDO, no por nombre
      "period": "2026-07-Q1",
      "ingested_at": "2026-07-16T09:00:00",
      "status": "processed",             // pending | processed | failed
      "run_id": "run-2026-07-16-01",     // corrida que lo procesó
      "output": "data/gold/2026-07-Q1/"
    }
  ]
}
```

- **Ingesta:** cuando llegan archivos nuevos, `ingest` los copia a `bronze/` y los registra como `pending` (dedupe por `sha256`: reenviar el mismo archivo no lo duplica ni lo reprocesa).
- **Procesamiento:** el motor trabaja los `pending`, produce silver + gold y los marca `processed`. **Idempotente:** nunca reprocesa lo ya `processed`.
- **Modo incremental (§10):** el **delta** es simplemente el conjunto de archivos `pending`. "Otro mes" = subir el archivo nuevo; el **manifiesto** (no una carpeta que haya que señalar) decide qué se audita.
- El **periodo es metadato** (campo del manifiesto), no una carpeta que el usuario deba elegir. Los outputs sí pueden subdividirse por periodo dentro de `gold/` (organización post-proceso, sin ambigüedad).

> **→ Evolución a SaaS:** `input/` → tabla de configuración del tenant; `data/` (medallion) → almacenamiento por tenant (schema/bucket); `manifest.json` → tabla de *ingestions* con estado. `ClientContext` abstrae el origen, así que el motor no cambia (§14).

---

## 12. Multi-tenant y Aislamiento por Cliente

- **Identidad del cliente = tenant + `client.yaml`** (con su `sector_id`), sin registro central por ahora.
- Cada cliente es un **tenant** = una carpeta independiente y autocontenida bajo `clients/<CLIENTE>/` (config en `input/`, datos reales en `data/` con capas medallion); **no hay estado compartido** entre clientes.
- El **Científico de Datos** opera múltiples clientes ejecutando el motor con distintos identificadores.
- El motor **nunca hardcodea** nada de un cliente: todo lo específico vive en su `input/` y sus datos. Agregar un cliente = crear su tenant + sus 3 YAMLs (10 minutos), sin tocar código.

> **→ Evolución a SaaS:** el modelo carpeta-por-cliente migra a **tablas multi-tenant** (o buckets por tenant) sin cambiar la interfaz de `ClientContext`: las rutas/consultas se resuelven detrás de esa abstracción. El aislamiento lógico de hoy es el aislamiento por `tenant_id` de mañana.

---

## 13. Encapsulamiento del LLM

- Todo acceso a LLM pasa por `app/src/zeroleak/llm/` detrás de una interfaz estable.
- **El LLM NO participa del camino de datos reales.** Su rol es de **desarrollo/diseño**: ayudar a construir reglas, módulos y estructuras usando **exclusivamente datos sintéticos** (C-01, §7). El motor de auditoría en ejecución es **determinista y sin LLM**.
- Si en el futuro se usa LLM para narrar hallazgos o proponer configuración, opera **solo sobre agregados/banderas** (nunca PII) y su salida se **valida** antes de escribir artefactos.
- **Proveedor por defecto:** API de Anthropic (Claude), detrás de la interfaz, de modo que el proveedor/modelo sea intercambiable sin tocar el motor.

> **Beneficio:** el core es testeable sin LLM y reproducible; la Bóveda se mantiene intacta porque el LLM y los datos reales viven en planos separados por diseño.

---

## 14. Camino de Evolución a SaaS

ZeroLeak recorre tres fases. **Lo que se construye hoy es el motor de todas.**

| Fase | Qué es | Interfaz | Procesamiento | Datos |
|---|---|---|---|---|
| **1 · Servicio** *(hoy)* | Consultoría de diagnóstico financiero de datos | Script/CLI del DS | Local (Bóveda) | CSV/Excel que el cliente envía |
| **2 · SaaSw** | Software con servicio (concierge) | Portal web simple + carga de archivos | Semiautomático: el DS revisa y aprueba | Carga web → almacenamiento seguro |
| **3 · SaaS** | Producto self-service y escalable | Frontend completo + API | Automático (microservicios, agendado) | Conectores a POS/CRM/BD del cliente |

**Actores del sistema (RBAC futuro — 6 roles).** Se documentan ahora para que el modelo de datos escale sin reescritura; **no se construyen en la Fase 1**. Se implementan como **una sola tabla de usuarios con `rol_id`** (RBAC):

| Rol | Lado | Ve / puede |
|---|---|---|
| **SuperAdmin** | ZeroLeak | Todo el sistema + métricas de facturación del negocio |
| **Admin_ZeroLeak** | ZeroLeak | Asigna Científicos de Datos a Clientes |
| **Data_Scientist** | ZeroLeak | Solo sus clientes asignados; ejecuta/revisa el motor y publica reportes |
| **Cliente_Uploader** | Cliente | Solo carga los archivos de la quincena |
| **Cliente_Viewer** | Cliente | Tablas, Pareto y descarga de CSVs masticados |
| **Cliente_Owner** | Cliente | Dashboard ejecutivo (dinero perdido vs recuperado); paga la suscripción |

**Mapa de costuras (qué de hoy se convierte en qué mañana):**

| Componente hoy (Fase 1) | Pieza mañana (Fase 3) | Costura que lo habilita |
|---|---|---|
| 4 YAMLs | Tablas relacionales | `load_config` abstrae el origen (archivo → BD) |
| Tenant por cliente (`clients/<X>/`: `input/` + `data/` medallion) | Esquema/bucket por tenant en BD / object storage | `ClientContext` resuelve rutas/consultas |
| Manifiesto de procesamiento (`manifest.json`) | Tabla de *ingestions* con estado | `ingest` abstrae el ledger (archivo → tabla) |
| CLI del DS | Frontend web + API | El motor ya es "como una API" (§2.5) |
| Ejecución local manual | Microservicios agendados | El pipeline no depende del disparador |
| Modo incremental manual | Alertas automáticas (MRR) | El cálculo de delta es el mismo (§10) |
| CSVs masticados | Botón *"Corregir este 20%"* | Punto de extensión (fuera de diagnóstico) |

---

## 15. Alcance MVP: Retail Moderno

**Nicho elegido:** **Retail Moderno** (cadenas de comida, cafeterías, minimercados, tiendas) — el "océano azul". Alta transaccionalidad, muchos humanos digitando, sistemas fragmentados (POS + delivery + WhatsApp + fidelización). Ven el ROI en la misma semana. *E-commerce es la expansión natural posterior.*

**Caso guía ilustrativo — "Sanduchería" (sándwich cubano):** varios puntos físicos + venta por **Rappi** + pedidos por **WhatsApp**. Entrega **3 archivos CSV** que sus sistemas ya generan:

| Archivo | Origen | Columnas clave |
|---|---|---|
| **1 · Ventas POS** (patrón de oro) | POS (Alegra/Square/Siigo…) | `id_factura`, `fecha`, `punto_venta`, `canal`, `producto/sku`, `cantidad`, `precio_unitario`, `total`, `cajero` |
| **2 · Liquidación Rappi** | Portal Rappi / integrador (Hubster/Deliverect) | `id_orden_rappi`, `estado`, `valor_productos`, `comisión`, `ajustes`, `monto_neto` |
| **3 · Clientes / Fidelización** | CRM / programa de puntos | `id_cliente`, `nombre`, `teléfono`, `email`, `fecha_registro` |

**Dos módulos independientes en el MVP** (se mantienen separados por simplicidad y para cobrar por dos áreas):
- **Módulo A — Auditoría Financiera y Operativa:** cruza **POS × Rappi** (conciliación: pedidos cancelados/penalizados, descuadres). No requiere datos de clientes.
- **Módulo B — Higiene de Base de Datos:** analiza **Clientes** de forma aislada (correos falsos `no@tiene.com`, teléfonos rotos, nulos, duplicados). Valor de marketing/recompra.

> El motor se mantiene **agnóstico de sector**: la sanduchería es un caso; el conocimiento del sector vive en el YAML 4 (Maestro de Sectores). El **primer feature (Tracer Bullet)** aterrizará un slice vertical mínimo de este caso.
>
> **Fase 2 (futuro):** si el POS amarra cada venta a un `id_cliente`, se habilita el **cruce Clientes × Ventas** (cliente fantasma, unificación de duplicados). Fuera del MVP.

---

## 16. Puntos Abiertos y Futuro

**Premortem — las 4 causas de muerte a vacunar** (diseñar con anticuerpos desde hoy):

1. **Paradoja del presupuesto** — el cliente sabe que pierde dinero pero no tiene con qué arreglarlo. *Vacuna:* entregar los CSVs masticados (la "receta") y, a futuro, el botón de corrección; atacar PYMES ágiles.
2. **Pesadilla del NDA/seguridad** — Legal/Ciberseguridad bloquea conectar la BD. *Vacuna:* la arquitectura **Datos en Bóveda** (§7) es el argumento de privacidad; en Fase 1 ni siquiera hace falta conectar nada.
3. **Alucinación de costos** — el CFO desacredita las cifras. *Vacuna:* **cálculo auditable** (§2.8): el cliente ve la fórmula y ajusta las variables; blindaje legal (cláusula de no-responsabilidad operativa: las pérdidas son *estimaciones* basadas en variables declaradas por el cliente).
4. **Monstruo de la personalización (YAML infinito)** — cada cliente opera distinto y el config se vuelve inmanejable. *Vacuna:* el Maestro de Sectores (YAML 4) como plantilla reutilizable; disciplina para no personalizar sin límite.

**Otros puntos abiertos:**
- **Esquemas formales de los 4 YAMLs y de los contratos** (JSON Schema / Pydantic) — se definen al construir cada módulo.
- **Modelo de cobro** (documento fuente): suscripción fija quincenal/mensual ($150–$300 USD) vs *success fee* (20% de lo recuperado) para los primeros clientes. No impacta el motor.
- **Reporte ejecutivo:** formato del entregable (PDF/plataforma) — se define en el feature de `report`.
- **Persistencia:** carpeta-por-cliente ahora; migración a BD/object storage detrás de `ClientContext`.
- **Conectores API** (Fase 3): Shopify, POS, CRM, WooCommerce — extensión futura, no MVP.
```
