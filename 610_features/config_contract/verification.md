# Verification — config_contract

> Artefacto del paso 12 (`spec_verifier`). Auditoría **crítica e independiente**,
> ejecutada en **contexto fresco**. El verificador **no arregla** código ni tests:
> ejecuta la suite real, la lee, y emite un veredicto **binario**
> CONFORME / NO CONFORME respaldado por una **matriz de trazabilidad** `CA-xx →
> test → evidencia`. Base canónica: `spec.md` (CA-01 … CA-15), `definition.md`
> (HU-01 … HU-08), `plan.md`, `constraints.md` C-01, decisiones D-21/D-22/D-23.

## Veredicto global

**CONFORME.**

Los 15 criterios de aceptación (CA-01 … CA-15) están **cubiertos** con evidencia
verificada por el propio verificador: la suite completa corre **verde**, cada
`CA-xx` tiene ≥ 1 test identificable que lo ejercita de forma no tautológica, el
alcance (core-only, sin CLI, sin tocar bronze) se respeta y la restricción
inviolable C-01 (Datos en Bóveda) se cumple por diseño y se blinda con un test de
auditoría. No se detectó ningún hueco bloqueante.

## Resultado real de `pytest` (ejecutado por el verificador)

Comando y salida reales (Python 3.13.7, pytest 9.1.1):

```
$ py -3.13 -m pytest tests -q
........................................................................ [ 81%]
................                                                         [100%]
88 passed in 4.78s
```

Suite específica de la feature (19 ítems, todos PASSED):

```
$ py -3.13 -m pytest tests/test_config_contract.py -v
tests/test_config_contract.py::test_load_contract_valido_n_columnas_orden PASSED
tests/test_config_contract.py::test_load_contract_fidelidad_de_campos PASSED
tests/test_config_contract.py::test_load_contract_seis_tipos_enum PASSED
tests/test_config_contract.py::test_load_contract_campo_tipo_faltante PASSED
tests/test_config_contract.py::test_load_contract_otros_campos_faltantes[nombre-...] PASSED
tests/test_config_contract.py::test_load_contract_otros_campos_faltantes[nulable-...] PASSED
tests/test_config_contract.py::test_load_contract_otros_campos_faltantes[llave-...] PASSED
tests/test_config_contract.py::test_load_contract_lista_vacia PASSED
tests/test_config_contract.py::test_load_contract_tipo_fuera_de_enum PASSED
tests/test_config_contract.py::test_load_contract_duplicados_exactos PASSED
tests/test_config_contract.py::test_load_contract_no_duplicado_por_caso_o_espacio[mayusculas] PASSED
tests/test_config_contract.py::test_load_contract_no_duplicado_por_caso_o_espacio[espacio_final] PASSED
tests/test_config_contract.py::test_load_contract_fail_fast_un_solo_error PASSED
tests/test_config_contract.py::test_load_contract_yaml_roto_parse_error PASSED
tests/test_config_contract.py::test_load_contract_parse_error_mensaje_accionable PASSED
tests/test_config_contract.py::test_load_contract_frontera_no_toca_bronze[valido] PASSED
tests/test_config_contract.py::test_load_contract_frontera_no_toca_bronze[invalido_campo_faltante] PASSED
tests/test_config_contract.py::test_load_contract_core_invocable_sin_cli PASSED
tests/test_config_contract.py::test_load_contract_fixtures_sinteticos_sin_pii PASSED
19 passed
```

`88 passed` = 19 de `config_contract` + 69 preexistentes (`ingest`,
`client_scaffold`, etc.); **cero regresiones**.

### Verificación adicional de mensajes de error (ejecución directa del verificador)

Para no dar por bueno "de palabra" que los mensajes identifican campo/columna/valor
y enumeran los tipos, el verificador invocó `load_contract` directamente sobre
fixtures sintéticos y leyó la excepción real:

```
CA-06: "columna de índice 1, campo 'tipo': valor 'numero_magico' inválido
        (Input should be 'string', 'integer', 'float', 'date', 'datetime'
        or 'boolean')"
CA-04: "falta el campo requerido 'tipo' en la columna de índice 0 (Field required)"
CA-14: "falta el campo requerido 'tipo' en la columna de índice 1 (Field required)"
```

Confirma en la salida real: CA-06 identifica **valor inválido** + **columna** +
**los 6 valores permitidos**; CA-04 identifica **campo** + **columna**; CA-14
emite **un único** mensaje de una sola línea, sin la cadena de agregación
multi-error de Pydantic ("N validation errors for …").

## Matriz de trazabilidad (CA → test → evidencia → veredicto por CA)

