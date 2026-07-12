# Metodología de Desarrollo de ZeroLeak

Esta es la **metodología de ingeniería para construir** ZeroLeak: cómo se desarrolla, de forma
disciplinada, trazable y reanudable, el código determinista que audita la calidad de los datos de un
cliente y **traduce los errores a pérdidas financieras** (dinero perdido, priorizado con Pareto).

> **Qué es ZeroLeak.** Un servicio/SaaS B2B de **diagnóstico** de calidad de datos (no de limpieza). Su
> núcleo es un motor Python determinista (`validador.py`, con Pandas/NumPy/Pydantic) que procesa
> archivos CSV/Excel del cliente y produce un reporte financiero. Evolución del negocio:
> **Servicio → SaaSw → SaaS puro**. Nicho MVP: **Retail Moderno**.

> **Alcance de este documento.** Cubre **desarrollo**, no el negocio. El **runtime** de ZeroLeak es
> **código Python determinista**; el LLM **no procesa datos reales del cliente** (ver §6, *Datos en
> Bóveda*). Los únicos agentes de IA del proyecto son los **agentes de desarrollo** que construyen ese
> código; en runtime **no hay agentes orquestando**.

---

## 0. Propósito y Mapa de Fuentes

### 0.1 Propósito
Reducir el espacio de decisiones probabilísticas durante la **construcción** del motor, encuadrando el
trabajo de los agentes de desarrollo mediante **prototipado visual (notebook), especificaciones, tests y
verificación independiente**, con el **humano como GateKeeper**. Se construye un core determinista y
reproducible que primero se **explora en un notebook** y luego se **consolida en `.py`, feature a feature**.

### 0.2 Mapa de fuentes de verdad
Este documento no repite lo que ya tiene dueño canónico:

| Tema | Fuente canónica |
|---|---|
| Principios (P1–P8), Estándares (E1–E12), Normas de Comportamiento (NC-1…NC-6) | **`905_guideline/principles.md`** |
| Plantillas de artefactos de feature (feature_contract, definition, notebook, spec, plan, verification, state) | **`600_template/`** |
| Estado y avance del proyecto entre sesiones | **`900_persistence/`** |
| Estrategia de ramas / PR y protocolos de sesión | **`CLAUDE.md`** + agentes `session-starter` / `session-closer` |
| **Metodología de construcción** (este archivo): flujo notebook→SDD+TDD, gates, persistencia, evaluación, evolución, seguridad | **este documento** |

> **Comportamiento vinculante.** Todo agente de desarrollo debe cumplir los P/E/NC de `principles.md`
> como restricciones inmutables.

---

## 1. Flujo de Construcción (Notebook → SDD+TDD)

Ninguna pieza de trabajo se produce sin una definición previa, un prototipo visual aprobado y un
mecanismo de validación. **Modelo Opción A: una feature = una construcción completa (sin bandas).** El
ciclo de vida de una feature son **13 pasos**:

| # | Paso | Responsable | Artefacto / Acción |
|---|---|---|---|
| 1 | Definir la feature | Humano + sesión principal | Acuerdo de intención + `git checkout -b feature/<n>` |
| 2 | Escribir el contrato | Sesión principal | `feature_contract.md` (estrella polar / "terminado") |
| 3 | Definir la feature | `feature_definer` | `definition.md` (historias `HU-xx`) |
| 4 | Prototipar en notebook | `notebook_writer` | `<feature>.ipynb` (spike, **datos sintéticos**) |
| 5 | **🚦 Gate humano** | Humano | Revisa y aprueba los resultados del notebook |
| 6 | Especificar | `spec_writer` | `spec.md` (criterios `CA-xx` verificables) |
| 7 | **🚦 Gate humano** | Humano | Aprueba / rechaza la spec |
| 8 | Planear | `plan_builder` | `plan.md` (tareas `TSK-xx` + casos de test) |
| 9 | **🚦 Gate humano** | Humano | Aprueba / rechaza el plan |
| 10 | Construir (bucle TDD) | `tdd_tester` → `tdd_coder` → `tdd_refactor` | RED → GREEN → REFACTOR |
| 11 | Probar integración | `integration_tester` (contexto fresco) | Suite end-to-end con fixtures |
| 12 | Verificar | `spec_verifier` (contexto fresco) | `verification.md` (veredicto CONFORME/NO CONFORME) |
| 13 | Integrar | Sesión principal abre PR → **🚦 Gate humano** | El humano prueba (`human_test`) y **mergea** a `main` |

