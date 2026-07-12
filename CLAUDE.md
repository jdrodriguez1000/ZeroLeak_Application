# CLAUDE.md

Guía para trabajar en el proyecto **ZeroLeak**.

## Persistencia del proyecto

El estado y la memoria del proyecto viven en la carpeta `900_persistence/`
(`progress.md`, `tasks.md`, `lessons.md`, `decisions.md`, `assumptions.md`,
`constraints.md`). Consulta estos archivos para conocer el avance, las tareas y
el contexto antes de trabajar.

## Tareas obligatorias

- **Protocolo de inicio de sesión:** cada vez que se invoque al gerente para
  iniciar/retomar la sesión, es obligatorio ejecutar el protocolo de inicio a
  través del subagente `session-starter`. El detalle del protocolo está definido
  en `.claude/agents/session-starter.md`; no se repite aquí.

- **Protocolo de cierre de sesión:** cada vez que se invoque al gerente para
  cerrar/terminar/guardar la sesión, es obligatorio ejecutar el protocolo de
  cierre a través del subagente `session-closer`. El detalle del protocolo está
  definido en `.claude/agents/session-closer.md`; no se repite aquí.

## Control de versiones (Git / GitHub)

- **Repositorio remoto:** `https://github.com/jdrodriguez1000/ZeroLeak_Application.git`
- **Estrategia de ramas:**
  - Por ahora se trabaja directamente sobre la rama **`main`**.
  - Cuando se construya un **feature**, se hace en **su propia rama**; luego se
    lleva a `main` mediante un **Pull Request**.
- **Regla de PR:** el **PR lo escribe el agente**, pero la **aprobación y el merge
  los realiza el humano**. El agente nunca hace merge por su cuenta.
- El versionado (commit + push, y PR cuando aplique) es la **tarea final** del
  protocolo de cierre de sesión (ver `session-closer`).