| CA | Test que lo cubre | Evidencia verificada | Tipo (RED/caract.) | Veredicto |
|---|---|---|---|---|
| CA-01 | `test_load_contract_valido_n_columnas_orden` | `len(columnas)==N` y lista de `nombre` en el orden declarado. | RED (Caso 1) | **cubierto** |
| CA-02 | `test_load_contract_fidelidad_de_campos` | Los 4 campos por columna 1:1 (`is` para bool, evita coerción falsa). Caracterización blindada con inyección de defecto reversible (state Caso 2). | caracterización | **cubierto** |
| CA-03 | `test_load_contract_seis_tipos_enum` | Acepta los 6 tipos; `tipo.value` coincide; `{col.tipo} == set(TipoDato)` (blinda `datetime`, D-23b). | caracterización | **cubierto** |
| CA-04 | `test_load_contract_campo_tipo_faltante` | `ContractSchemaError` con `'tipo'` + índice de columna; no retorna objeto. Msg real inspeccionado. | RED (Caso 4) | **cubierto** |
| CA-05 | `test_load_contract_otros_campos_faltantes` (param. nombre/nulable/llave) | `ContractSchemaError` identifica cada campo + columna. Caracterización blindada. | caracterización | **cubierto** |
| CA-06 | `test_load_contract_tipo_fuera_de_enum` | `ContractSchemaError` con valor inválido + columna + **los 6 permitidos** (verificado en msg real). | RED (Caso 6) | **cubierto** |
| CA-07 | `test_load_contract_yaml_roto_parse_error` | `ContractParseError` (no `Schema`); verifica no-herencia mutua → distinguibles por tipo (HU-04). | RED (Caso 10) | **cubierto** |
| CA-08 | `test_load_contract_parse_error_mensaje_accionable` | Msg contiene "yaml" + "sintax/inválid"; fixture `.txt` para que "yaml" no se cuele por la ruta. Test robusto. | RED (Caso 11) | **cubierto** |
| CA-09 | `test_load_contract_duplicados_exactos` | `ContractSchemaError` nombra el duplicado (`test_id`); no retorna objeto. | RED (Caso 8) | **cubierto** |
| CA-10 | `test_load_contract_no_duplicado_por_caso_o_espacio` (param.) | `test_id` vs `Test_ID` y `test_id ` NO son duplicados (comparación exacta, D-23e). Caracterización blindada. | caracterización | **cubierto** |
| CA-11 | `test_load_contract_lista_vacia` | `ContractSchemaError` con mensaje exacto `"la lista de columnas no puede estar vacía"`. | RED (Caso 7) | **cubierto** |
| CA-12 | `test_load_contract_frontera_no_toca_bronze` (param. válido/inválido) | Espía sobre `builtins.open`: única ruta abierta == `path`; ninguna bajo `data/bronze`. Frontera D-21. | caracterización | **cubierto** |
| CA-13 | `test_load_contract_core_invocable_sin_cli` | Invocación directa → `Contract`; firma `(path)`; `zeroleak.cli` sin símbolo/uso "contract". Core-only D-23d. | caracterización | **cubierto** |
| CA-14 | `test_load_contract_fail_fast_un_solo_error` | Una sola `ContractSchemaError`, sin "validation error"/"errors for", sin líneas apiladas. Msg real inspeccionado. | caracterización | **cubierto** |
| CA-15 | `test_load_contract_fixtures_sinteticos_sin_pii` | Fixtures bajo `tmp_path`, jamás bajo `clients/*/data/` (regex); nombres en lista blanca sintética, sin `@`. C-01. | caracterización | **cubierto** |

**Sobre los 8 tests de caracterización (CA-02/03/05/10/12/13/14/15):** revisados
individualmente, **no** son tautológicos ni vacíos. Cada uno asevera algo real
(igualdad de campos, cardinalidad del enum, ausencia de rutas prohibidas, firma,
cardinalidad de una excepción, whitelist de nombres) y el `state.json` documenta
que el `tdd_tester` inyectó un defecto temporal reversible por caso y comprobó
que el test **falla** correctamente ante el defecto (blindaje legítimo, patrón
`ingest`). El verificador re-ejecutó la suite completa en verde y validó los
mensajes de error directamente.

## Auditoría de alcance (definition / plan / decisiones)

