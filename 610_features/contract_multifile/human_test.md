# Pruebas humanas — `contract_multifile` (paso 13, gate humano)

> Este documento contiene las **pruebas que tú (humano) debes ejecutar** para
> validar la feature `contract_multifile` **antes de aprobar y mergear el PR** a
> `main`. Están diseñadas paso a paso y listas para copiar/pegar en la terminal.
> La feature es **core-only** (D-23d): expone la función `load_contract(path) ->
> Contract` y **no** un comando CLI, por eso las pruebas se ejecutan invocando
> Python directamente.
>
> Qué construyó esta feature: soporte para contrato de datos **multi-archivo**
> (`contract_data.archivos[].{nombre, columnas}`) en vez del esquema anterior de
> un solo bloque `contract_data.columnas`. Cierra además **T-56** (raíz
> nula/no-mapa ya no revienta con `AttributeError`) y **T-58** (la plantilla
> `600_template/contract_data.yaml` migrada al esquema nuevo).

## Prerrequisitos (una sola vez)

1. Abre una terminal (**PowerShell**) en la raíz del repositorio:
   `C:\Users\USUARIO\Documents\TripleS\ZeroLeak_Application`
2. Asegúrate de estar en la rama de la feature:
   ```powershell
   git branch --show-current
   ```
   Debe imprimir `feature/contract_multifile`. (Para las pruebas puedes quedarte
   en esta rama; el merge a `main` lo harás desde GitHub tras aprobar el PR.)
3. Verifica que Python 3.13 está disponible (el `python` del PATH es 3.12 y
   **falla**; usa siempre `py -3.13`):
   ```powershell
   py -3.13 --version
   ```
   Debe imprimir `Python 3.13.x`.

---

## Prueba 0 — Suite automatizada (regresión completa)

**Objetivo:** confirmar que **todos** los tests del proyecto (incluidos los 42
de esta feature) pasan en verde, sin regresiones.

**Comando:**
```powershell
py -3.13 -m pytest app/tests -q
```

**Resultado esperado:** la última línea dice **`111 passed`** (sin `failed` ni
`error`). Tiempo aproximado: unos segundos.

**Si falla:** anota el/los test(s) en rojo y **no apruebes el PR**; repórtalo en
la próxima sesión.

---

## Prueba 1 — Verificación asistida de comportamiento (1 comando, 15 casos)

**Objetivo:** ejercitar `load_contract` de punta a punta con contratos
**sintéticos** multi-archivo (válidos e inválidos) y confirmar el comportamiento
observable de los criterios de aceptación clave, incluida la **igualdad exacta**
de los mensajes de error congelados (M-01…M-13). El script crea sus propios YAML
en un directorio **temporal** (nunca bajo `clients/*/data/`) y no modifica nada;
la última prueba carga la plantilla **real y versionada** del repo.

**Comando:**
```powershell
py -3.13 610_features/contract_multifile/pruebas_humanas.py
```

**Resultado esperado:** quince líneas `[OK]` y, al final,
**`RESULTADO: 15/15 pruebas OK`** con el mensaje
`Todas las pruebas humanas pasaron. Feature lista para aprobar el PR.`

Las quince pruebas cubren:

| # | Caso | CA | M-xx | Qué valida |
|---|---|---|---|---|
| P1 | Contrato válido de 2 archivos | CA-01/02 | — | `Contract` con archivos en orden `[clientes.csv(3), ventas.csv(4)]` y campos fieles |
| P2 | Los 6 tipos en un archivo | CA-05 | — | Acepta `string/integer/float/date/datetime/boolean` |
| P3 | Columna homónima entre archivos | CA-03 | — | `cliente_id` en `clientes.csv` **y** `ventas.csv` se **acepta** (duplicado por archivo, no global) |
| P4 | `contract_data:` nulo | CA-19 | M-01 | `ContractSchemaError` (nunca `AttributeError`) — cierra **T-56** |
| P5 | Esquema viejo (`columnas` en la raíz) | CA-08 | M-02 | Mensaje que orienta a `archivos[]`, no el genérico M-04 |
| P6 | Contrato híbrido | CA-28 | M-13 | Se **rechaza** el `columnas` residual (nunca se ignora en silencio) |
| P7 | `archivos: []` | CA-06 | M-04 | `la lista de archivos no puede estar vacía` |
| P8 | `archivos` no-lista | CA-09 | M-03 | `'archivos' debe ser una lista (se encontró: 'ventas.csv')` |
| P9 | Archivo sin `nombre` | CA-10 | M-06 | Localizador **degrada limpio** a `archivo[1]` |
| P10 | Nombre de archivo duplicado | CA-13 | M-05 | `nombre de archivo duplicado: 'ventas.csv'` (nivel raíz) |
| P11 | Columna sin `tipo` | CA-15 | M-09 | Localiza `archivo[1] 'ventas.csv', columna de índice 1` |
| P12 | `tipo` fuera del enum | CA-16 | M-10 | Archivo + columna + valor inválido + los 6 permitidos |
| P13 | Columna duplicada en un archivo | CA-17 | M-11 | `archivo[1] 'ventas.csv': nombre de columna duplicado: 'venta_id'` |
| P14 | YAML sintácticamente roto | CA-18 | M-12 | `ContractParseError` (distinguible por tipo de `ContractSchemaError`) |
| P15 | Plantilla real del repo | CA-22 | — | `600_template/contract_data.yaml` carga sin error, `len(archivos) >= 1` |

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
2. Pega este bloque (crea un contrato multi-archivo válido en temporal y lo carga):
   ```python
   import tempfile, os
   from zeroleak.config import load_contract, ContractSchemaError, ContractParseError

   d = tempfile.mkdtemp()
   p = os.path.join(d, "contract_data.yaml")
   open(p, "w", encoding="utf-8").write(
       "contract_data:\n"
       "  archivos:\n"
       "    - nombre: clientes.csv\n"
       "      columnas:\n"
       "        - {nombre: cliente_id, tipo: integer, nulable: false, llave: true}\n"
       "    - nombre: ventas.csv\n"
       "      columnas:\n"
       "        - {nombre: venta_id, tipo: integer, nulable: false, llave: true}\n"
       "        - {nombre: monto,    tipo: float,   nulable: false, llave: false}\n"
   )
   c = load_contract(p)
   for a in c.archivos:
       print(a.nombre, "->", [(x.nombre, x.tipo.value) for x in a.columnas])
   ```
   **Esperado:**
   ```
   clientes.csv -> [('cliente_id', 'integer')]
   ventas.csv -> [('venta_id', 'integer'), ('monto', 'float')]
   ```
3. Prueba un error a mano (tipo inválido) y observa la excepción:
   ```python
   open(p, "w", encoding="utf-8").write(
       "contract_data:\n  archivos:\n    - nombre: ventas.csv\n"
       "      columnas:\n        - {nombre: monto, tipo: xyz, nulable: false, llave: false}\n"
   )
   try:
       load_contract(p)
   except ContractSchemaError as e:
       print("OK, error esperado:", e)
   ```
   **Esperado:** un mensaje que localiza `archivo[0] 'ventas.csv', columna de
   índice 0, campo 'tipo': valor 'xyz' inválido` y enumera los 6 tipos permitidos.
4. Sal con `exit()`.

---

## Criterio de aprobación del PR

Aprueba y mergea el PR **solo si**:

- ✅ Prueba 0 → `111 passed`
- ✅ Prueba 1 → `RESULTADO: 15/15 pruebas OK`

La Prueba 2 es exploratoria y no condiciona la aprobación.

## Qué NO cubre esta feature (fuera de alcance, por diseño)

- **No** compara el contrato contra un CSV real de bronze (eso es `load_data`,
  etapa posterior; frontera **D-21**). `load_contract` solo abre el propio
  `contract_data.yaml`, nunca un `.csv` ni nada bajo `data/bronze/` o `clients/`.
- **No** expone un comando `zlk contract validate` (core-only, **D-23d**).
- **No** resuelve la colisión `Ventas.csv` vs `ventas.csv` (mismo fichero en
  Windows/macOS): se comparan `nombre` por **cadena exacta**; la colisión física
  se difiere a `load_data` (**T-59**).
- **No** carga otros YAML (`business_rules.yaml`, `finance.yaml`, etc.).

Si al probar esperabas alguno de estos comportamientos, **no es un fallo**: está
deliberadamente fuera del alcance de este tracer bullet.
