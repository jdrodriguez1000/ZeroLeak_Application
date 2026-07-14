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
- [L-11] Separar "ingesta" (copia + hash) de "parseo" (estructura/delimitador) evita acoplar comandos tempranos del pipeline a un formato específico.
- [L-12] Los subagentes `tdd_*` no tienen kernel de Jupyter disponible; la sesión principal debe instalar `nbconvert`/`ipykernel` en el `.venv` del proyecto para ejecutar el notebook.
- [L-13] Un test nuevo puede pasar en verde de inmediato porque el CA que cubre ya quedó satisfecho por el refactor de un caso previo; tratarlo como test de caracterización/regresión en vez de forzar un RED artificial.
- [L-14] El patrón de caracterización (L-13) se repite con frecuencia cuando el diseño temprano ya es agnóstico/general (p. ej. helpers extraídos en refactors previos); reconocerlo rápido evita RED artificiales innecesarios en varios casos seguidos del mismo bucle.

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

## [2026-07-13] L-11 — Separar ingesta (copia + hash) de parseo (estructura/delimitador)
- **Situación:** Al diseñar el alcance del segundo Tracer Bullet `ingest`, surgió la tentación de que el comando validara "es un CSV legible" o infiriera el delimitador del archivo.
- **Lección:** Acoplar la ingesta temprana a un formato específico (validar que sea "un CSV legible") compromete la agnosticidad del pipeline frente a variaciones de delimitador (`,`/`;`/`|`) o estructura, que son responsabilidad de una etapa posterior (el Contrato de Datos / YAML 1). El principio "archivador notarial" — copiar bytes fielmente y hashear, sin parsear — mantiene `ingest` simple, robusto y reutilizable para cualquier extensión de la allow-list.
- **Acción futura:** Al diseñar comandos tempranos del pipeline (ingesta, registro, staging), limitar su validación a lo estrictamente agnóstico de formato (existencia, no vacío, extensión permitida) y diferir toda validación de estructura/contenido a la etapa de contrato de datos.

## [2026-07-13] L-12 — Los subagentes `tdd_*`/`notebook_writer` no tienen kernel de Jupyter para ejecutar notebooks
- **Situación:** Al construir `ingest.ipynb` (paso 4 del Tracer Bullet `ingest`), el agente `notebook_writer` produjo el notebook pero no pudo ejecutarlo para generar evidencia real (sin kernel/entorno disponible en su contexto de ejecución).
- **Lección:** Los subagentes que trabajan con notebooks pueden carecer del entorno Python necesario (kernel, `nbconvert`, `ipykernel`) para ejecutarlos, aunque sí puedan escribir el JSON del `.ipynb`. La sesión principal debe asumir la ejecución cuando esto ocurra.
- **Acción futura:** Si un agente reporta no poder ejecutar un notebook, la sesión principal debe instalar `nbconvert`+`ipykernel` en el `.venv` del proyecto (ya con Python 3.13, ver L-09) y ejecutar el notebook in-place (`jupyter nbconvert --to notebook --execute --inplace`), verificando exit code 0 y ausencia de celdas con error antes de dar el paso 4 por completo.

## [2026-07-13] L-13 — Test de caracterización cuando un CA ya quedó satisfecho por un caso anterior
- **Situación:** En el bucle TDD de `ingest`, el Caso 3 (CA-02, forma exacta del manifest) pasó en verde de inmediato al escribirse, sin ningún cambio de código: el helper `_build_manifest_entry` (extraído durante el refactor del Caso 2) ya emitía exactamente los 4 campos exigidos.
- **Lección:** A diferencia de L-10 (donde se provoca temporalmente el defecto para confirmar honestamente el fallo), aquí no aplicaba esa técnica porque no había ningún comportamiento "por romper": el CA ya estaba cubierto como efecto colateral genuino de una decisión de diseño anterior (el helper). En ese caso, forzar un RED artificial sería teatro, no verificación. La resolución correcta es reportar el hallazgo a la sesión principal, decidir explícitamente tratar el test como **caracterización/regresión** (blindaje contra regresiones futuras, no evidencia de un ciclo TDD clásico) y dejar constancia de esa decisión en `plan.md`/`state.json` (marcando la tarea de test como `implementada` con la nota correspondiente, y la tarea de código como `cancelada_suspendida` si no hay nada nuevo que escribir).
- **Acción futura:** Antes de forzar un RED artificial en un caso que pasa en verde de inmediato, evaluar si existe un comportamiento real que romper (L-10) o si el CA ya fue satisfecho genuinamente por trabajo previo (L-13); en el segundo caso, documentar la decisión explícitamente en vez de simular un ciclo que no ocurrió.

## [2026-07-14] L-14 — El patrón de caracterización se repite cuando el diseño temprano ya es general
- **Situación:** Al cerrar el bucle TDD de `ingest` (bloques 3 y 4), el patrón de caracterización descrito en L-13 volvió a aparecer tres veces más: Caso 8 (CA-04, argumentos mezclados archivo+carpeta) quedó cubierto por el helper `_expand_paths` extraído en el Caso 7; Caso 9 (CA-10, delimitadores `,`/`;`/`|` sin parseo) quedó cubierto por el diseño byte-a-byte adoptado desde el Caso 2 (`_hash_file`/`shutil.copyfile` nunca interpretan el contenido); Caso 11 (CA-11, frontera PII del `.gitignore`) quedó cubierto por la regla `clients/*/data/` ya vigente desde `client_scaffold` (C-01), sin ningún cambio de `.gitignore` ni de código de producción.
- **Lección:** Cuando el diseño de un caso temprano se hace deliberadamente agnóstico/general (p. ej. operar siempre sobre bytes crudos, o extraer un helper que ya cubre el caso general), varios casos posteriores del mismo bucle tienden a pasar en verde de inmediato como caracterización, no como una excepción aislada. Detectar esta tendencia temprano (en vez de sorprenderse cada vez) agiliza el bucle: se puede anticipar la pregunta "¿ya está cubierto por diseño?" antes de escribir un RED que se sabe no va a fallar.
- **Acción futura:** Al iniciar cada caso nuevo del bucle TDD, antes de escribir el test, revisar brevemente si el comportamiento exigido por el CA ya es una consecuencia necesaria del diseño agnóstico adoptado en casos anteriores; si es así, ir directo al patrón de caracterización (L-13) en vez de asumir que habrá un RED clásico.
