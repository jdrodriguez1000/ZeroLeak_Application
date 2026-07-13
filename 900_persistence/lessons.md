# Lessons — Lecciones Aprendidas

Registro de las lecciones aprendidas durante la ejecución del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por lección registrada. -->
- [L-01] Los subagentes `.claude/agents/*.md` requieren reiniciar Claude Code para ser invocables.
- [L-02] Extracción de `.docx` sin `python-docx` y encoding en consola Windows.
- [L-03] Carpetas de andamiaje pueden arrastrar artefactos de un proyecto hermano (FODA).
- [L-04] Colores de agentes repetidos entre subagentes (decisión consciente, pendiente de revisión).
- [L-05] Reemplazos masivos con `sed` pueden generar prefijos duplicados si el patrón ya existe parcialmente.
- [L-06] Comparar `state.json` con el proyecto hermano FODA ayuda a detectar diferencias de esquema (campo `band`) antes de instanciar el primer feature.
- [L-07] Editar notebooks `.ipynb` con contenido no-ASCII vía heredoc de bash en Windows/git-bash corrompe caracteres; usar scripts Python con escapes `\uXXXX` y verificar por codepoint + ejecución.
- [L-08] El gate humano de la spec (paso 7) requiere aprobación explícita; no debe darse por superado de forma implícita.
- [L-09] `pyproject.toml` exige Python 3.13+, pero el `python` del PATH del usuario es 3.12; usar `py -3.13` / `.venv` dedicado.
- [L-10] En el bucle TDD, un caso puede pasar en verde de inmediato si su código ya quedó cubierto por un caso anterior; la verificación honesta consiste en provocar temporalmente el defecto y confirmar el fallo, revirtiendo sin dejar rastro.

---

## [2026-07-12] L-01 — Registro de subagentes personalizados
- **Situación:** Al intentar invocar `session-closer` con la herramienta Agent, el harness respondió que el tipo de agente no existía (solo listaba los integrados).
- **Lección:** Crear el `.md` en `.claude/agents/` no basta para que el agente sea spawneable en la sesión en curso; el harness parece cargar los tipos al inicio.
- **Acción futura:** Tras crear/editar agentes, **reiniciar Claude Code** y verificar que aparezcan como tipos invocables. Mientras tanto, la sesión principal puede ejecutar el protocolo manualmente.

## [2026-07-12] L-02 — Leer archivos `.docx` en este entorno
- **Situación:** No hay `pandoc` ni `python-docx`; además la consola Windows (cp1252) falló al imprimir emojis del documento.
- **Lección:** Un `.docx` es un ZIP con XML; se extrae con `zipfile` + `xml.etree` de la stdlib. Para evitar `UnicodeEncodeError`, **escribir la salida a un archivo UTF-8** en vez de imprimir a consola.
- **Acción futura:** Reutilizar el script `extract_docx.py` del scratchpad para futuros `.docx`.

## [2026-07-12] L-03 — Artefactos ajenos en carpetas de andamiaje
- **Situación:** `700_architecture/system_design.md` y `sdd_tdd_workflow.md` resultaron pertenecer al proyecto hermano **FODA** (Foda_Application), no a ZeroLeak; estaban sin trackear en git, probablemente copiados al iniciar el andamiaje del repo.
- **Lección:** Antes de dar por válido el contenido de una carpeta recién creada por andamiaje, **verificar que el contenido corresponda al proyecto actual** (nombres, dominio, referencias cruzadas), especialmente si existe un proyecto hermano con estructura similar.
- **Acción futura:** Al iniciar/retomar sesión, revisar carpetas de diseño (`700_architecture/`, etc.) en busca de referencias a otros proyectos antes de asumir que su contenido es correcto.

## [2026-07-12] L-04 — Colores repetidos entre subagentes
- **Situación:** Al crear los 9 agentes de desarrollo (T-10), algunos colores quedaron repetidos: `green` en `feature-definer` y `tdd-coder`; `cyan` en `notebook-writer` e `integration-tester`; `blue` compartido entre `tdd-refactor` y `session-starter`.
- **Lección:** Fue una decisión consciente del humano al momento de crear cada agente (no un error), pero puede dificultar distinguir agentes por color en la interfaz si se ejecutan en paralelo.
- **Acción futura:** Evaluar si conviene unificar/diferenciar los colores en una sesión futura, sin que sea bloqueante para el avance del proyecto.

## [2026-07-12] L-05 — `sed` puede generar prefijos duplicados en reemplazos masivos
- **Situación:** Durante el refactor a `app/` (T-20), un reemplazo masivo con `sed` sobre referencias a `tests/` produjo un bug de doble prefijo `app/app/tests/` en 10 lugares (agentes tdd-*, integration-tester, plan-builder, template `plan.md`, `methodology.md`, `610_features/README.md`), porque el patrón `tests/` ya aparecía parcialmente prefijado por `app/` en algunas líneas procesadas antes.
- **Lección:** Al hacer reemplazos masivos de rutas con `sed` (o similares) en múltiples archivos, verificar con un `grep` posterior que no queden patrones duplicados/anidados, especialmente cuando el reemplazo se aplica más de una vez sobre el mismo conjunto de archivos o cuando el patrón de búsqueda es un substring de la cadena de reemplazo.
- **Acción futura:** Preferir reemplazos con anclas más específicas (p. ej. inicio de línea o comillas) y siempre correr un `grep` de verificación tras un refactor de rutas masivo antes de dar por cerrada la tarea.

