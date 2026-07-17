# Feature Contract — contract_check

> Artefacto **a nivel feature**, creado por la **sesión principal** (humano + Claude Code) en el paso 2 del flujo.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de escribir la definición**.
> **Una feature = una construcción completa** (Opción A, sin bandas): un solo ciclo SDD+TDD la lleva a "terminado".

## Estrella Polar
Cerrar el **bucle de retroalimentación** sobre el Contrato de Datos: darle al humano que edita a mano
`clients/<CLIENTE>/input/contract_data.yaml` una forma de **preguntarle al motor si su YAML quedó bien, cuando él
quiera**, mediante una fachada CLI nueva —`zlk contract check <CLIENTE>`— que responde **OK** o el **error exacto y
accionable** que el motor ya sabe producir. Hoy `load_contract` existe, está verificado y habla trece mensajes
cuidadosamente congelados (M-01…M-13), pero **nadie lo invoca**: el CLI solo tiene `client new` e `ingest`, e
`ingest` es archivador notarial que no parsea contenido (D-21). El resultado es que el humano edita el contrato **a
ciegas** hasta que una etapa futura (`load_data`) lo cargue. Esta feature no construye motor nuevo: **conecta el
motor que ya existe con la persona que lo necesita**.

## Definición de "Terminado"
Condiciones que deben cumplirse para considerar la feature **terminada** (comportamiento end-to-end completo):
- Existe el subcomando **`zlk contract check <CLIENTE>`**, que resuelve el contrato del tenant en
  `<clients_root>/<CLIENTE>/input/contract_data.yaml` (con `clients_root` desde `ZEROLEAK_CLIENTS_ROOT`, o
  `./clients` por defecto — **la misma convención vigente** de `client new` e `ingest`, `cli.py:_clients_root`) y
  lo valida invocando **`load_contract`**.
- **Contrato válido → señal de éxito clara** por stdout y **exit code 0**. La señal confirma lo que se validó (que
  el humano sepa que el motor leyó *su* contrato y no otra cosa); la forma exacta la fija la spec.
- **Contrato inválido → el mensaje del motor tal cual, sin reescribir**, por stderr, con exit code distinto de 0.
  Los textos M-01…M-13 fueron congelados carácter a carácter en `contract_multifile` y **verificados por igualdad
  exacta**: esta feature los **muestra**, no los redacta, no los adorna ni los traduce. Un cambio de redacción aquí
  sería una regresión silenciosa de esa spec.
- **`ContractParseError` y `ContractSchemaError` se distinguen** en la salida (son dos fallas de naturaleza
  distinta: el YAML no se puede leer vs. el YAML se lee pero no cumple el esquema). Cómo se distinguen —mismo exit
  code con prefijo distinto, o exit codes distintos— lo fija la spec.
- **Hueco real del motor cubierto por la fachada:** `load_contract` hace `open(path)` **sin capturar
  `FileNotFoundError`** (`contract.py:213`), y su frontera D-21 dice que es la única ruta que abre. Un tenant
  inexistente, o uno sin `input/contract_data.yaml`, hoy produciría un **traceback crudo de infraestructura**. La
  fachada debe traducir eso a un **mensaje de dominio claro** y su propio exit code, **sin tocar el core**: el
  motor sigue asumiendo que el YAML existe (D-22), y es la CLI quien comprueba la precondición antes de invocarlo
  —exactamente el patrón que `ingest` ya usa con `TenantNotFoundError` (precondición global de tenant, CA-08 de
  `ingest`).
- **Primera corrida realista contemplada:** un tenant recién creado por `client new` trae un `contract_data.yaml`
  con la raíz `contract_data:` presente y **sin cuerpo** (`scaffold.py:_CONTRACT_DATA_YAML`). Ese caso **no es un
  error de la feature**: produce **M-01** (el fix de T-56), y es precisamente la señal útil "tu contrato está
  vacío, complétalo". La feature debe tratarlo como un camino de primera clase, no como un borde.
- **El core no se modifica.** `load_contract`, `Contract`, `ArchivoContrato`, `Columna`, `TipoDato`,
  `ContractParseError` y `ContractSchemaError` se **consumen** desde `zeroleak.config` tal como están exportados
  hoy. Si durante la construcción aparece la tentación de cambiar el core, es señal de que algo se salió del
  alcance y debe subir al gate humano.
- **Fachada delgada, como las dos que ya existen:** el CLI despacha y traduce excepciones de dominio a exit codes;
  **no** tiene lógica de negocio propia (el mismo criterio de `client_scaffold`, CA-02/CA-03, y de `ingest`,
  CA-12).
