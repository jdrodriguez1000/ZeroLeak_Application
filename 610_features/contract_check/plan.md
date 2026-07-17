# Plan — contract_check

> Artefacto del paso 8 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate, paso 9) antes de arrancar el bucle.
>
> Base canónica: `spec.md` (**CA-01 … CA-23** + catálogo de fachada **F-01 … F-03** y tabla de exit codes, **aprobada sin cambios** en el gate del paso 7), `definition.md` (HU-01 … HU-11), `feature_contract.md` (estrella polar, con la corrección del gate del paso 5), `contract_check.ipynb` (spike ejecutado, 14/14 celdas con salidas reales, gate del paso 5 APROBADO), `900_persistence/` (D-21, D-22, D-23c, D-25/D-26, C-01, L-10, L-13/L-14, L-17).
>
> **Contexto ya fijado por la spec y por los gates 5 y 7 (este plan lo honra, no lo reabre):**
> 1. **Variante A:** el mensaje del motor sale por stderr **intacto**; parse y esquema se distinguen por **exit code** (`3` / `4`). Nunca por prefijo.
> 2. **Exit codes congelados:** `0` éxito · `1` argv que no despacha (`_USAGE`) · `2` precondición (tenant **o** contrato ausente, **un solo código**, se distinguen por mensaje) · `3` `ContractParseError` · `4` `ContractSchemaError`.
> 3. **F-01 es de dos líneas y lleva acentos** (resolución O-1/O-2 del gate del paso 7). El spike las imprimió sin acentos por convención del notebook; la forma **normativa es la acentuada**.
> 4. **F-02 duplica literalmente el texto de `TenantNotFoundError` de `ingest`**: **deuda declarada y aceptada** (O-3). **No** se exporta ni se importa la plantilla desde `ingest` (evitaría acoplar `contract_check` a otro eje, D-21).
> 5. **El core no se toca.** `app/src/zeroleak/config/contract.py` queda byte a byte idéntico al de `main` (CA-19). Si aparece la tentación de tocarlo, sube al gate.
> 6. **CA-21 es la única modificación permitida a la suite vigente:** el retiro de **exactamente dos** aserciones de `test_load_contract_core_invocable_sin_cli`. Baseline verificada: **111 passed**.

## Enfoque Técnico

**Ubicación.** No se crean módulos nuevos de producción: la feature **agrega una fachada delgada** a `app/src/zeroleak/cli.py`, el mismo archivo que ya hospeda `client new` e `ingest`. **Ningún** archivo bajo `app/src/zeroleak/config/` se toca.

**Forma del cambio de producción (~15 líneas, prototipo de la Celda 3 del spike):**

- **Import nuevo (única superficie consumida):** `from zeroleak.config import ContractParseError, ContractSchemaError, load_contract`. Se consume la superficie **tal como se exporta hoy**; nada se redefine.
- **`_parse_contract_check_args(argv) -> str | None` — nuevo.** Mismo patrón que `_parse_client_new_name` (`cli.py:32`), con **longitud exacta**: `len(argv) == 3 and argv[0] == "contract" and argv[1] == "check"` → `argv[2]`; en cualquier otro caso `None`. El `== 3` (y no `>= 3`, como `_parse_ingest_args`) es **deliberado y verificado** (CA-14): con `>=` el comando se tragaría en silencio un argumento de más.
- **`_dispatch_contract_check(client) -> int` — nuevo.** Secuencia única, sin ramas de negocio:
  1. `clients_root = _clients_root()` (**se reutiliza**, no se duplica la convención); `contrato = clients_root / client / "input" / "contract_data.yaml"`.
  2. **Precondición 1:** `if not (clients_root / client).is_dir()` → **F-02** por stderr, `return 2`. **Sin invocar el motor.**
  3. **Precondición 2:** `if not contrato.is_file()` → **F-03** por stderr, `return 2`. **Sin invocar el motor.** Las dos preceden a `load_contract` porque el motor hace `open(path)` sin capturar `FileNotFoundError` (`contract.py:213`) y por D-22 **asume** que el YAML existe: el hueco es de la fachada, no del core.
  4. **Motor:** `contract = load_contract(contrato)` dentro de un `try`. Es la **única** llamada que valida.
  5. **Traducción del fallo:** `except ContractParseError as exc` → `print(str(exc), file=sys.stderr); return 3`; `except ContractSchemaError as exc` → ídem con `return 4`. `str(exc)` **sin una sola alteración**: ni prefijo, ni sufijo, ni reformato. Igual que `_dispatch_client_new` traduce `ClientNameError`/`TenantExistsError`.
  6. **Traducción del éxito:** **F-01** por stdout (dos líneas: veredicto + `len(contract.archivos)` y los nombres en el orden declarado), `return 0`.
- **Enganche en `main`.** Tercer bloque `parse → dispatch`, después de `client new` e `ingest`, **antes** del `print(_USAGE); return 1` final. El orden de despacho vigente **no cambia**: `contract check` no puede colisionar con `client`/`ingest` (primer token distinto).
- **`_USAGE`.** Se **agrega una tercera línea**, conservando íntegras las dos vigentes (indentación de continuación: 5 espacios, alineada con las existentes).

**Lo que NO hay.** Ni módulo `zeroleak/contract/`, ni excepción nueva, ni modelo nuevo, ni bandera, ni constante de mensaje del motor: los trece M-01 … M-13 **se muestran, no se escriben**.

**Asimetría deliberada de esta feature.** Es **pequeña en producción y grande en verificación**: 23 CA sobre ~15 líneas. En consecuencia, **11 de los 22 casos del bucle son candidatos a caracterización** (`(car?)`): el comportamiento ya existe —lo aporta el motor, la convención de `_clients_root()` o el `return 1` vigente de `main`— y el test lo **congela como regresión** en vez de arrancar código nuevo. Se marcan como tales y **no se fuerza un RED artificial** (L-13/L-14).