| Aspecto | Esperado | Observado | OK |
|---|---|---|---|
| Frontera D-21 (no toca `data/bronze/`) | Solo abre el `path` del contrato | CA-12: espía de `open` confirma única ruta = el propio YAML | ✔ |
| Core-only D-23d (sin CLI) | Ningún `zlk contract validate`; `load_contract` invocable directo | CA-13: sin símbolo/uso "contract" en `zeroleak.cli`; firma `(path)` | ✔ |
| Enum cerrado de 6 tipos D-23b | `string/integer/float/date/datetime/boolean` | `TipoDato` con exactamente 6; CA-03 exige `set(TipoDato)` completo; `datetime` presente | ✔ |
| Fail-fast D-23c | Un solo primer error, sin agregación | `_mensaje_esquema` toma `exc.errors()[0]`; CA-14 verifica cardinalidad | ✔ |
| Duplicados por cadena exacta D-23e | Sin normalizar mayúsculas/espacios | CA-09 (duplica) / CA-10 (no duplica por caso/espacio) | ✔ |
| Idioma ES campos D-23a | `nombre/tipo/nulable/llave` bajo `contract_data.columnas` | Modelos y fixtures en ES | ✔ |
| Dos excepciones distinguibles por tipo | `ContractParseError` vs `ContractSchemaError` | CA-07 verifica no-herencia mutua | ✔ |
| Out of scope respetado | Sin comparar CSV real, sin `business_rules`/`finance`, sin `ClientConfig`, sin CLI | Módulo `config/contract.py` limitado a leer+validar el YAML | ✔ |

## Cobertura HU → CA (toda HU con ≥ 1 CA con evidencia)

| HU | CA (con evidencia verde) | OK |
|---|---|---|
| HU-01 | CA-01, CA-02, CA-03 | ✔ |
| HU-02 | CA-04, CA-05, CA-14 | ✔ |
| HU-03 | CA-03, CA-06 | ✔ |
| HU-04 | CA-07, CA-08 | ✔ |
| HU-05 | CA-09, CA-10, CA-11, CA-14 | ✔ |
| HU-06 | CA-12 | ✔ |
| HU-07 | CA-13 | ✔ |
| HU-08 | CA-15 | ✔ |

Las 8 historias quedan cubiertas.

## Cumplimiento de restricciones (constraints.md)

- **C-01 (Datos en Bóveda, INVIOLABLE):** cumplido. Todos los fixtures son
  YAMLs sintéticos escritos en `tmp_path`; ninguno reside bajo `clients/*/data/`
  (verificado por CA-15 con regex y por inspección de `conftest.py`). Los
  nombres de columna son ficticios y auditables por lista blanca. Ningún dato
  real de cliente interviene.
- **C-03 (integración a `main` solo vía PR con merge humano):** aplicable al
  paso 13; no se viola aquí (esta feature no hace merge).

## Hallazgos

### Bloqueantes
- **Ninguno.**

### Observaciones menores (no bloquean el veredicto)
1. **TSK-28 (`tdd_refactor`, refactor integral) sin ejecutar.** El plan reservó
   un refactor final integral de `config/contract.py`; en `plan.md` figura
   `no_implementada` y en `state.json` no hay fase de refactor final. No es
   bloqueante: la calidad ya se atendió con refactors por-caso (Casos
   1/4/6/7/8/10/11 marcados `refactored`), el código está limpio, tipado con
   generics de builtin y con docstrings que referencian los CA; la suite está
   verde. El módulo queda apto para PR; el refactor integral es pulido opcional.
2. **CA-14 — límite honesto del fixture.** El YAML de CA-14 (campo faltante +
   duplicados) produce de por sí **un** error a nivel de ítem en Pydantic (el
   `field_validator` de duplicados no llega a ejecutarse), por lo que el test
   verifica **cardinalidad** (una sola excepción, sin agregación), no que el
   fail-fast descarte activamente un segundo error. Es exactamente lo que el
   plan anticipó (nota de riesgo del gate paso 9) y es coherente con D-23c: el
   mensaje real confirma una sola línea sin la cadena multi-error de Pydantic.
   Cobertura suficiente para el criterio tal como está redactado.
3. **CA-15 — sin detector genérico de PII.** La ausencia de PII se blinda con una
   lista blanca de nombres de columna, no con un detector automático (no existe
   en el proyecto). Limitación conocida y declarada en el propio test; la parte
   automáticamente verificable (rutas fuera de `clients/*/data/`) sí es sólida.

Ninguna observación degrada un `CA-xx` a `parcial` ni compromete C-01.

## Etapa de retorno recomendada

**No aplica** (veredicto CONFORME). La feature queda lista para el **paso 13**:
apertura de PR por el agente → gate humano (`human_test` + `merge_to_main`, C-03).
Si el equipo lo desea, puede ejecutarse TSK-28 (refactor integral) antes del PR
como pulido opcional, manteniendo la suite verde; no es requisito para el gate.

---

**Firma:** `spec_verifier` (paso 12), contexto fresco, sin modificar código ni
tests. Suite ejecutada y leída por el verificador: **88 passed**.
