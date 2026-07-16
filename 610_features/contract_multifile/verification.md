# Verification — contract_multifile

> Artefacto del paso 12 (`spec_verifier`), escrito en **contexto fresco** por el
> agente verificador. Audita con mentalidad crítica que lo construido cumple la
> `spec.md` aprobada (28 `CA-xx` + catálogo congelado `M-01…M-13`), contrastando
> **cada criterio contra evidencia real ejecutada por el propio verificador** (no
> reportes heredados). Independencia P1/P3: el verificador **no** modificó código
> ni tests; solo ejecutó la suite y leyó su salida.

---

## 1. Resumen ejecutivo

- **Veredicto global: ✅ CONFORME.**
- **Suite ejecutada por el verificador** (`py -3.13 -m pytest app/tests -q`):
  **111 passed / 0 failed** (7.09 s). Corrida específica de la feature
  (`app/tests/test_contract_multifile.py -v`): **42 passed / 0 failed**
  (Python 3.13.7, pytest 9.1.1).
- **Cobertura de criterios:** los **28 CA-xx** están `cubierto` con evidencia
  verificada. **0** `parcial`, **0** `no cubierto`.
- **Mensajes congelados:** los tests que dependen de un `M-xx` fijan el texto por
  **igualdad exacta** (`assert str(exc) == …`), no por subcadena — verificado por
  lectura directa de cada aserción. Las constantes de `contract.py`
  (`_MENSAJE_*`, `_PLANTILLA_*`) coinciden carácter a carácter con los textos de
  la spec.
- **Alcance:** respetado. Core-only (sin fachada CLI, CA-27 lo blinda), frontera
  D-21 (no abre bronze/clients/.csv, CA-23 con guarda de no-vacuidad L-17), sin
  atajo `Contract.columnas` (CA-24). Restricción **C-01** respetada y **auditada
  por test** (CA-26): fixtures 100% sintéticos, ninguno bajo `clients/*/data/`.
- **Integración (paso 11):** `integration_tester` figura `pending` en `state.json`,
  pero el plan y D-23d (core-only) establecen explícitamente que **no aplican
  tareas de integración** a esta feature; la cobertura end-to-end se logra
  invocando `load_contract` directamente. No es un hueco de conformidad.

---

## 2. Resultado real de la suite (evidencia ejecutada, no heredada)

```
$ py -3.13 -m pytest app/tests -q
........................................................................ [ 64%]
.......................................                                  [100%]
111 passed in 7.09s

$ py -3.13 -m pytest app/tests/test_contract_multifile.py -v
...
42 passed in 1.56s
```

Los 42 tests de la feature incluyen las expansiones paramétricas (M-01 ×2,
M-04 ×3, campos faltantes ×3, no-duplicado por caso/espacio ×2, frontera ×2).
El total de 111 incluye además la suite preexistente del proyecto (CLI, etc.),
verde — lo que satisface CA-25 (migración sin fallos en toda la suite).

---

## 3. Matriz de trazabilidad CA → test → resultado observado

Todos los tests viven en `app/tests/test_contract_multifile.py`. Estado
observado = **PASSED** ejecutado por el verificador. "Igualdad exacta" = el test
asevera el mensaje `M-xx` con `assert str(exc_info.value) == mensaje_esperado`.