- **Sin regresiones, con una excepción declarada y aprobada:** la suite completa queda en verde. Los 111 tests
  vigentes siguen pasando **salvo dos aserciones** de `test_load_contract_core_invocable_sin_cli`
  (`test_contract_multifile.py:1635`), que esta feature rompe **por diseño**.
  > **Corrección del paso 5 (gate humano).** La versión original de este contrato afirmaba que la feature "no toca
  > `test_contract_multifile.py`". **Era falso**, y el spike lo destapó: ese test materializa CA-27/D-23d y
  > assertea la **ausencia** de fachada CLI — `simbolos_contract == []` y `"contract" not in _USAGE.lower()` —,
  > exactamente lo que el humano derogó en el paso 1. **Resolución del gate:** se **retiran esas dos aserciones**
  > y se **conservan las tres** restantes (invocación directa, parámetro `path`, anotación de retorno `Contract`),
  > que son el contenido real de CA-27 —*el core es invocable sin CLI*— y siguen siendo ciertas. CA-27 se
  > **reinterpreta, no se abandona**: el core no necesita la CLI; ahora además la tiene.
- **Seguro por diseño (C-01):** se desarrolla y prueba **exclusivamente** contra tenants y YAMLs **sintéticos** en
  `tmp_path`. El contrato describe **estructura**, no PII; `input/` es material versionable (§7), no datos reales
  del cliente. El comando **no lee ningún CSV** ni toca `data/`.

## Alcance
**In scope:**
- Subcomando `zlk contract check <CLIENTE>` en `app/src/zeroleak/cli.py`: parseo de argumentos, despacho y
  actualización de `_USAGE`.
- Resolución de la ruta del contrato del tenant por convención (`<clients_root>/<CLIENTE>/input/contract_data.yaml`),
  reutilizando `_clients_root()`.
- Precondición de existencia (tenant y/o archivo de contrato ausente) traducida a mensaje de dominio + exit code,
  **antes** de invocar `load_contract`.
- Reporte de éxito por stdout (exit 0) y de error por stderr (exit ≠ 0), propagando el mensaje del motor **sin
  alterarlo**.
- Distinción observable entre `ContractParseError` y `ContractSchemaError`.
- Tests unitarios de la fachada (invocando `main(argv)` como ya hacen `test_cli_client_new.py` /
  `test_cli_ingest.py`) y **prueba de integración end-to-end** con tenant sintético: `client new` → editar el YAML
  → `contract check`, cubriendo camino feliz, contrato vacío recién scaffoldeado (M-01) y al menos un contrato
  inválido.

**Out of scope (nunca, o en otra feature):**
- **Modificar el motor** `config/contract.py`: ni la firma de `load_contract`, ni los modelos, ni las excepciones,
  ni **una sola letra** de los mensajes M-01…M-13.
- **Escribir, corregir, autocompletar o crear** el `contract_data.yaml`. El comando **diagnostica, no repara**
  (D-22: cargar/validar ≠ crear/autorear; el entrevistador/autor sigue siendo T-44, futuro).
- **Emparejar** el contrato con los archivos realmente ingeridos en bronze, ni leer/validar ningún CSV: frontera
  D-21 intacta, eso es `load_data`.
- **Validar los otros YAMLs** (`business_rules.yaml`, `finance.yaml`, Maestro de Sectores): cada uno es su propio
  tracer bullet por-YAML (D-21). El subcomando es `contract check`, no `config check`.
- **Doblar la validación dentro de `zlk ingest`** (opción (b) de T-68, **descartada** en el paso 1): `ingest` sigue
  siendo archivador notarial que no parsea contenido.
- Agregación multi-error / listar todos los defectos del contrato de una vez: el motor es **fail-fast** por D-23c y
  esta feature no lo cambia. Muestra el primer error, como el motor lo da.
- Modo interactivo, `--fix`, `--watch`, salida JSON, o cualquier bandera más allá de lo mínimo (E4: mínima
  complejidad).
- Validar la plantilla `600_template/contract_data.yaml` como parte del comando (ya la cubre CA-22 de
  `contract_multifile`).

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **verificables y detallados** viven en `spec.md` como `CA-xx`.
1. `zlk contract check <CLIENTE>` sobre un tenant cuyo `input/contract_data.yaml` es **válido** (uno o varios
   archivos) termina con **exit code 0** e informa el éxito por **stdout**.
2. El mismo comando sobre un contrato **inválido por esquema** termina con exit ≠ 0 e imprime por **stderr** el
   mensaje de `ContractSchemaError` **exactamente como lo emite el motor** (verificado por igualdad exacta contra
   la constante `_MENSAJE_*` correspondiente, no por subcadena laxa).
3. El mismo comando sobre un YAML **sintácticamente roto** termina con exit ≠ 0 e imprime el mensaje de
   `ContractParseError`, **distinguible** del fallo de esquema.
4. El comando sobre un tenant recién creado por `zlk client new` (contrato con raíz presente y sin cuerpo) reporta
   **M-01** y exit ≠ 0 — señal útil, no traceback.
5. El comando sobre un **tenant inexistente**, o sobre un tenant **sin** `input/contract_data.yaml`, reporta un
   mensaje de dominio claro y su exit code, **sin `FileNotFoundError` ni traceback crudo**.