**Dependencias.** Ninguna nueva.

## Archivos Afectados
- `app/src/zeroleak/cli.py` — **modificar** (import del motor, `_parse_contract_check_args`, `_dispatch_contract_check`, tercer bloque de despacho en `main`, tercera línea de `_USAGE`). **Es el único archivo de producción tocado.**
- `app/tests/conftest.py` — **modificar** (fixture factory de tenant con contrato; fixture del árbol sintético de escenarios).
- `app/tests/test_cli_contract_check.py` — **crear** (los 21 tests unitarios de fachada).
- `app/tests/test_contract_multifile.py` — **modificar, y solo esto** (CA-21: retirar 2 aserciones de `test_load_contract_core_invocable_sin_cli`, conservar 3, actualizar docstring).
- `app/tests/integration/test_contract_check_e2e.py` — **crear** (CA-23, paso 11).
- **NO se toca:** `app/src/zeroleak/config/contract.py` ni ningún archivo bajo `app/src/zeroleak/config/` (CA-19).

## El orden de CA-21 no es negociable — decisión visible en el gate

`test_contract_multifile.py::test_load_contract_core_invocable_sin_cli` assertea hoy que `zeroleak.cli` **no** tiene símbolos `contract` y que `"contract" not in _USAGE.lower()`. **En el instante en que el Caso 1 introduce la fachada, ese test se pone rojo** — no al final de la feature, sino en el primer caso.

