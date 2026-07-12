# Lessons — Lecciones Aprendidas

Registro de las lecciones aprendidas durante la ejecución del proyecto.

---

## Índice
<!-- Mantener actualizado. Un enlace por lección registrada. -->
- [L-01] Los subagentes `.claude/agents/*.md` requieren reiniciar Claude Code para ser invocables.
- [L-02] Extracción de `.docx` sin `python-docx` y encoding en consola Windows.
- [L-03] Carpetas de andamiaje pueden arrastrar artefactos de un proyecto hermano (FODA).

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
