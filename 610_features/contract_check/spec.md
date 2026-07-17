# Spec — contract_check

> Artefacto del paso 6 (`spec_writer`), escrito **después** de aprobar el notebook (spike, gate del paso 5). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate, paso 7) antes de planear.

## Resumen
`contract check` agrega a `zlk` un tercer subcomando —`zlk contract check <CLIENTE>`— que resuelve el `contract_data.yaml` del tenant por la convención vigente, comprueba las precondiciones de existencia que el motor no cubre, invoca `load_contract` **sin modificar el core** y traduce su veredicto a salida observable: éxito por stdout con exit `0`, o el mensaje del motor **verbatim** por stderr con un exit code que distingue precondición, parse y esquema.

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `ZEROLEAK_CLIENTS_ROOT` (variable de entorno) | string | Raíz de tenants. Si no está definida → `./clients` relativo al cwd (`cli._clients_root()`, convención vigente de `client new` / `ingest`). |
| requiere | `<clients_root>/<CLIENTE>/` | Directorio | Precondición: debe existir y ser directorio. |
| requiere | `<clients_root>/<CLIENTE>/input/contract_data.yaml` | YAML | Precondición: debe existir y ser archivo. Su esquema es el de `contract_multifile` (`contract_data.archivos[].columnas[]`); **esta feature no lo redefine ni lo valida por su cuenta**: lo entrega tal cual a `load_contract`. |
| produce | *(ninguno)* | — | El comando es de **solo lectura**: no crea, modifica ni borra ningún archivo (HU-08 / D-22). Sus únicas salidas son **stdout**, **stderr** y el **exit code**. |

### Catálogo de mensajes de la **fachada** (F-01…F-03) — congelado

> Los mensajes del **motor** (M-01…M-13) son propiedad de `contract_multifile` y esta feature **no los escribe: los muestra**.
> Los de abajo son **nuevos y de otra capa** (la fachada), por eso se numeran `F-xx` y no colisionan con el catálogo `M-xx`.
> Son **contrato**: los tests los fijan literalmente, con el mismo rigor con que `contract_multifile` congeló M-01…M-13.

| ID | Cuándo | Canal | Texto |
|---|---|---|---|
| F-01 | Contrato válido (éxito) | stdout | Dos líneas:<br>`OK  contrato válido: <CLIENTE> — <ruta_del_contrato>`<br>`    <n> archivo(s) declarado(s): <nombre_1>, <nombre_2>, …` |
| F-02 | El directorio del tenant no existe | stderr | `Tenant inexistente o incompleto: '<CLIENTE>'` (`{client!r}`) — **texto idéntico** al de `TenantNotFoundError` de `ingest` (`ingest/core.py:125`) |
| F-03 | El tenant existe pero le falta el contrato | stderr | `El tenant '<CLIENTE>' no tiene contrato: falta <ruta_del_contrato>` |

Detalles vinculantes de forma:
- **F-01**: dos espacios tras `OK`; ` — ` es guion largo (U+2014) rodeado de espacios; `<ruta_del_contrato>` es la ruta completa del YAML tal como la resolvió la fachada (`<clients_root>/<CLIENTE>/input/contract_data.yaml`); la segunda línea va indentada con 4 espacios; `<n> = len(contract.archivos)`; los nombres se listan en el **orden declarado**, separados por `", "`.
- **F-01/F-03** usan **acento ortográfico** ("válido") en coherencia con M-01…M-13, que están acentuados. El spike los imprimió sin acentos por convención propia del notebook; la forma **normativa es la acentuada** (ver punto abierto O-1 del gate).
- **F-02** se reutiliza literalmente para no inventar una segunda redacción de "tenant que no está" en el producto.

### Exit codes — congelados

| Código | Situación | Canal del mensaje |
|---|---|---|
| `0` | Contrato válido | stdout (F-01) |
| `1` | Invocación mal formada (cualquier `argv` que no despache) | stderr (`_USAGE`) |
| `2` | Precondición incumplida: tenant ausente **o** contrato ausente | stderr (F-02 / F-03) |
| `3` | `ContractParseError` (YAML sintácticamente roto) | stderr (mensaje del motor **verbatim**) |
| `4` | `ContractSchemaError` (YAML legible que no cumple el esquema) | stderr (mensaje del motor **verbatim**) |