Por eso **TSK-04 (retiro de las dos aserciones) vive en el Caso 1**, ejecutada por el `tdd_tester` **junto con** el test nuevo del camino feliz y **antes** de que TSK-05 entregue el código. No es una limpieza de cierre: es la condición para que el bucle pueda quedar verde caso a caso. El retiro está **autorizado por el gate del paso 5** y **acotado por CA-21**; el **Caso 20** lo audita al final (conteo de funciones de test intacto, tres aserciones conservadas, suite verde).

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición: un solo responsable, un solo entregable, codificar ≠ testear (test-first: la tarea de test antecede a la de código). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`. **Estado** ∈ `no_implementada | implementada | cancelada_suspendida`; el **responsable es el único que actualiza el estado de su tarea** (Single Writer Rule). Todas se crean en `no_implementada`.
>
> `(car?)` = **candidata a caracterización** (L-13/L-14): puede quedar en verde de inmediato por efecto colateral del diseño (el motor ya lo cubre, la convención ya existe, el `return 1` de `main` ya está). Entonces el `tdd_tester` conserva el test como regresión, verifica su honestidad **inyectando temporalmente el defecto** (L-10) y el `tdd_coder` marca su tarea `cancelada_suspendida` **sin entregable**. No se fuerza un RED artificial.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Fixture factory `tenant_con_contrato(nombre, *, texto=None, archivos=None) -> Path` en `conftest.py`: crea `<clients_root>/<nombre>/input/` y escribe ahí el `contract_data.yaml` (texto crudo, o generado desde `archivos=[{nombre, columnas}]` con el mismo generador que `write_contract_yaml`); devuelve la ruta del tenant. Todo bajo `tmp_path`, vocabulario sintético (`clientes.csv`, `ventas.csv`; `cliente_id`, `correo`, `alta`, `venta_id`, `monto`), sin PII (C-01). | Fixture factory en `app/tests/conftest.py` | tdd_tester | implementada | CA-22 (andamiaje), CA-01 |
| TSK-02 | Fixture `escenario_contract_check` en `conftest.py`: un `clients_root` sintético con los **cinco** tenants que la feature necesita a la vez —válido (2 archivos), scaffoldeado (`contract_data:` sin cuerpo, texto **exacto** de `scaffold.py:_CONTRACT_DATA_YAML`), de esquema inválido, de YAML roto y sin contrato— más, en el tenant válido, un `data/bronze/clientes.csv` sintético y un `data/manifest.json`. Es el sujeto de las auditorías de solo-lectura y de frontera. | Fixture de escenario en `app/tests/conftest.py` | tdd_tester | implementada | CA-16 (andamiaje), CA-17 (andamiaje), CA-22 |
| TSK-03 | Test: sobre un tenant con contrato válido de 2 archivos (`clientes.csv`, `ventas.csv`), `main(["contract","check",C])` retorna **exactamente 0**, stdout no vacío y **stderr vacío**. | Test "camino-feliz-exit-0" | tdd_tester | implementada | CA-01 |
| TSK-04 | **CA-21 — retiro acotado.** En `test_contract_multifile.py::test_load_contract_core_invocable_sin_cli` retirar **exactamente dos** aserciones (`simbolos_contract == []` y `"contract" not in zeroleak_cli._USAGE.lower()`) y **conservar las tres** restantes (invocación directa → `isinstance(contrato, Contract)`; `list(signature.parameters) == ["path"]`; `signature.return_annotation is Contract`), con el docstring actualizado a la reinterpretación de CA-27 (*el core sigue siendo invocable sin CLI; ahora además tiene una*). **Nada más se toca de ese archivo.** | `test_contract_multifile.py` con el retiro acotado | tdd_tester | implementada | CA-21 |
| TSK-05 | Subcomando `contract check` en `cli.py`, camino feliz: import de `load_contract`/`ContractParseError`/`ContractSchemaError` desde `zeroleak.config`; `_parse_contract_check_args(argv)` (`len(argv) == 3`); `_dispatch_contract_check(client)` que resuelve la ruta con `_clients_root()`, invoca el motor e imprime el éxito por stdout con `return 0`; tercer bloque `parse → dispatch` en `main` antes del `_USAGE`. | El subcomando `contract check` (camino feliz) en `app/src/zeroleak/cli.py` | tdd_coder | implementada | CA-01 |
| TSK-06 | Test: stdout es **exactamente** F-01 — línea 1 `OK  contrato válido: <C> — <ruta>` (dos espacios tras `OK`, guion largo U+2014 rodeado de espacios, `<ruta> == str(clients_root/<C>/input/contract_data.yaml)`), línea 2 `    2 archivo(s) declarado(s): clientes.csv, ventas.csv` (4 espacios de indentación, orden declarado); + variante de **un solo** archivo → `1 archivo(s) declarado(s): <nombre>`. Igualdad exacta, no subcadena. | Test "F-01-texto-exacto-uno-y-dos-archivos" | tdd_tester | implementada | CA-02 |
| TSK-07 | Formato literal de **F-01** en `_dispatch_contract_check`: dos líneas, acentuadas (resolución O-1/O-2), recuento `len(contract.archivos)` y nombres unidos por `", "` en el orden declarado. | Formato F-01 en `app/src/zeroleak/cli.py` | tdd_coder | cancelada_suspendida (caracterización — sin entregable: TSK-05 (Caso 1) ya entregó el formato F-01 completo, verificado línea por línea en `_dispatch_contract_check`, `cli.py:142-146`) | CA-02 |
| TSK-08 | Test: con `<C>` inexistente bajo `clients_root` → retorna **exactamente 2**, stdout vacío, stderr **exactamente** `Tenant inexistente o incompleto: '<C>'` (**F-02**, con `{client!r}`); stderr **no contiene** `Traceback` ni `FileNotFoundError`. | Test "tenant-inexistente-F-02" | tdd_tester | implementada | CA-08 |
| TSK-09 | Precondición 1 en `_dispatch_contract_check`: si `clients_root/<C>` no es directorio → **F-02** por stderr y `return 2`, **antes** de cualquier acceso al motor. | Precondición de tenant en `app/src/zeroleak/cli.py` | tdd_coder | implementada | CA-08 |
| TSK-10 | Test: tenant que existe como directorio pero **sin** `input/contract_data.yaml` → retorna **exactamente 2** (el **mismo** código que TSK-08) y stderr es **exactamente** `El tenant '<C>' no tiene contrato: falta <ruta>` (**F-03**, ruta resuelta); sin `Traceback` ni `FileNotFoundError`; + aserción de que los stderr de F-02 y F-03 son **distintos entre sí** (mismo código, mensajes distintos). | Test "contrato-ausente-F-03-y-disyuncion-con-F-02" | tdd_tester | implementada | CA-09 |
| TSK-11 | Precondición 2 en `_dispatch_contract_check`: si el YAML no es archivo → **F-03** por stderr (con la ruta resuelta) y `return 2`. | Precondición de contrato en `app/src/zeroleak/cli.py` | tdd_coder | implementada | CA-09 |
| TSK-12 | Test: parcheando `load_contract` **en el namespace de `zeroleak.cli`** con un doble que registra llamadas, (a) tenant inexistente y (b) tenant sin contrato dejan el doble con **0 llamadas** y retornan `2` sin propagar excepción. **Guarda de no-vacuidad (L-17):** el mismo doble, sobre un tenant **con** contrato, registra **exactamente 1** llamada y con la ruta del YAML — el instrumento está vivo. | Test "precondicion-antes-del-motor-con-guarda" | tdd_tester | implementada | CA-10 |
| TSK-13 | `(car?)` Orden de la secuencia: las dos precondiciones se evalúan **antes** de `load_contract`; ajustar solo si el test lo exige (TSK-09/TSK-11 ya lo sitúan así). | Ajuste del orden en `app/src/zeroleak/cli.py` | tdd_coder | cancelada_suspendida (caracterización — sin entregable: TSK-09 y TSK-11 (Casos 3 y 4) ya sitúan ambas precondiciones antes de `load_contract`, verificado en `_dispatch_contract_check`, `cli.py:130-141`) | CA-10 |
| TSK-14 | Test (**propiedad verbatim**): para un tenant cuyo YAML viola el esquema, se compara el **mismo archivo** por dos caminos —`str(exc)` capturado llamando `load_contract(ruta)` **directo**, y el stderr del comando—: `stderr.strip() == str(exc)` (igualdad exacta), `stdout == ""`, exit **4**. | Test "schema-verbatim-exit-4" | tdd_tester | no_implementada | CA-03 |
| TSK-15 | Rama `except ContractSchemaError` en `_dispatch_contract_check`: `str(exc)` por stderr **sin alteración alguna** (ni prefijo, ni sufijo, ni reformato) y `return 4`; stdout intacto. | Rama de esquema (exit 4) en `app/src/zeroleak/cli.py` | tdd_coder | no_implementada | CA-03 |
| TSK-16 | `(car?)` Test (**mensaje concreto**): YAML donde `archivos[1]` (`ventas.csv`) declara `columnas: []` → stderr **exactamente** `archivo[1] 'ventas.csv': la lista de columnas no puede estar vacía` (**M-07**), verificado por **igualdad exacta contra la constante congelada** `_MENSAJE_COLUMNAS_VACIA` con su localizador D-25a (importada del motor, **no** recopiada como literal), exit `4`. Prueba que el texto del motor llega **entero** a la terminal, no solo "algo parecido". | Test "M-07-exacto-por-la-fachada" | tdd_tester | no_implementada | CA-04 |
| TSK-17 | Test: `contract_data.yaml` sintácticamente inválido → retorna **exactamente 3**, stdout vacío, stderr **igual por igualdad exacta** a `str(exc)` del `ContractParseError` que lanza `load_contract` sobre el mismo archivo (**M-12**, con el detalle multilínea de PyYAML —líneas, columnas, ruta— **intacto**). | Test "parse-verbatim-exit-3" | tdd_tester | no_implementada | CA-05 |
| TSK-18 | Rama `except ContractParseError` en `_dispatch_contract_check`: `str(exc)` por stderr sin alteración y `return 3`. | Rama de parseo (exit 3) en `app/src/zeroleak/cli.py` | tdd_coder | no_implementada | CA-05 |
| TSK-19 | `(car?)` Test (**variante A**): con dos tenants —YAML roto y esquema inválido— los exit codes son `3` y `4`: **distintos entre sí** y **distintos de `0`, `1` y `2`**; y ninguno de los dos stderr lleva prefijo, sufijo ni adorno de la fachada (ambos siguen cumpliendo la igualdad exacta con el mensaje del motor). Congela el mecanismo de distinción resuelto en el gate del paso 5. | Test "distincion-parse-schema-variante-A" | tdd_tester | no_implementada | CA-06 |
| TSK-20 | `(car?)` Test (**primera corrida, M-01**): tenant cuyo `input/contract_data.yaml` tiene el contenido **exacto** que deja `client new` (`scaffold.py:_CONTRACT_DATA_YAML`, raíz sin cuerpo) → exit `4` y stderr **exactamente** `_MENSAJE_RAIZ_INVALIDA.format(cuerpo=None)` (**M-01**). Además: el stderr **no contiene ninguna cadena propia de la fachada** (`OK`, `Tenant inexistente`, `no tiene contrato`) — evidencia de que **no hay rama especial** y de que es el motor quien cubre el caso. **Sin tarea de código: por diseño, este caso no debe añadir ni una línea a `cli.py`.** | Test "primera-corrida-M-01-sin-rama-especial" | tdd_tester | no_implementada | CA-07 |
| TSK-21 | Test: `zeroleak.cli._USAGE` es **exactamente** las tres líneas `uso: zlk client new <NOMBRE_CLIENTE>` / `     zlk ingest <CLIENTE> <ruta>...` / `     zlk contract check <CLIENTE>`: conserva **íntegras** las dos vigentes y agrega **una sola** línea nueva (igualdad exacta del texto completo, no subcadena). | Test "usage-tres-lineas-exactas" | tdd_tester | no_implementada | CA-15 |
| TSK-22 | Agregar la tercera línea a `_USAGE` en `cli.py` (`     zlk contract check <CLIENTE>`, indentación de continuación alineada con las vigentes), sin tocar las dos existentes. | `_USAGE` de tres líneas en `app/src/zeroleak/cli.py` | tdd_coder | no_implementada | CA-15 |
| TSK-23 | `(car?)` Test parametrizado: `["contract"]`, `["contract","check"]`, `["contract","foo"]`, `["contract","check",C,"de_mas"]` y `[]` → cada uno retorna **exactamente 1**, stdout vacío, stderr contiene `uso: zlk` **y** `contract check`, y **no** levanta excepción. | Test "argv-mal-formado-usage-exit-1" | tdd_tester | no_implementada | CA-13 |
| TSK-24 | `(car?)` Test (**`len(argv) == 3` exacto**): con `load_contract` parcheado en el namespace de `zeroleak.cli` como doble contador, `main(["contract","check",C,"extra"])` sobre un tenant **con contrato válido** deja el doble con **0 llamadas** y retorna `1` con `_USAGE` en stderr — el argumento de más **no se traga en silencio**. **Guarda de no-vacuidad:** la invocación de 3 argumentos con el mismo doble registra **1** llamada. | Test "len-argv-exacto-no-traga-extra" | tdd_tester | no_implementada | CA-14 |
| TSK-25 | `(car?)` Test: con `root_a` (contiene `<C>` con contrato válido) y `root_b` (vacía), el **mismo** `main(["contract","check",C])` retorna `0` con `ZEROLEAK_CLIENTS_ROOT=root_a` y `2` con `=root_b`; en el caso de éxito la ruta impresa en F-01 cae **bajo `root_a`**. | Test "env-clients-root-manda" | tdd_tester | no_implementada | CA-11 |
| TSK-26 | `(car?)` Test: con `ZEROLEAK_CLIENTS_ROOT` **no definida** (`monkeypatch.delenv(..., raising=False)`) y el cwd fijado (`monkeypatch.chdir`) en un `tmp_path` que contiene `clients/<C>/input/contract_data.yaml` válido → retorna `0` y la ruta impresa en F-01 es `<cwd>/clients/<C>/input/contract_data.yaml`. | Test "fallback-clients-relativo-al-cwd" | tdd_tester | no_implementada | CA-12 |
| TSK-27 | `(car?)` Test (**fachada delgada**): parcheando `load_contract` en el namespace de `zeroleak.cli` para que lance `ContractSchemaError("mensaje sintético de prueba")`, el comando sobre un tenant con contrato **válido en disco** imprime por stderr **exactamente** `mensaje sintético de prueba` y retorna `4` — el veredicto y el texto vienen **solo** del motor, la fachada no revalida ni contradice lo que hay en disco. Análogamente, con el doble lanzando `ContractParseError("…")` → exit `3`. | Test "fachada-delgada-el-motor-manda" | tdd_tester | no_implementada | CA-20 |
| TSK-28 | Test (**solo lectura**): foto de **todo** el árbol `clients_root` del escenario (ruta relativa → `(tamaño, mtime_ns, sha256)`); se ejecuta el comando sobre **todos** los casos (válido, scaffoldeado, esquema inválido, YAML roto, sin contrato, tenant fantasma y argv mal formado); la foto posterior es **idéntica**: 0 creados, 0 borrados, 0 con contenido o `mtime_ns` alterado. **Guarda de no-vacuidad:** `len(foto_antes) >= 1` **antes** de comparar — dos fotos vacías no probarían nada. | Test "solo-lectura-foto-del-arbol" | tdd_tester | no_implementada | CA-16 |
| TSK-29 | Test (**frontera D-21**): con un audit hook de CPython (`sys.addaudithook`, evento `open`) activo durante `contract check` sobre el tenant válido —que **sí** tiene `data/bronze/clientes.csv` y `manifest.json`—: (1) **guarda de no-vacuidad (L-17) primero** — el espía observó ≥ 1 apertura **y** entre ellas está `contract_data.yaml`; (2) recién entonces la ausencia: **ninguna** ruta observada cae bajo `data/bronze|silver|gold`, termina en `.csv` ni es `manifest.json`; (3) el comando retornó `0`. | Test "frontera-D-21-audit-hook-con-guarda" | tdd_tester | no_implementada | CA-17 |
| TSK-30 | Test (**segundo instrumento, independiente**): con `mock.patch.object(zeroleak.config.contract, "open", espia, create=True)` (**no** `builtins.open`: L-17, quedaría mudo), el comando sobre el tenant válido hace que el espía registre **exactamente 1** apertura, y que sea el `contract_data.yaml` del tenant; el comando sigue retornando `0` con el espía puesto. **Guarda de no-vacuidad:** `espia.vistos != []` antes de afirmar el "exactamente 1". | Test "segundo-instrumento-open-del-motor" | tdd_tester | no_implementada | CA-18 |
| TSK-31 | Test/auditoría de la modificación acotada (CA-21): `test_contract_multifile.py` conserva **el mismo número de funciones de test** que en `main` (conteo vía AST del archivo, contrastado con la versión de `main`), `test_load_contract_core_invocable_sin_cli` conserva **sus tres** aserciones, y el diff de la rama sobre `app/tests/` **no elimina ni debilita** ninguna otra aserción ni test. | Test "auditoria-modificacion-acotada-de-la-suite" | tdd_tester | no_implementada | CA-21 |
| TSK-32 | Test (**cumplimiento C-01**): todos los tenants, YAMLs y CSV de los tests nuevos se construyen en `tmp_path`; ningún test nuevo lee `clients/` del repositorio ni ruta alguna fuera de `tmp_path`; los nombres de columna de los fixtures pertenecen a la **lista blanca sintética** (`cliente_id`, `correo`, `alta`, `venta_id`, `monto`), sin PII real. | Test "fixtures-sinteticos-sin-pii" | tdd_tester | no_implementada | CA-22 |
| ~~TSK-33~~ | **RETIRADA en el gate del paso 9 (2026-07-17).** Era un test que consultaba `git diff --exit-code main -- app/src/zeroleak/config/`. **Motivo del retiro:** CA-19 es una condición **de esta rama**, no una invariante del código. Como test mergeado se convertiría en un cerrojo permanente ("nadie puede volver a tocar `config/` nunca"), que el primer feature legítimo que evolucione el motor (`load_data`) encontraría en rojo sin contexto; además dependería de `git` y de la ref `main`, fallando en cualquier clone que no las tenga. **CA-19 se verifica igual, en su lugar natural:** `spec_verifier` (paso 12) lo audita contra el diff real de la rama, y el humano lo confirma en el gate del paso 13. Sin test en la suite. | — (sin entregable) | — | cancelada_suspendida | CA-19 |
| TSK-34 | Refactor manteniendo verde: constantes para **F-01/F-02/F-03** y para los exit codes con nombre (un único sitio donde vive cada texto y cada código congelado), docstrings con referencia a CA/F/HU, tipado y estilo consistentes con `_dispatch_client_new`/`_dispatch_ingest`. **Sin cambiar ni un carácter observable** de stdout/stderr ni ningún exit code. | `app/src/zeroleak/cli.py` refactorizado | tdd_refactor | no_implementada | CA-01 … CA-22 (calidad) |
| TSK-35 | Prueba de integración **end-to-end** en un solo test, invocando `main(argv)` **en proceso** sobre un `clients_root` sintético: (1) `main(["client","new",C])` → `0`; (2) `main(["contract","check",C])` sobre el tenant recién creado → `4` con **M-01** por stderr; (3) se **edita a mano** el `contract_data.yaml` dejándolo válido → `0` con F-01; (4) se edita dejándolo inválido por esquema → `4` con el mensaje del motor verbatim. Cierra el lazo real: `client new` → editar → preguntar. | `app/tests/integration/test_contract_check_e2e.py` | integration_tester | no_implementada | CA-23 |

## Dependencias y Contratos
- **Consume (sin modificar):** `zeroleak.config` — `load_contract(path) -> Contract`, `Contract`, `ContractParseError`, `ContractSchemaError`, y el catálogo **M-01 … M-13** congelado por `contract_multifile` (PR #4). Los tests de CA-04/CA-07 importan las constantes `_MENSAJE_*` del motor **en vez de recopiar el literal**: si el motor cambiara un texto, la regresión aparece en el motor, no aquí.
- **Consume:** `cli._clients_root()` (convención `ZEROLEAK_CLIENTS_ROOT` → `./clients`) y `scaffold.py:_CONTRACT_DATA_YAML` (origen del caso M-01 de primera corrida).
- **Produce:** una superficie CLI nueva —`zlk contract check <CLIENTE>`— con exit codes `{0,1,2,3,4}` y los mensajes **F-01 … F-03**. **Ningún artefacto en disco:** el comando es de solo lectura (CA-16).
- **Evoluciona:** `_USAGE` (dos líneas → tres). Único consumidor vigente que lo asserteaba: la aserción que CA-21 retira (verificado en el paso 6, punto O-4 del gate).
- **Deuda declarada (O-3):** el texto de **F-02** está duplicado literalmente del `TenantNotFoundError` de `ingest` (`ingest/core.py:125`), **por decisión del gate**. Si una de las dos redacciones cambia, la otra **no** se entera: el riesgo se acepta a cambio de no acoplar ejes (D-21).
- **Frontera (D-21):** no se abre, lee ni referencia nada bajo `data/` (CA-17, CA-18); no se emparejan los `nombre` del contrato con archivos físicos; no se validan `business_rules.yaml`, `finance.yaml` ni el Maestro de Sectores.
- **Deriva de:** D-22 (diagnostica, no repara), D-23c (fail-fast heredado del motor, sin agregación), C-01 (Datos en Bóveda).
- **Pendiente registrado al cierre (gate del paso 5):** anotar en `900_persistence/decisions.md` la decisión que **deroga D-23d** (core-only) y **reinterpreta CA-27**.

## Estrategia de Test
- **Unit (`app/tests/test_cli_contract_check.py`):** camino feliz (exit 0 y F-01 exacto, con 1 y con 2 archivos); precondiciones (F-02, F-03, mismo código y mensajes distintos, motor no invocado con guarda de no-vacuidad); traducción del motor (esquema verbatim, M-07 exacto contra la constante congelada, parse verbatim, distinción 3/4 sin adornos); primera corrida M-01 sin rama especial; invocación (`_USAGE` de tres líneas exactas, cinco formas mal formadas, `len(argv)==3` con doble contador); convención (`ZEROLEAK_CLIENTS_ROOT` manda, fallback `./clients`); fachada delgada con dobles que lanzan excepciones sintéticas; transversales (solo lectura con foto sha256/mtime, frontera D-21 con audit hook, segundo instrumento sobre el `open` del motor, auditoría de CA-21, C-01, core intacto vs `main`).
- **Integración (`app/tests/integration/test_contract_check_e2e.py`, paso 11):** **sí aplica** —a diferencia de `contract_multifile`, core-only— y es **exactamente un test** (CA-23): la secuencia real `client new` → `contract check` (M-01) → editar a mano → `contract check` (F-01) → romper el esquema → `contract check` (exit 4), con `main(argv)` **en proceso** tal como lo pide la spec. **No** por subprocess: CA-23 lo fija así, y la costura "consola instalada → proceso" ya está cubierta por `test_ingest_e2e.py` / `test_client_new_e2e.py` para el mismo `main`.
- **Fixtures / datos de prueba:** **sintéticos** (C-01), siempre en `tmp_path`, vía `tenant_con_contrato` (TSK-01) y `escenario_contract_check` (TSK-02). Vocabulario: `clientes.csv`, `ventas.csv`; columnas `cliente_id`, `correo`, `alta`, `venta_id`, `monto`. **Ningún** test nuevo lee `clients/` del repo ni ninguna ruta fuera de `tmp_path` — esta feature **no tiene** la excepción de archivo versionado que sí tenía CA-22 de `contract_multifile`.

## Casos de Test (bucle TDD)
Ordenados de simple a complejo: **camino feliz → precondiciones → traducción del motor → invocación → convención → transversales de auditoría**. Deben coincidir con `stages.tdd.cases[]` del `state.json` de la feature. Cada caso agrupa sus tareas de test y de código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | Contrato válido de 2 archivos → exit `0`, stdout no vacío, stderr vacío. **Incluye el retiro de las 2 aserciones de CA-21**, que se pone rojo en cuanto nace la fachada. | TSK-01, TSK-02, TSK-03, TSK-04, TSK-05 | CA-01, CA-21 |
| 2 | stdout es **exactamente** F-01: dos líneas, acentuadas, ruta completa, recuento y nombres en orden; con 1 archivo → `1 archivo(s) declarado(s): …`. | TSK-06, TSK-07 | CA-02 |
| 3 | Tenant inexistente → exit `2`, stdout vacío, stderr **exactamente** F-02, sin `Traceback` ni `FileNotFoundError`. | TSK-08, TSK-09 | CA-08 |
| 4 | Tenant sin `input/contract_data.yaml` → exit `2` (el **mismo** que el Caso 3), stderr **exactamente** F-03; y F-02 ≠ F-03: mismo código, mensajes distintos. | TSK-10, TSK-11 | CA-09 |
| 5 | Doble de `load_contract` en el namespace de `zeroleak.cli`: **0 llamadas** en los dos casos de precondición; **1 llamada** en el tenant con contrato (guarda de no-vacuidad, L-17). | TSK-12, TSK-13 | CA-10 |
| 6 | YAML que viola el esquema → `stderr.strip() == str(exc)` del `load_contract` directo (igualdad exacta), stdout vacío, exit `4`. | TSK-14, TSK-15 | CA-03 |
| 7 | `archivos[1] 'ventas.csv'` con `columnas: []` → stderr **exactamente** **M-07** (igualdad exacta contra `_MENSAJE_COLUMNAS_VACIA` con su localizador), exit `4`. | TSK-16 | CA-04 |
| 8 | YAML sintácticamente roto → exit `3`, stdout vacío, stderr == `str(exc)` del `ContractParseError` (**M-12**, detalle de PyYAML intacto). | TSK-17, TSK-18 | CA-05 |
| 9 | Variante A: parse `3` y esquema `4` — distintos entre sí y de `0/1/2`; ninguno lleva prefijo ni adorno de la fachada. | TSK-19 | CA-06 |
| 10 | Contrato recién scaffoldeado por `client new` → exit `4` con **M-01** exacto, y stderr **sin ninguna cadena de la fachada**: el motor lo cubre, no hay rama especial. | TSK-20 | CA-07 |
| 11 | `_USAGE` es exactamente tres líneas: las dos vigentes íntegras + **una** nueva. | TSK-21, TSK-22 | CA-15 |
| 12 | Las cinco invocaciones mal formadas → exit `1`, stdout vacío, `uso: zlk` y `contract check` en stderr, sin excepción. | TSK-23 | CA-13 |
| 13 | `contract check <C> extra` sobre tenant válido → doble con **0 llamadas** y exit `1`; con 3 argumentos, **1** llamada (guarda). | TSK-24 | CA-14 |
| 14 | `ZEROLEAK_CLIENTS_ROOT` manda: `root_a` → `0` (ruta de F-01 bajo `root_a`), `root_b` → `2`, con el mismo argv. | TSK-25 | CA-11 |
| 15 | Sin la variable y con cwd en `tmp_path` → `0`, con la ruta `<cwd>/clients/<C>/input/contract_data.yaml` en F-01. | TSK-26 | CA-12 |
| 16 | Doble que lanza `ContractSchemaError("mensaje sintético de prueba")` sobre un contrato **válido en disco** → stderr exacto y exit `4`; con `ContractParseError` → `3`. La fachada no revalida. | TSK-27 | CA-20 |
| 17 | Foto `(tamaño, mtime_ns, sha256)` de todo el árbol antes/después de correr **todos** los casos → idéntica; guarda `len(foto_antes) >= 1`. | TSK-28, TSK-02 | CA-16 |
| 18 | Audit hook sobre `open`: guarda de no-vacuidad primero (≥ 1 apertura, y el YAML entre ellas); luego, ninguna ruta de bronze/silver/gold, `.csv` ni `manifest.json`; exit `0`. | TSK-29, TSK-02 | CA-17 |
| 19 | Segundo instrumento (`open` parcheado en `zeroleak.config.contract`, no en `builtins`): **exactamente 1** apertura, la del YAML del tenant; exit `0` con el espía puesto. | TSK-30 | CA-18 |
| 20 | Auditoría de CA-21: mismo conteo de funciones de test que en `main`, tres aserciones conservadas, ninguna otra cobertura reducida, suite verde (111 vigentes + los nuevos). | TSK-31 | CA-21 |
| 21 | Todos los fixtures nuevos son sintéticos, viven en `tmp_path` y usan la lista blanca de columnas; ninguno toca `clients/` del repo. | TSK-32 | CA-22 |
| ~~22~~ | **CASO RETIRADO en el gate del paso 9.** CA-19 (core intacto) **no** se verifica con un test en la suite: lo audita `spec_verifier` en el paso 12 contra el diff real de la rama, y el humano lo confirma en el gate del paso 13. Ver TSK-33 para el motivo. | ~~TSK-33~~ | CA-19 (fuera del bucle TDD) |

> **Refactor:** TSK-34 (`tdd_refactor`) se ejecuta manteniendo verde, típicamente tras cerrar el Caso 16 (cuando ya están las tres ramas de traducción y los cinco exit codes). **No** puede cambiar ni un carácter observable: los Casos 2, 3, 4, 6, 7, 8, 10 y 11 son su red de seguridad.
>
> **Integración (paso 11):** TSK-35 (`integration_tester`), **fuera** del bucle TDD y en contexto fresco, tras cerrar los 22 casos.
>
> **Nota sobre caracterización (L-13/L-14).** Marcados `(car?)`: TSK-13, TSK-16, TSK-19, TSK-20, TSK-23, TSK-24, TSK-25, TSK-26, TSK-27 (Casos 5, 7, 9, 10, 12, 13, 14, 15, 16). Es **la mitad del bucle**, y es esperable: el comportamiento ya lo aportan el motor (M-01 … M-13, exit 4 vía TSK-15), la convención `_clients_root()` ya vigente y el `print(_USAGE); return 1` que `main` ya hace hoy con cualquier argv desconocido. **No se fuerza un RED artificial**: el `tdd_tester` conserva el test como regresión, verifica su honestidad **inyectando temporalmente el defecto** (L-10) y el `tdd_coder` marca su tarea `cancelada_suspendida` **sin entregable**. Los casos que **sí** esperan código real: 1 (la fachada), 2 (formato F-01), 3 y 4 (las precondiciones — el hueco real del motor), 6 y 8 (las dos ramas de traducción) y 11 (`_USAGE`).

## Verificación de Cobertura (todo `CA-xx` tiene ≥ 1 `TSK-xx`; ninguna tarea huérfana)
| CA | Cubierto por |
|---|---|
| CA-01 | TSK-01, TSK-03, TSK-05 |
| CA-02 | TSK-06, TSK-07 |
| CA-03 | TSK-14, TSK-15 |
| CA-04 | TSK-16 |
| CA-05 | TSK-17, TSK-18 |
| CA-06 | TSK-19 |
| CA-07 | TSK-20 |
| CA-08 | TSK-08, TSK-09 |
| CA-09 | TSK-10, TSK-11 |
| CA-10 | TSK-12, TSK-13 |
| CA-11 | TSK-25 |
| CA-12 | TSK-26 |
| CA-13 | TSK-23 |
| CA-14 | TSK-24 |
| CA-15 | TSK-21, TSK-22 |
| CA-16 | TSK-02, TSK-28 |
| CA-17 | TSK-02, TSK-29 |
| CA-18 | TSK-30 |
| CA-19 | *(sin TSK: verificado por `spec_verifier` en el paso 12 y por el humano en el paso 13 — gate del paso 9, TSK-33 retirada)* |
| CA-20 | TSK-27 |
| CA-21 | TSK-04, TSK-31 |
| CA-22 | TSK-01, TSK-02, TSK-32 |
| CA-23 | TSK-35 |
| todos | TSK-34 (calidad, manteniendo verde) |

**34 tareas vivas (+1 retirada en el gate) · 21 casos de bucle + 1 prueba de integración · 23/23 CA cubiertos (CA-19 fuera del bucle, ver TSK-33) · 0 tareas huérfanas.**

## Resultado del Gate (paso 9) — 2026-07-17

**Plan APROBADO con un cambio.**

- **Punto 2 — RESUELTO EN CONTRA del plan:** se **retira TSK-33** (y con ella el Caso 22). CA-19 no se verifica con un
  test en la suite. Motivo: es una condición **de esta rama**, no una invariante del código; mergeada se volvería un
  cerrojo permanente sobre `config/` que el primer feature legítimo que evolucione el motor (`load_data`) encontraría
  en rojo sin contexto, además de depender de `git` y de la ref `main`. **CA-19 se verifica en su lugar natural:**
  auditoría de `spec_verifier` contra el diff real (paso 12) + gate humano (paso 13).
- **Puntos 1, 3, 4, 5, 6, 7, 8 — ACEPTADOS a favor del plan tal como está escrito:** CA-21 se ejecuta en el Caso 1
  (con la auditoría del Caso 20 al cierre); los 9 casos de caracterización se conservan sin fusionar (su valor es
  impedir que aparezca lógica en la fachada, no dirigir código); TSK-05 se mantiene como entregable cohesivo;
  CA-23 corre en proceso y la evidencia de terminal real se obtiene en el paso 13; la duplicación de F-02 y la
  acentuación de F-01 quedan anotadas como riesgos conocidos; se acepta el audit hook con CA-18 como segundo
  instrumento independiente.

## Riesgos Técnicos / Decisiones a Validar en el Gate (paso 9)

1. **CA-21 se ejecuta en el Caso 1, no al cierre — es lo más frágil del plan.** El test `test_load_contract_core_invocable_sin_cli` se pone **rojo en el instante** en que TSK-05 introduce el import y el subcomando. Por eso TSK-04 (retiro de las dos aserciones) va **dentro del Caso 1**, hecha por el `tdd_tester` **antes** del código. **A validar:** que el humano acepta que la única modificación autorizada de la suite vigente ocurra en el **primer** caso del bucle (y no al final, donde sería más visible), a cambio de que el bucle quede verde caso a caso. El Caso 20 la audita al cierre. **Riesgo residual:** entre el Caso 1 y el Caso 20, el retiro solo está custodiado por la disciplina del bucle.

2. ~~**CA-19 (core intacto) como test automatizado que consulta `git`.**~~ **→ RESUELTO EN EL GATE: TSK-33 retirada.** El planteamiento original era un test con `git diff --exit-code main -- app/src/zeroleak/config/` + `sha256` contra `git show main:…`, el **único test del proyecto que dependería del estado del repositorio**. El humano lo retiró: CA-19 es una condición de esta rama, no una invariante del código, y como test mergeado se convertiría en un cerrojo permanente sobre `config/`. Se verifica en el paso 12 (`spec_verifier`, contra el diff real) y en el paso 13 (gate humano). Ver la sección "Resultado del Gate".

3. **La mitad del bucle son caracterizaciones (9 tareas `(car?)`, 9 casos).** Es consecuencia directa de la asimetría de la feature: ~15 líneas de producción contra 23 CA. **A validar:** que se acepta un bucle donde 9 de 22 casos previsiblemente arranquen en verde y se conserven como regresión (con la honestidad verificada por inyección/reversión, L-10), en vez de fusionarlos o recortarlos. Recortarlos sería tentador y equivocado: los `(car?)` de esta feature son precisamente los que prueban que **no hay lógica propia en la fachada** (CA-07, CA-20) — su valor no es dirigir código, es **impedir** que aparezca.

4. **Granularidad de TSK-05 (el "camino feliz" es parser + dispatch + wiring).** Con la regla de un solo entregable, lo estricto sería partirlo en tres; pero un parser sin enganche en `main` no puede poner verde ningún test, así que el Caso 1 quedaría sin RED→GREEN legítimo. El plan trata "el subcomando `contract check` operativo (camino feliz)" como **un** entregable cohesivo — mismo criterio que TSK-05 de `contract_multifile` (modelo + `load_contract` + reexport). **A confirmar** que la granularidad es la deseada.

5. **CA-23 corre en proceso, no por subprocess** — a diferencia de `test_ingest_e2e.py` / `test_client_new_e2e.py`, que invocan el `zlk` instalado. Lo fija la spec ("invocando `main(argv)` en proceso"), y la costura consola→proceso ya está cubierta por las e2e vigentes sobre el mismo `main`. **Consecuencia a mirar de frente:** ningún test de esta feature ejercita `zlk contract check` **desde una terminal real**. Si el humano quiere esa evidencia, el lugar natural es el **paso 13 (`human_test`)** — o ampliar TSK-35 con una invocación por subprocess (fuera de lo que CA-23 pide).

6. **F-02 duplica el texto de `ingest` (deuda declarada, O-3).** Los tests fijarán el literal **dos veces** en el proyecto (aquí y en `test_cli_ingest.py`), sin ningún mecanismo que los mantenga sincronizados. Es la decisión del gate del paso 7 y el plan la honra; **el humano debe notar** que un cambio futuro de redacción en `ingest` dejará las dos fachadas hablando distinto sin que nada se ponga rojo.

7. **F-01 acentuada: el spike no es la referencia.** El prototipo del notebook imprimió `OK  contrato valido:` (sin acento). La forma **normativa** es la acentuada (`válido`), fijada por la spec y ratificada en el gate. **Riesgo operativo:** copiar del spike al implementar TSK-07 introduce el bug silenciosamente; TSK-06 (igualdad exacta) es la única red. Se anota aquí para que el `tdd_coder` no "corrija" el acento hacia el spike.

8. **`sys.addaudithook` es irreversible dentro del proceso (CA-17/TSK-29).** Un audit hook no se puede desinstalar y ve **todas** las aperturas del intérprete durante lo que reste de la sesión de pytest. El test debe activar el filtro solo durante la invocación (bandera de captura) para no contaminar ni ralentizar el resto de la suite, y el orden de ejecución de los tests no debería afectarlo. **A confirmar** que se acepta el instrumento; CA-18 (TSK-30, `mock.patch.object` sobre el `open` del motor, sí reversible) existe justamente como **segundo instrumento independiente** por si el primero resulta problemático.

---

**Siguiente paso:** **gate humano (paso 9)** para aprobar/rechazar este plan. **No** se arranca el bucle TDD (paso 10: `tdd_tester → tdd_coder → tdd_refactor`) hasta la aprobación; el paso 11 (`integration_tester`, TSK-35) **sí aplica** en esta feature.