**Correspondencia SPEC/RED/GREEN/REFACTOR/VERIFY:**
`spec_writer`→SPEC (el *Qué*) · `tdd_tester`→RED (criterio de éxito, test que falla **antes** del código) ·
`tdd_coder`→GREEN (código mínimo) · `tdd_refactor`→REFACTOR (limpieza sin cambiar comportamiento) ·
`integration_tester` + `spec_verifier`→VERIFY (auditoría en contexto fresco).

**Invariantes:**
- **Independencia:** quien codifica ≠ quien prueba ≠ quien verifica (contextos frescos; P1/P3).
- **Test-first:** el test que falla se escribe **antes** del código (paso 10).
- **Notebook antes de spec:** el spike visual (paso 4) informa la spec; **no la reemplaza** (paso 6 la reescribe con rigor).
- **Gate humano** en notebook, spec, plan y cierre (P5). Ningún agente cruza un gate por su cuenta: lo hace la sesión principal tras la aprobación humana.

**El notebook no se "gradúa" tal cual.** Al pasar a `.py` no se copia-pega: la spec y el bucle TDD
reescriben la lógica. El notebook queda como **artefacto de referencia/demo** ligado a `definition.md`.

**Trazabilidad end-to-end.** La columna vertebral que une todos los artefactos:
```
HU-xx (definition) → CA-xx (spec) → TSK-xx (plan) → matriz de trazabilidad (verification)
```
Toda `HU-xx` debe estar cubierta por ≥1 `CA-xx`; todo `CA-xx` por ≥1 `TSK-xx`; toda `CA-xx` con evidencia
en `verification.md`. Si algo no traza, el artefacto está incompleto.

**Ubicación de artefactos.** Por feature en
`610_features/<feature>/{feature_contract.md, definition.md, <feature>.ipynb, spec.md, plan.md, verification.md, state.json}`;
el código en `app/src/zeroleak/…` y los tests en `app/tests/…`. Las plantillas viven en `600_template/`.

---

## 2. Gates de Aprobación
- **Automáticos:** criterios técnicos medibles (pasar `pytest`, cobertura de los `CA-xx`).
- **Humanos:** el humano aprueba intención/alcance. Hay gate humano obligatorio **tras el notebook**
  (paso 5), **tras `spec_writer`** (paso 7), **tras `plan_builder`** (paso 9) y en el cierre
  (`human_test` + `merge_to_main`, paso 13).

---

## 3. Persistencia y Trazabilidad (desarrollo)
La fuente de verdad reside en el **filesystem**, no en la memoria de los agentes. Esto permite reanudar
el trabajo entre sesiones y ante fallos (E1, E5).

### 3.1 Capas de persistencia
| Capa | Dónde | Qué guarda |
|---|---|---|
| Proyecto / sesión | `900_persistence/` | `progress` · `tasks` · `lessons` · `decisions` · `assumptions` · `constraints` |
| Por feature (SDD/TDD) | `610_features/<feature>/state.json` | máquina de estado de la construcción (13 etapas) |

### 3.2 Single Writer Rule
Cada archivo de estado tiene **un único responsable de escritura**, para evitar condiciones de carrera.
En `plan.md`, el **responsable de cada tarea es el único que actualiza su estado**
(`no_implementada` | `implementada` | `cancelada_suspendida`).

### 3.3 Git y reanudación
- **Commit por etapa** con prefijo convencional; el **push** se hace en el cierre de sesión (`session-closer`).
- Para retomar una feature interrumpida, la sesión principal lee su `state.json` (`status`,
  `current_stage`) y reinvoca al agente correspondiente con contexto fresco.

---

## 4. Evaluación
La independencia del evaluador (P3: quien genera no evalúa) se cumple: `integration_tester` y
`spec_verifier` corren en **contextos frescos**, separados de quien codifica.

**La evaluación se dimensiona a la naturaleza de la salida:**

| Tipo de salida | Naturaleza | Evaluación |
|---|---|---|
| **Código determinista** (todo el motor `validador.py`) | Objetiva | **Tests** (RED) + **veredicto binario** de `spec_verifier` (CONFORME/NO CONFORME) + matriz de trazabilidad. |
| **Reglas financieras** (traductor a dólares) | Cuantitativa | Aserción tipo "3 duplicados × $1.20 → pérdida = $3.60" (encaja como test) + **evaluación temprana** con ~20 casos sintéticos representativos (E9). |

