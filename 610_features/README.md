# 610_features — Features construidos (SDD+TDD)

Cada feature de ZeroLeak vive en su propia carpeta `610_features/<feature>/` y
reúne todos sus artefactos del flujo de 13 pasos (Notebook → SDD+TDD,
**Opción A: sin bandas** — D-01). Las **plantillas** de estos artefactos viven
en [`../600_template/`](../600_template/).

## Estructura de un feature

```
610_features/<feature>/
├── feature_contract.md   # contrato del feature (lo escribe la sesión principal)
├── definition.md         # HU / criterios de aceptación (CA) / tareas (TSK)
├── <feature>.ipynb       # notebook-first: spike con datos sintéticos (gate humano)
├── spec.md               # especificación consolidada
├── plan.md               # plan de construcción (Single Writer Rule)
├── verification.md       # evidencia de cada CA + cumplimiento de C-01
└── state.json            # máquina de estado de la construcción (13 etapas)
```

El **código** correspondiente vive en `app/src/zeroleak/…` y los **tests** en `app/tests/…`.

## Trazabilidad

`HU-xx → CA-xx → TSK-xx`, con evidencia de cada `CA-xx` en `verification.md`.
Si algo no traza, el artefacto está incompleto (ver `905_guideline/methodology.md`).

## Índice de features

<!-- Un enlace por feature construido o en construcción. -->
_(aún no hay features; el primero será el Tracer Bullet, T-12.)_