- Los valores `0`/`1`/`2` **respetan la semántica vigente** de `cli.py` (0 = éxito, 1 = uso/fallo parcial, 2 = precondición de tenant).
- `3` y `4` materializan la **variante A** resuelta en el gate del paso 5 (criterio 12 del `feature_contract`): parse y esquema se distinguen **por exit code**, nunca por prefijo, porque un prefijo obligaría a aflojar la igualdad exacta de stderr contra el mensaje del motor.
- `2` es **un solo código** para las dos precondiciones (criterio 13 del `feature_contract`): tenant ausente y contrato ausente se distinguen **por mensaje** (F-02 vs F-03), no por código.

## Comportamiento Esperado

1. **Parseo del subcomando.** `argv` corresponde a `contract check` **si y solo si** `len(argv) == 3 and argv[0] == "contract" and argv[1] == "check"`; entonces `<CLIENTE> = argv[2]`. La longitud es **exacta**, como `_parse_client_new_name` — por eso `contract check <CLIENTE> extra` **no** despacha y cae al uso (con `>= 3` se tragaría argumentos de más en silencio). Cualquier otro `argv` que tampoco despache `client new` ni `ingest` imprime `_USAGE` por stderr y retorna `1`.
2. **Resolución de la ruta.** `clients_root = cli._clients_root()` (misma función, sin duplicar la convención); `contrato = clients_root / <CLIENTE> / "input" / "contract_data.yaml"`.
3. **Precondición 1 — tenant.** Si `clients_root/<CLIENTE>` no es directorio → F-02 por stderr, exit `2`. **No se invoca el motor.**
4. **Precondición 2 — contrato.** Si el YAML no es archivo → F-03 por stderr, exit `2`. **No se invoca el motor.** Ambas precondiciones se comprueban **antes** de `load_contract`, porque el motor hace `open(path)` sin capturar `FileNotFoundError` (`contract.py:213`) y por D-22 **asume** que el YAML existe: cubrir el hueco es trabajo de la fachada, no del core.
5. **Invocación del motor.** `contract = load_contract(contrato)`. Es la **única** llamada de validación: la fachada no inspecciona el YAML, no lo pre-parsea, no decide nada sobre su contenido.
6. **Traducción del fallo.** `ContractParseError` → `str(exc)` por stderr **sin una sola alteración** (ni prefijo, ni sufijo, ni traducción, ni reformato) + exit `3`. `ContractSchemaError` → ídem + exit `4`. En ambos casos **stdout queda vacío**.
7. **Traducción del éxito.** F-01 por stdout (identificando tenant, ruta y archivos declarados) + exit `0`, con **stderr vacío**.
8. **Fail-fast heredado.** El motor es fail-fast (D-23c): se muestra **el primer error**, tal como el motor lo da. La fachada no agrega, agrupa ni continúa.
9. **Fachada delgada.** El subcomando solo resuelve ruta, comprueba precondiciones, invoca y traduce. Ni un gramo de lógica de validación propia (mismo criterio que CA-02/CA-03 de `client_scaffold` y CA-12 de `ingest`).
10. **`_USAGE`.** Se **agrega una línea** al texto vigente, conservando las dos existentes:
    ```
    uso: zlk client new <NOMBRE_CLIENTE>
         zlk ingest <CLIENTE> <ruta>...
         zlk contract check <CLIENTE>
    ```
11. **Solo lectura.** Ninguna ruta de ejecución escribe en disco.

## Casos Límite y Errores

