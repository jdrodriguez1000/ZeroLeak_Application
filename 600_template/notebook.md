# Notebook (spike) — <feature>

> Guía del artefacto del paso 4 (`notebook_writer`). El entregable real es un archivo **`<feature>.ipynb`**;
> este `.md` documenta **qué debe contener y bajo qué reglas**. El notebook es un **spike de exploración**
> que prototipa y **visualiza** la definición (`definition.md`) antes de escribir la spec.

## 🔒 Regla inviolable: Datos en Bóveda
- El notebook usa **exclusivamente datos sintéticos** ("matrices de mentiras", 3–5 filas con nombres falsos
  tipo `test1@correo.com`, `Usuario 1`). **Ningún dato real del cliente entra a un notebook que el LLM vea.**
- Los datos reales viven en `data_real/` (aislada del indexador). Ver `constraints.md`.

## Propósito del spike
- Validar el enfoque técnico de cada historia (`HU-xx`) end-to-end.
- Producir resultados **visibles** que el humano pueda revisar y aprobar (paso 5, gate humano).
- Informar la `spec.md` (no reemplazarla): lo que aquí funciona se traduce luego a criterios `CA-xx`.

## Estructura sugerida de celdas
| Celda | Contenido | Traza → HU |
|---|---|---|
| 1 | Cargar datos sintéticos de prueba | — |
| 2 | <prototipo de la detección/lógica principal> + visualización del resultado | HU-01 |
| 3 | <siguiente pieza de lógica> + visualización | HU-02 |
| n | <cálculo/salida final> + visualización | HU-0x |

## Lifecycle (Opción A)
- El notebook es **artefacto de referencia/demo ligado a `definition.md`**.
- Al pasar a `src/`, **no se copia-pega**: la spec y el bucle TDD reescriben la lógica. La fuente de verdad
  del producto pasa a ser `.py` + tests; el notebook queda como documentación del spike.

## Resultado esperado del gate humano (paso 5)
- [ ] El enfoque de cada `HU-xx` quedó demostrado con datos sintéticos.
- [ ] El humano **aprueba** continuar hacia la especificación.
