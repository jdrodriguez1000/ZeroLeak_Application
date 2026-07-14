# Pruebas humanas — `config_contract` (paso 13, gate humano)

> Este documento contiene las **pruebas que tú (humano) debes ejecutar** para
> validar la feature `config_contract` **antes de aprobar y mergear el PR** a
> `main`. Están diseñadas paso a paso y listas para copiar/pegar en la terminal.
> La feature es **core-only** (D-23d): expone la función `load_contract(path) ->
> Contract` y **no** un comando CLI, por eso las pruebas se ejecutan invocando
> Python directamente.

## Prerrequisitos (una sola vez)

1. Abre una terminal (PowerShell) en la raíz del repositorio:
   `C:\Users\USUARIO\Documents\TripleS\ZeroLeak_Application`
2. Asegúrate de estar en la rama de la feature:
   ```powershell
   git branch --show-current
   ```
   Debe imprimir `feature/config_contract`. (Para las pruebas puedes quedarte en
   esta rama; el merge a `main` lo harás desde GitHub tras aprobar el PR.)
3. Verifica que Python 3.13 está disponible (el `python` del PATH es 3.12 y
   **falla**; usa siempre `py -3.13`):
   ```powershell
   py -3.13 --version
   ```
   Debe imprimir `Python 3.13.x`.

---

## Prueba 0 — Suite automatizada (regresión completa)

**Objetivo:** confirmar que los 88 tests del proyecto (incluidos los 19 de esta
feature) pasan en verde, sin regresiones.

**Comando:**
```powershell
py -3.13 -m pytest app/tests -q
```

**Resultado esperado:** la última línea dice **`88 passed`** (sin `failed` ni
`error`). Tiempo aproximado: unos segundos.

**Si falla:** anota el/los test(s) en rojo y **no apruebes el PR**; repórtalo en
la próxima sesión.

---

## Prueba 1 — Verificación asistida de comportamiento (1 comando, 7 casos)

**Objetivo:** ejercitar `load_contract` de punta a punta con contratos
**sintéticos** (válidos e inválidos) y confirmar el comportamiento observable de
los criterios de aceptación clave. El script crea sus propios YAML en un
directorio **temporal** (nunca bajo `clients/*/data/`) y no modifica nada.

**Comando:**
```powershell
py -3.13 610_features/config_contract/pruebas_humanas.py
```

**Resultado esperado:** siete líneas `[OK]` y, al final,
**`RESULTADO: 7/7 pruebas OK`** con el mensaje
`Todas las pruebas humanas pasaron. Feature lista para aprobar el PR.`

Las siete pruebas cubren:

| # | Caso | CA | Qué valida |
|---|---|---|---|
| P1 | Contrato válido | CA-01/02 | Devuelve `Contract` con las columnas en el orden declarado y campos fieles |
| P2 | Los 6 tipos | CA-03 | Acepta `string/integer/float/date/datetime/boolean` |
| P3 | Falta `tipo` | CA-04 | `ContractSchemaError` que nombra campo y columna (índice) |
| P4 | `tipo` fuera de enum | CA-06 | `ContractSchemaError` con valor inválido + los 6 permitidos |
| P5 | `columnas: []` | CA-11 | `ContractSchemaError` "la lista de columnas no puede estar vacía" |
| P6 | Duplicados | CA-09/10 | `test_id`/`test_id` se rechaza; `test_id`/`Test_ID` se acepta |
| P7 | YAML roto | CA-07/08 | `ContractParseError` accionable (menciona "YAML" e "inválido") |

**Si sale algún `[FALLA]`:** el script imprime el detalle (esperado vs
obtenido) y termina con código != 0; **no apruebes el PR** y repórtalo.

---

## Prueba 2 (opcional) — Exploración manual en el intérprete

**Objetivo:** si quieres "tocar" la API con tus propias manos, puedes probar en
una sesión interactiva de Python.

**Pasos:**
1. Abre el intérprete:
   ```powershell
   py -3.13
   ```
2. Pega este bloque (crea un contrato válido en temporal y lo carga):
   ```python
   import tempfile, os
   from zeroleak.config import load_contract, ContractSchemaError, ContractParseError

   d = tempfile.mkdtemp()
   p = os.path.join(d, "contract_data.yaml")
   open(p, "w", encoding="utf-8").write(
       "contract_data:\n"
       "  columnas:\n"
       "    - {nombre: test_id, tipo: integer, nulable: false, llave: true}\n"
       "    - {nombre: correo,  tipo: string,  nulable: true,  llave: false}\n"
   )
   c = load_contract(p)
   print("columnas:", [(x.nombre, x.tipo.value) for x in c.columnas])
   ```
   **Esperado:** `columnas: [('test_id', 'integer'), ('correo', 'string')]`
3. Prueba un error a mano (tipo inválido) y observa la excepción:
   ```python
   open(p, "w", encoding="utf-8").write(
       "contract_data:\n  columnas:\n    - {nombre: x, tipo: xyz, nulable: false, llave: false}\n"
   )
   try:
       load_contract(p)
   except ContractSchemaError as e:
       print("OK, error esperado:", e)
   ```
   **Esperado:** un mensaje que contiene `valor 'xyz' inválido` y enumera los 6
   tipos permitidos.
4. Sal con `exit()`.

---

## Criterio de aprobación del PR

Aprueba y mergea el PR **solo si**:

- ✅ Prueba 0 → `88 passed`
- ✅ Prueba 1 → `RESULTADO: 7/7 pruebas OK`

La Prueba 2 es exploratoria y no condiciona la aprobación.

## Qué NO cubre esta feature (fuera de alcance, por diseño)

- **No** compara el contrato contra un CSV real de bronze (eso es `load_data`,
  etapa posterior; frontera D-21).
- **No** expone un comando `zlk contract validate` (core-only, D-23d).
- **No** carga otros YAML (`business_rules.yaml`, `finance.yaml`, etc.).

Si al probar esperabas alguno de estos comportamientos, **no es un fallo**: está
deliberadamente fuera del alcance de este tracer bullet.