- **Tenant inexistente** → F-02, exit `2`, sin `FileNotFoundError` ni traceback.
- **Tenant existente sin `input/contract_data.yaml`** → F-03, exit `2`, sin traceback.
- **Contrato recién scaffoldeado por `client new`** (`contract_data:` con raíz presente y sin cuerpo, `scaffold.py:_CONTRACT_DATA_YAML`) → PyYAML lo parsea a `None` → el motor emite **M-01** → stderr = M-01 verbatim, exit `4`. **Camino de primera clase, no borde**, y **sin rama especial en la fachada**: el motor ya lo cubre.
- **YAML sintácticamente roto** → **M-12** verbatim, exit `3`.
- **Contrato que viola el esquema** (cualquiera de M-01…M-11, M-13) → mensaje verbatim, exit `4`.
- **`contract`, `contract check`, `contract foo`, `contract check <C> extra`, `argv` vacío** → `_USAGE` por stderr, exit `1`, stdout vacío, sin excepción no controlada.
- **`ZEROLEAK_CLIENTS_ROOT` definida** → manda; **no definida** → `./clients` relativo al cwd.
- **Contrato válido de un solo archivo y de varios archivos** → ambos exit `0`; F-01 refleja el recuento real.
- **Invocaciones repetidas** → idempotentes por construcción (solo lectura): el mismo tenant produce el mismo veredicto sin alterar nada.
- **YAML inválido** → **nunca se repara** (D-22): el comando diagnostica, no autoreparara; el archivo queda byte a byte igual.

## Interfaces / Firmas Públicas

- **CLI (única interfaz nueva):** `zlk contract check <CLIENTE>` → exit code ∈ `{0, 1, 2, 3, 4}` con la semántica congelada arriba.
- **Punto de entrada verificable en proceso:** `main(argv: list[str] | None = None) -> int` (ya existente), invocado como en `test_cli_client_new.py` / `test_cli_ingest.py`. El orden de despacho de `client new` e `ingest` **no cambia** su comportamiento observable.
- **Motor consumido, no modificado:** `load_contract(path) -> Contract`, `Contract`, `ArchivoContrato`, `Columna`, `TipoDato`, `ContractParseError`, `ContractSchemaError`, importados desde `zeroleak.config` tal como se exportan hoy.
- **Convención reutilizada:** `_clients_root() -> Path`.

> Firmas a nivel de contrato observable; los nombres de los helpers privados de `cli.py` y su estructura interna son del bucle TDD.

## Criterios de Aceptación (verificables)