| CA | Test(s) que lo cubren | Evidencia / rigor observado | Estado |
|---|---|---|---|
| CA-01 | `test_load_contract_valido_dos_archivos_orden`, `test_load_contract_valido_tres_archivos_orden` | `len==2` y `==3`, nombres en orden declarado, `[3,4]` y `[3,4,2]` columnas | cubierto |
| CA-02 | `test_load_contract_fidelidad_de_campos_por_archivo` | ancla `archivos[1].columnas[0]==venta_id/integer/False/True` + fidelidad 1:1 de las 4+3 columnas | cubierto |
| CA-03 | `test_load_contract_columna_homonima_en_dos_archivos` | `cliente_id` en clientes.csv y ventas.csv aceptado, con `llave` distinta por archivo (duplicado por-archivo) | cubierto |
| CA-04 | `test_load_contract_un_archivo_caso_general`, `test_load_contract_valido_tres_archivos_orden` | `len==1` con fidelidad 1:1; N archivos como caso general sin cota | cubierto |
| CA-05 | `test_load_contract_seis_tipos_enum` | 6 tipos mapean a `TipoDato`; `set(tipos)==set(TipoDato)` | cubierto |
| CA-06 | `test_load_contract_archivos_vacia_ausente_nula_m04[archivos_vacia]` | M-04 igualdad exacta | cubierto |
| CA-07 | `..._m04[archivos_ausente]`, `..._m04[archivos_nula]` | M-04 igualdad exacta en ausente y nula | cubierto |
| CA-08 | `test_load_contract_esquema_viejo_m02` | M-02 igualdad exacta **y** `!= M-04` (disjunto del genérico) | cubierto |
| CA-09 | `test_load_contract_archivos_no_lista_m03` | M-03 igualdad exacta (`'archivos' debe ser una lista (se encontró: 'ventas.csv')`) | cubierto |
| CA-10 | `test_load_contract_archivo_sin_nombre_m06` | M-06 igualdad exacta; degradación a `archivo[1]` sin nombre | cubierto |
| CA-11 | `test_load_contract_columnas_vacias_en_archivo_m07` | M-07 igualdad exacta (índice + nombre) | cubierto |
| CA-12 | `test_load_contract_archivo_sin_columnas_m08` | M-08 igualdad exacta | cubierto |
| CA-13 | `test_load_contract_archivo_duplicado_no_adyacente_m05` | M-05 igualdad exacta; colisión **no adyacente** (índices 0 y 2 de 3) mata detector por pares | cubierto |
| CA-14 | `test_load_contract_mayusculas_no_son_duplicado` | `Ventas.csv`/`ventas.csv` cargan, `len==2` (cadena exacta) | cubierto |
| CA-15 | `test_load_contract_columna_sin_tipo_m09`, `test_load_contract_campo_tipo_faltante`, `test_load_contract_otros_campos_faltantes[nombre/nulable/llave]` | M-09 igualdad exacta; nombre de archivo presente aunque Pydantic no lo reporte | cubierto |
| CA-16 | `test_load_contract_tipo_fuera_de_enum`, `test_load_contract_tipo_fuera_de_enum_archivo_del_medio` | M-10 igualdad exacta; archivo del medio de 3 mata "reporta el último"/off-by-one | cubierto |
| CA-17 | `test_load_contract_duplicados_exactos` | M-11 igualdad exacta | cubierto |
| CA-18 | `test_load_contract_yaml_roto_parse_error`, `test_load_contract_parse_error_mensaje_accionable` | `ContractParseError` distinguible por tipo (no subclase mutua); prefijo M-12 con `startswith` | cubierto |
| CA-19 | `test_load_contract_raiz_nula_o_no_mapa_m01[raiz_nula]` | M-01 exacto `(se encontró: None)`; verifica `type is ContractSchemaError` (no AttributeError) | cubierto |
| CA-20 | `..._m01[raiz_no_mapa_cadena]` | M-01 exacto `(se encontró: 'pendiente_de_completar')`, sin AttributeError | cubierto |
| CA-21 | `test_load_contract_fail_fast_cardinalidad_agnostico_al_orden`, `test_load_contract_fail_fast_un_solo_error` | cardinalidad 1 + ausencia de agregación; acepta M-05 **o** M-10 (agnóstico al orden) | cubierto |
| CA-22 | `test_load_contract_plantilla_real_carga` | `load_contract("600_template/contract_data.yaml")` sin excepción, `len>=1`, plantilla declara `archivos` y no `columnas` | cubierto |
| CA-23 | `test_load_contract_frontera_no_toca_bronze_con_guarda[valido/invalido]` | espía de `open`: guarda de no-vacuidad (`>=1`) **primero**, luego `== [str(path)]`; sin bronze/clients/.csv | cubierto |
| CA-24 | `test_contract_no_expone_columnas` | `'columnas' not in Contract.model_fields`, acceso lanza `AttributeError`, `hasattr` False | cubierto |
| CA-25 | `test_auditoria_migracion_sin_esquema_viejo` (+ suite 111 verde) | auditoría estática: 2 apariciones del esquema viejo, ambas exentas como caso inválido; ventana relajada de M-07 endurecida | cubierto |
| CA-26 | `test_load_contract_fixtures_sinteticos_sin_pii` | rutas bajo `tmp_path`, lista blanca de columnas/archivos, sin PII, ninguno bajo `clients/*/data/` | cubierto |
| CA-27 | `test_load_contract_core_invocable_sin_cli` | firma `signature(load_contract).parameters == ['path']`, retorno `is Contract`, `zeroleak.cli` sin símbolo/uso `contract` | cubierto |
| CA-28 | `test_load_contract_hibrido_archivos_y_columnas_residual_m13` | M-13 igualdad exacta + disyunción verificada (mensaje `!=` al del esquema viejo) | cubierto |