> **Principio rector:** el core de ZeroLeak es determinista, por lo que **los tests bastan**; no se aplica
> rúbrica calibrada de LLM porque el LLM **no evalúa datos reales** en runtime. Si en fases futuras se
> añaden salidas de LLM (p. ej. redacción de conclusiones en el SaaSw), se introducirá rúbrica 0.0–1.0
> calibrada (E3) *solo* donde el LLM aporte.

**Evaluación Temprana (E9).** Al completar el primer componente funcional, evaluar una muestra de ~20
casos sintéticos representativos; si la calidad es baja, ajustar la spec **antes** de continuar.

---

## 5. Evolución del Harness (E4: Mínima Complejidad)
El harness de desarrollo parte del mínimo viable y evoluciona:
- Se construye con el **menor número de componentes** que satisfagan el trabajo (E4, NC-2).
- **El modelo sin bandas (Opción A) es la decisión por defecto.** El modelo de *bandas* (endurecer una
  feature en pasadas `tracer_bullet → stab_n`) queda **disponible pero diferido**: se adopta solo si una
  feature concreta resulta demasiado grande para un ciclo. El primer feature del proyecto se construye
  deliberadamente como un **Tracer Bullet a nivel de proyecto** (slice fino end-to-end, NC-4).
- Cada componente codifica una **suposición explícita** sobre una limitación del modelo; no se agrega sin
  evidencia de que su ausencia degrada la calidad.
- **Prueba de remoción periódica:** quitar un componente a la vez y medir el impacto; si la calidad no
  cae, se elimina y se registra la lección en `lessons.md`.

---

## 6. Seguridad: "Datos en Bóveda" (restricción inviolable)
ZeroLeak procesa datos sensibles de clientes (ventas, PII). La protección **no depende de encriptar
archivos**, sino de una **separación absoluta** entre la IA que diseña el código y el entorno local que
procesa la información:

- **El LLM solo diseña la maquinaria.** Los agentes de desarrollo ven estructuras, YAMLs y **datos
  sintéticos** ("matrices de mentiras", 3–5 filas falsas). **Ningún modelo de IA toca, lee o procesa los
  CSV/Excel reales del cliente.**
- **El motor corre 100% local.** La lectura de filas reales, la detección y el cálculo de pérdidas
  ocurren en la máquina local; ningún dato real sale hacia servidores de IA.
- **Notebooks con datos sintéticos.** El `<feature>.ipynb` que escribe `notebook_writer` usa
  exclusivamente datos sintéticos (paso 4).
- **`data_real/` aislada.** La carpeta con datos reales se excluye del indexador (`.gitignore` / exclusión
  de contexto), prohibiendo físicamente a los agentes leerla.
- **Drop & Detach (binarización).** Para auditar campos sensibles, el motor crea columnas bandera (1/0),
  elimina las columnas de texto original (email, nombre, teléfono) y calcula sobre esos unos y ceros,
  eliminando la PII de raíz.

> Esta restricción es vinculante y se detalla en `constraints.md`. Todo agente y todo artefacto la
> respetan; su cumplimiento se verifica en `verification.md`.

---

## Apéndice: Estándares de Ingeniería
- **Convención de commits:** `tipo(<feature>): descripción` (`feat`/`spec`/`plan`/`test`/`refactor`/`verify`/`chore`/`docs`).
- **Estrategia de ramas (detalle en `CLAUDE.md`):** toda feature nueva se construye en su rama
  `feature/<nombre>`. La cadena SDD/TDD corre sobre esa rama y el `session-closer` empuja a la rama actual.
  La integración a `main` es **solo vía Pull Request**: cuando `spec_verifier` emite CONFORME, la sesión
  principal abre el PR (`gh pr create`) y el `state.json` avanza a las dos etapas terminales de gate
  humano `human_test` (el humano prueba la feature) y `merge_to_main` (el humano mergea el PR).
  **La automatización llega hasta el PR; el harness nunca mergea a `main` por su cuenta.**
- **Selección de modelos:** el modelo adecuado según la tarea — **Opus** para definición/spec/plan/verificación
  (`spec_writer`, `plan_builder`, `spec_verifier`) y para `notebook_writer` (excepción explícita),
  **Sonnet** para ejecución (`tdd_coder`, `tdd_refactor`, `integration_tester`, `tdd_tester`) y para
  `feature_definer` (excepción explícita), **Haiku** para tareas ligeras (p. ej. `session-starter`).
  Ver D-05 revisado para las excepciones.