> Cada criterio lleva un **código `CA-xx`** (único en la feature) y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.
> Todos los fixtures son **sintéticos** y viven en `tmp_path` (C-01).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado un tenant sintético cuyo `input/contract_data.yaml` declara 2 archivos válidos (`clientes.csv`, `ventas.csv`), `main(["contract", "check", "<CLIENTE>"])` retorna exactamente `0`, escribe en stdout un texto no vacío y deja **stderr vacío**. | HU-01 |
| CA-02 | En ese mismo caso, stdout es **exactamente** F-01 formateado: primera línea `OK  contrato válido: <CLIENTE> — <ruta>` con `<ruta> == str(clients_root/<CLIENTE>/input/contract_data.yaml)`, y segunda línea `    2 archivo(s) declarado(s): clientes.csv, ventas.csv` (recuento y nombres en el orden declarado). Un contrato válido de **un solo** archivo produce `1 archivo(s) declarado(s): <nombre>`. | HU-01 |
| CA-03 | **Propiedad verbatim (esquema).** Para un tenant cuyo YAML viola el esquema, se compara el mismo archivo por dos caminos: `str(exc)` capturado llamando `load_contract(ruta)` **directo**, y el `stderr` del comando. `stderr.strip() == str(exc)` (igualdad exacta), `stdout == ""` y el exit code es `4`. | HU-02 |
| CA-04 | **Mensaje concreto (esquema).** Para un YAML donde `archivos[1]` (`ventas.csv`) declara `columnas: []`, el stderr del comando es **exactamente** `archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía` (**M-07**, verificado por igualdad exacta contra la constante congelada `_MENSAJE_COLUMNAS_VACIA` con su localizador D-25a, no por subcadena) y el exit code es `4`. | HU-02 |
| CA-05 | **Parse verbatim.** Para un `contract_data.yaml` sintácticamente inválido, el comando retorna exactamente `3`, deja stdout vacío y su stderr es igual por **igualdad exacta** a `str(exc)` del `ContractParseError` que lanza `load_contract` sobre el mismo archivo (**M-12**, con el detalle de PyYAML intacto). | HU-03 |
| CA-06 | **Distinción parse/schema (variante A).** Con dos tenants —uno de YAML roto y otro que viola el esquema— los exit codes son `3` y `4` respectivamente: son **distintos entre sí** y **distintos de `0`, `1` y `2`**; y ninguno de los dos stderr lleva prefijo, sufijo ni adorno añadido por la fachada (ambos siguen cumpliendo la igualdad exacta con el mensaje del motor). | HU-02, HU-03 |
| CA-07 | **Primera corrida (M-01).** Para un tenant cuyo `input/contract_data.yaml` tiene el contenido **exacto** que deja `client new` (`scaffold.py:_CONTRACT_DATA_YAML`: raíz `contract_data:` sin cuerpo), el comando retorna `4` y su stderr es **exactamente** `_MENSAJE_RAIZ_INVALIDA.format(cuerpo=None)` (**M-01**). El texto de stderr **no contiene ninguna cadena propia de la fachada** (no aparecen `OK`, `Tenant inexistente`, `no tiene contrato`): evidencia de que la fachada **no tiene rama especial** para este caso y es el motor quien lo cubre. | HU-04 |
| CA-08 | **Tenant inexistente.** Con `<CLIENTE>` que no existe bajo `clients_root`, el comando retorna exactamente `2`, stdout queda vacío y stderr es **exactamente** `Tenant inexistente o incompleto: '<CLIENTE>'` (**F-02**); stderr **no contiene** `Traceback` ni `FileNotFoundError`. | HU-05 |
| CA-09 | **Contrato ausente.** Con un tenant que existe como directorio pero **sin** `input/contract_data.yaml`, el comando retorna exactamente `2` —el **mismo** código que CA-08— y stderr es **exactamente** `El tenant '<CLIENTE>' no tiene contrato: falta <ruta>` (**F-03**, con la ruta resuelta); stderr **no contiene** `Traceback` ni `FileNotFoundError`. El test verifica además que los stderr de CA-08 y CA-09 son **distintos entre sí**: mismo código, mensajes distintos. | HU-05 |
| CA-10 | **Precondición antes del motor.** Parcheando `load_contract` en el namespace de `zeroleak.cli` con un doble que registra sus llamadas, invocar el comando sobre (a) un tenant inexistente y (b) un tenant sin contrato deja el doble con **0 llamadas** en ambos casos, y ambas invocaciones retornan `2` sin propagar excepción. Guarda de no-vacuidad: el mismo doble, sobre un tenant **con** contrato, registra **exactamente 1** llamada con la ruta del YAML — el instrumento está vivo. | HU-05 |
| CA-11 | **`ZEROLEAK_CLIENTS_ROOT` manda.** Con dos raíces sintéticas `root_a` (que contiene `<CLIENTE>` con contrato válido) y `root_b` (vacía), el **mismo** `main(["contract","check","<CLIENTE>"])` retorna `0` con `ZEROLEAK_CLIENTS_ROOT=root_a` y `2` con `ZEROLEAK_CLIENTS_ROOT=root_b`; en el caso de éxito la ruta impresa en F-01 cae bajo `root_a`. | HU-06 |
| CA-12 | **Fallback `./clients`.** Con `ZEROLEAK_CLIENTS_ROOT` **no definida** (`monkeypatch.delenv`) y el cwd fijado en un `tmp_path` que contiene `clients/<CLIENTE>/input/contract_data.yaml` válido, el comando retorna `0` y la ruta impresa en F-01 es la de `<cwd>/clients/<CLIENTE>/input/contract_data.yaml`. | HU-06 |
| CA-13 | **Invocaciones mal formadas.** Cada uno de `["contract"]`, `["contract","check"]`, `["contract","foo"]`, `["contract","check","<CLIENTE>","de_mas"]` y `[]` retorna exactamente `1`, deja stdout vacío, imprime por **stderr** un texto que contiene `uso: zlk` y la subcadena `contract check`, y **no levanta ninguna excepción**. | HU-07 |
| CA-14 | **`len(argv) == 3` exacto.** Con `load_contract` parcheado en el namespace de `zeroleak.cli` como doble contador, `main(["contract","check","<CLIENTE>","extra"])` sobre un tenant **con contrato válido** deja el doble con **0 llamadas** y retorna `1` con `_USAGE` en stderr: el argumento de más **no se traga en silencio**. Guarda de no-vacuidad: la invocación de 3 argumentos con el mismo doble registra 1 llamada. | HU-07 |
| CA-15 | **`_USAGE`.** `zeroleak.cli._USAGE` es **exactamente** las tres líneas `uso: zlk client new <NOMBRE_CLIENTE>` / `     zlk ingest <CLIENTE> <ruta>...` / `     zlk contract check <CLIENTE>`: conserva íntegras las dos vigentes y agrega **una sola** línea nueva. | HU-07 |
| CA-16 | **Solo lectura.** Se toma una foto de **todo** el árbol `clients_root` sintético (ruta relativa → `(tamaño, mtime_ns, sha256)`) que incluye tenants válido, scaffoldeado, con esquema inválido, con YAML roto, sin contrato, y un CSV sintético en `data/bronze/` + `manifest.json`; se ejecuta el comando sobre **todos** los casos (válidos e inválidos, incluidos tenant fantasma y argv mal formado); la foto posterior es **idéntica** a la anterior (0 archivos creados, 0 borrados, 0 con contenido o `mtime_ns` alterado). **Guarda de no-vacuidad:** el test assertea `len(foto_antes) >= 1` **antes** de comparar — dos fotos vacías no probarían nada. | HU-08 |
| CA-17 | **Frontera D-21 — no se lee ningún CSV.** Con un audit hook de CPython (`sys.addaudithook`, evento `open`) activo durante `contract check` sobre un tenant que **sí tiene** un CSV sintético en `data/bronze/` y un `manifest.json`: (1) **guarda de no-vacuidad (L-17)** — el espía observó ≥ 1 apertura **y** entre ellas está `contract_data.yaml`, prueba de instrumento vivo; (2) recién entonces, la aserción de ausencia: **ninguna** ruta observada cae bajo `data/bronze|silver|gold`, termina en `.csv` o es `manifest.json`; (3) el comando retornó `0`. | HU-09 |
| CA-18 | **Segundo instrumento, independiente.** Con `mock.patch.object(zeroleak.config.contract, "open", espia, create=True)` (no se parchea `builtins.open`: L-17, quedaría mudo), el comando sobre el tenant válido hace que el espía registre **exactamente 1** apertura y que esa apertura sea el `contract_data.yaml` del tenant; el comando sigue retornando `0` con el espía puesto. **Guarda de no-vacuidad:** se assertea `espia.vistos != []` antes de afirmar el "exactamente 1". | HU-09 |
| CA-19 | **Core intacto.** Al cerrar la feature, `sha256(app/src/zeroleak/config/contract.py)` es **idéntico** al de la misma ruta en `main` antes de empezar (equivalente: `git diff main -- app/src/zeroleak/config/contract.py` vacío). Ningún archivo bajo `app/src/zeroleak/config/` aparece en el diff de la rama. | HU-10 |
| CA-20 | **Fachada delgada, sin lógica propia.** Parcheando `load_contract` en el namespace de `zeroleak.cli` para que lance `ContractSchemaError("mensaje sintético de prueba")`, el comando sobre un tenant con contrato **válido en disco** imprime por stderr **exactamente** `mensaje sintético de prueba` y retorna `4`: el veredicto y el texto provienen **únicamente** del motor, la fachada no revalida ni contradice. Análogamente, con el doble lanzando `ContractParseError("…")` el exit code es `3`. | HU-10 |
| CA-21 | **Modificación acotada y declarada de la suite.** En `app/tests/test_contract_multifile.py::test_load_contract_core_invocable_sin_cli` se retiran **exactamente dos** aserciones —`simbolos_contract == []` y `"contract" not in zeroleak_cli._USAGE.lower()`— y se **conservan las tres** restantes (invocación directa → `isinstance(contrato, Contract)`; `list(signature.parameters) == ["path"]`; `signature.return_annotation is Contract`), con el docstring actualizado para reflejar la reinterpretación de CA-27 (*el core sigue siendo invocable sin CLI; ahora además tiene una*). El diff de la rama sobre `app/tests/` **no elimina ni debilita ninguna otra aserción ni ningún otro test**: `test_contract_multifile.py` conserva el mismo número de funciones de test que en `main`, y la suite completa (los 111 tests vigentes + los nuevos de esta feature) queda **en verde**. | HU-10 |
| CA-22 | **C-01, Datos en Bóveda.** Todos los tenants, YAMLs y CSV usados por los tests nuevos se construyen en `tmp_path` con datos sintéticos; ningún test nuevo lee `clients/` del repositorio ni ninguna ruta fuera de `tmp_path`, y los nombres de columna usados en los fixtures pertenecen a la lista blanca sintética ya establecida (`cliente_id`, `correo`, `alta`, `venta_id`, `monto`), sin PII real. | HU-11 |
| CA-23 | **Integración end-to-end.** Sobre un `clients_root` sintético: (1) `main(["client","new","<CLIENTE>"])` → `0`; (2) `main(["contract","check","<CLIENTE>"])` sobre el tenant recién creado → `4` con **M-01** por stderr; (3) se **edita a mano** el `contract_data.yaml` dejándolo válido y `contract check` → `0` con F-01; (4) se edita dejándolo inválido por esquema → `4` con el mensaje del motor verbatim. La secuencia completa corre en un solo test, invocando `main(argv)` en proceso. | HU-01, HU-04 |

