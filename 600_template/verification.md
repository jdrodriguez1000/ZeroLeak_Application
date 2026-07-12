# Verification — <feature>

> Artefacto del paso 12 (`spec_verifier`, contexto fresco). Verifica que lo construido **cumple la spec aprobada** y que las pruebas están en verde. Emite el veredicto que cierra la construcción o la marca como no conforme.
> Se apoya en el resultado del paso 11 (`integration_tester`).

## Veredicto
**<CONFORME | NO CONFORME>**

## Matriz de Trazabilidad
| Criterio de aceptación (spec) | Evidencia (test / comportamiento) | Estado |
|---|---|---|
| <CA-01> | <test_x / comportamiento> | cubierto / parcial / no cubierto |

## Resultado de la Suite
- <Conteo de tests, verde/rojo. Incluye el resultado de `integration_tester`.>

## Cumplimiento de Alcance y Restricciones
- **Alcance (`definition.md` / `feature_contract.md`):** <in scope hecho, out of scope respetado.>
- **Restricciones del proyecto (`constraints.md`):** <p. ej. Datos en Bóveda / datos sintéticos, cambios quirúrgicos NC-3, etc.>

## Hallazgos / Huecos
- <Si NO CONFORME: qué falta y **etapa de retorno recomendada**: `spec_writer` (spec mal), `plan_builder` (plan mal), bucle TDD (`tdd_tester`/`tdd_coder`) o `integration_tester`.>