## [2026-07-12] L-06 — Comparar `state.json` con el proyecto hermano FODA antes de instanciar el primero
- **Situación:** El humano preguntó por el formato correcto de `state.json` para el primer feature (`client_scaffold`). Se comparó el `state.json` de un feature ya construido en el proyecto hermano FODA (que incluye campo `band` y se organiza por bandas) contra la plantilla vigente `600_template/state.json`.
- **Lección:** El proyecto hermano FODA es una referencia útil de patrón, pero **no debe copiarse literalmente**: ZeroLeak adoptó D-01 (Opción A, sin bandas), por lo que su `state.json` **no lleva campo `band`** y en cambio incluye etapas propias del flujo de 13 pasos ausentes en FODA (`feature_contract` con owner `main_session`, `notebook_writer`, `human_test`, `merge_to_main`), conservando la granularidad de evidencia TDD (`red_evidence`, `green_evidence`, `refactor_note`, `cases[]`).
- **Acción futura:** Al instanciar el `state.json` de cada nuevo feature, usar siempre `600_template/state.json` como fuente de verdad (no el de FODA), y verificar que las decisiones D-01…D-05 sigan reflejadas correctamente.

## [2026-07-12] L-07 — Editar notebooks `.ipynb` con contenido no-ASCII en Windows/git-bash
- **Situación:** Al ajustar `client_scaffold.ipynb` para usar la regla de nombre aprobada (acentos/ñ válidos; ejemplos inválidos con cirílico y emoji) y para trabajar con `COMPANY_DEMO`, un primer intento de edición vía heredoc de bash corrompió los caracteres no-ASCII (acentos, ñ, cirílico) al escribir el JSON del notebook.
- **Lección:** El heredoc de bash en el entorno Windows/git-bash de este proyecto no preserva de forma confiable caracteres no-ASCII al escribir archivos. La inspección visual del terminal tampoco es suficiente para detectar la corrupción.
- **Acción futura:** Para editar notebooks (u otros archivos) con contenido no-ASCII, usar un script Python en archivo (no heredoc) con escapes explícitos `\uXXXX`, y verificar el resultado por **codepoint** (no visualmente) y por **ejecución real** (p. ej. `nbconvert --execute`), confirmando exit code 0 y 0 celdas con error. Además, las celdas markdown de un notebook no deben llevar `outputs` ni `execution_count`, o el JSON del notebook queda inválido.

## [2026-07-12] L-08 — El gate humano de la spec (paso 7) exige aprobación explícita
- **Situación:** Durante la construcción de `client_scaffold` (T-21), al llegar al paso 7 (gate humano sobre `spec.md`) el flujo avanzó dando por aprobada la spec de forma implícita, sin que el humano la aprobara explícitamente. El humano señaló el error y se corrigió, solicitando la aprobación explícita, que luego otorgó.
- **Lección:** Los gates humanos del flujo de 13 pasos (paso 5 sobre el notebook, paso 7 sobre la spec, paso 9 sobre el plan, `human_test`) son puntos de control obligatorios que requieren una confirmación explícita del humano; no deben asumirse superados por defecto ni inferirse de la ausencia de objeciones.
- **Acción futura:** En cada gate humano del flujo, solicitar y esperar una aprobación explícita antes de marcar la etapa correspondiente como `done` en `state.json` o de avanzar al siguiente paso.

## [2026-07-13] L-09 — Desajuste de versión de Python entre `pyproject.toml` y el PATH del usuario
- **Situación:** Al ejecutar TSK-24 (crear el tenant real `COMPANY_DEMO` instalando el paquete), `pip install -e .` falló porque `pyproject.toml` (en la raíz del repo) declara `requires-python = ">=3.13"`, mientras que el `python` resuelto por el PATH del usuario es la versión 3.12.10.
- **Lección:** No asumir que el `python`/`pip` del PATH satisface el `requires-python` del proyecto; verificar la versión antes de instalar. En Windows, el selector `py -3.13` permite invocar una versión específica instalada sin depender del PATH.
- **Acción futura:** Usar `py -3.13 -m venv .venv` en la raíz del repo y trabajar dentro de ese entorno (o invocar siempre `py -3.13`) para cualquier tarea que instale o ejecute el paquete `zeroleak`. `.venv/` ya está cubierto por `.gitignore`.

## [2026-07-13] L-10 — Verificación honesta cuando un caso TDD pasa en verde de inmediato
- **Situación:** En el bucle TDD de `client_scaffold`, varios casos (2-7, 11-13) tenían su código de producción ya cubierto desde el Caso 2 (que implementó la estructura completa del tenant), por lo que sus tests pasaban en verde apenas se escribían, sin una fase ROJA clásica.
- **Lección:** Que un test pase de inmediato no basta como evidencia de que realmente ejercita el comportamiento esperado. En esos casos, `tdd_tester` provocó temporalmente el defecto correspondiente en el código de producción, confirmó que el test fallaba por la razón correcta, y revirtió el cambio dejando el diff limpio antes de continuar — una "verificación razonada honesta" que sustituye a la fase ROJA cuando esta no puede ocurrir de forma natural.
- **Acción futura:** Aplicar esta técnica (romper temporalmente, confirmar el fallo, revertir sin rastro) cada vez que un test nuevo pase en verde sin haber tenido fase ROJA, antes de darlo por válido.