6. La resolución de `clients_root` respeta `ZEROLEAK_CLIENTS_ROOT` y cae a `./clients`, igual que los subcomandos
   vigentes.
7. Una invocación mal formada (`zlk contract`, `zlk contract check` sin cliente, `zlk contract foo`) imprime el
   **uso** por stderr y no revienta; `_USAGE` incluye la línea del subcomando nuevo.
8. El comando **no escribe nada** en disco: ni crea, ni corrige, ni toca el YAML, ni `data/`, ni el `manifest.json`
   (verificado, no asumido).
9. El comando **no lee ningún CSV** ni ninguna ruta fuera del `contract_data.yaml` del tenant (frontera D-21, con
   guarda de no-vacuidad al estilo L-17: el espía debe demostrar que observó algo).
10. `app/src/zeroleak/config/contract.py` queda **byte a byte idéntico** al de `main` al cerrar la feature.
11. La suite completa queda **en verde** (111 passed vigentes + los tests nuevos), con la **única** modificación
    declarada y aprobada en el gate del paso 5: el retiro de las dos aserciones de "no existe fachada CLI" en
    `test_load_contract_core_invocable_sin_cli`. Ninguna otra cobertura vigente se reduce.
12. **Distinción parse/schema (resuelto en el gate del paso 5 — variante A):** el mensaje del motor sale por
    stderr **intacto** y las dos fallas se distinguen por **exit code**. Es la única variante que preserva el
    criterio 2: con prefijo, `stderr` dejaría de ser igual **por igualdad exacta** al mensaje del motor y el test
    tendría que aflojarse a `startswith`. La spec fija los valores; el spike prototipó parse=3, schema=4.
13. **Precondición (resuelto en el gate del paso 5):** tenant inexistente y tenant sin `input/contract_data.yaml`
    comparten **un solo exit code (2)** —el mismo que `ingest` ya usa para `TenantNotFoundError`— y se distinguen
    por **mensaje**, no por código.

## Dependencias
- Feature **`config_contract` (T-43, en `main` vía PR #3)** y **`contract_multifile` (T-57, en `main` vía PR #4)**:
  aportan el motor completo que esta feature expone — `load_contract`, los modelos, las excepciones y el catálogo
  de mensajes M-01…M-13 congelado y verificado.
- Feature **`client_scaffold` (T-21, en `main`)**: crea el tenant y su `input/contract_data.yaml` placeholder; es
  el origen del caso M-01 de primera corrida y del `_clients_root()` que se reutiliza.
- Feature **`ingest` (T-28, en `main`)**: aporta el **patrón** a imitar — precondición de tenant verificada en el
  core/fachada y traducida a exit code (`TenantNotFoundError` → 2), y la forma de los tests de CLI.
- `900_persistence/tasks.md` **T-68** (esta feature; la opción (a) del registro es la elegida) y **T-69** (nota:
  `cargar_contrato.py`, borrado, era una herramienta de retroalimentación embrionaria — su historia en git es un
  punto de partida razonable, no una dependencia).
- `900_persistence/decisions.md`: **D-21** (descomposición por-YAML y frontera contra `load_data`), **D-22**
  (cargar/validar vs. crear), **D-23c** (fail-fast), **D-25**/**D-26** (forma y disyunción de los mensajes).
- **D-23d / CA-27 de `contract_multifile` (core-only, sin fachada CLI):** esta feature los **supera
  deliberadamente**. D-23d fue una decisión de **alcance de aquella feature** ("el consumidor real será `load_data`,
  que llama al core directo"), no una prohibición permanente de exponer el contrato por CLI; T-68 la registra
  explícitamente como opción (a) legítima "como feature posterior". El humano la eligió en el paso 1 de este flujo.
  **CA-27 sigue cumpliéndose**: el core continúa siendo invocable sin CLI — se le **agrega** una fachada, no se le
  impone una. Debe quedar registrada la decisión correspondiente en `decisions.md` al cierre.
- `700_architecture/system_design.md` §2.5/§4 (la CLI `zlk` es la primera fachada del motor) y §5 (YAML 1 =
  Contrato de Datos).
- `900_persistence/constraints.md` **C-01** (Datos en Bóveda): solo tenants y YAMLs sintéticos.

## Relación con Hitos de Producto
- **Sexto Tracer Bullet** del proyecto y **cierre del lazo humano** sobre el Contrato de Datos: es la primera vez
  que el trabajo de configuración del humano recibe una respuesta del motor. Sin esto, los trece mensajes de error
  que el proyecto congeló con tanto cuidado no tienen quién los muestre en el flujo real.
- **Habilita el futuro entrevistador/autor (T-44, D-22):** el lazo cerrado que aquella feature necesita
  —borrador → validar → repreguntar— es justo este comando; construir el juez antes que el autor es la secuencia
  que D-22 fijó.
- No bloquea a **`load_data`** (que llama al core directo), pero le entrega un tenant cuyo contrato **ya fue
  verificado por el humano**, en vez de uno que se descubre roto en mitad del pipeline.