**Cobertura HU:** toda `HU-01…HU-12` de `definition.md` está cubierta por ≥1 CA
`cubierto` (según la tabla HU→CA de la spec), por lo que la trazabilidad de
historias se satisface transitivamente.

---

## 4. Auditoría de alcance y restricciones (verificada)

- **Frontera D-21 (CA-23):** el test instrumenta `builtins.open` y afirma
  **exactamente una** apertura, el propio `contract_data.yaml`; ninguna ruta
  `data/bronze/`, `clients/` ni `.csv`. Incluye la **guarda de no-vacuidad L-17**
  (afirma `>= 1` apertura antes de las aserciones de ausencia): evidencia no
  vacua. Verificado ejecutando ambas variantes (fixture válido e inválido).
- **C-01 "Datos en Bóveda" (CA-26):** auditado por test — fixtures sintéticos en
  `tmp_path`, listas blancas de nombres de columna y archivo, patrón regex que
  rechaza `clients/<x>/data/`. Única excepción declarada: CA-22 lee la plantilla
  versionada `600_template/contract_data.yaml`, que es sintética por definición.
- **Core-only D-23d (CA-27):** sin fachada CLI; firma pública exacta
  `load_contract(path) -> Contract`, sin el parámetro `estilo` del spike.
- **Sin atajo de compatibilidad D-25d (CA-24):** `Contract` no expone `columnas`.
- **Cambios quirúrgicos:** la feature evolucionó `app/src/zeroleak/config/contract.py`
  y su reexport, reescribió `600_template/contract_data.yaml` al esquema
  `archivos[]` (verificado: declara `contract_data.archivos`, 2 archivos de
  ejemplo, sin PII) y migró/renombró la suite de tests. No se crearon módulos
  nuevos fuera de lo planeado.
- **Textos congelados:** las constantes de `contract.py` (M-01..M-05, M-07, M-11,
  M-12, M-13) y las plantillas (M-06, M-08, M-09, M-10) coinciden con la spec;
  cada `CA` dependiente de texto lo fija por igualdad exacta.

---

## 5. Hallazgos y observaciones

Ningún hallazgo bloqueante. Observaciones menores (no afectan el veredicto):

- **O-1 (informativa) — `integration_tester` en `state.json` figura `pending`.**
  Es coherente con el plan (D-23d core-only: "sin fase `integration_tester`").
  No representa un hueco de conformidad; se deja constancia para que el gate
  humano no lo interprete como etapa omitida por error. Recomendación: al
  cerrar, marcar ese bloque como `not_applicable`/`skipped` con la razón D-23d,
  para evitar ambigüedad futura.
- **O-2 (informativa) — breaking de superficie pública ya aceptado (D-25d).**
  El gate del plan (paso 9) registró que dos scripts de la feature ya cerrada
  `config_contract` (`pruebas_humanas.py`, `cargar_contrato.py`) consumen
  `.columnas` y quedarán rotos; se aceptó el breaking y se anotó tarea de
  limpieza futura (T-69). Fuera del alcance de esta verificación; solo se
  recuerda para el gate humano.

---

## 6. Veredicto y siguiente paso

**✅ CONFORME.** Todos los 28 `CA-xx` cubiertos con evidencia verificada por el
propio verificador; suite **111 passed / 0 failed**; alcance y restricciones
(D-21, D-23d, D-25d, C-01) respetados y, donde aplica, blindados por test.

La sesión principal puede proceder al **paso 13 (abrir PR)** → gate humano
(`human_test` + `merge_to_main`, C-03: el merge lo hace el humano). No se
recomienda ninguna etapa de retorno.