### Trazabilidad HU → Spec (cobertura)

> Toda `HU-xx` de `definition.md` está cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-23 |
| HU-02 | CA-03, CA-04, CA-06 |
| HU-03 | CA-05, CA-06 |
| HU-04 | CA-07, CA-23 |
| HU-05 | CA-08, CA-09, CA-10 |
| HU-06 | CA-11, CA-12 |
| HU-07 | CA-13, CA-14, CA-15 |
| HU-08 | CA-16 |
| HU-09 | CA-17, CA-18 |
| HU-10 | CA-19, CA-20, CA-21 |
| HU-11 | CA-22 |

## No-Objetivos

- **No** modificar `config/contract.py`: ni la firma de `load_contract`, ni los modelos, ni las excepciones, ni **una letra** de M-01…M-13 (CA-19).
- **No** escribir, corregir, autocompletar ni crear `contract_data.yaml`: el comando **diagnostica, no repara** (D-22; el entrevistador/autor es T-44, futuro).
- **No** emparejar el contrato con los archivos de `data/bronze/` ni leer/validar ningún CSV: frontera D-21 intacta, eso es `load_data`.
- **No** validar `business_rules.yaml`, `finance.yaml` ni el Maestro de Sectores: el subcomando es `contract check`, no `config check` (D-21).
- **No** doblar la validación dentro de `zlk ingest`: sigue siendo archivador notarial que no parsea contenido (opción (b) de T-68, descartada en el paso 1).
- **No** agregar multi-error: el motor es fail-fast (D-23c); se muestra el primer error tal como lo da.
- **No** modo interactivo, `--fix`, `--watch`, salida JSON ni ninguna bandera (E4: mínima complejidad).
- **No** validar `600_template/contract_data.yaml` como parte del comando (ya lo cubre CA-22 de `contract_multifile`).
- **No** distinguir parse de esquema por prefijo en el texto (variante B): descartada en el gate del paso 5 por romper la igualdad exacta de stderr.
