"""Tests unitarios del core `zeroleak.core.scaffold`.

Caso 1 del bucle TDD (client_scaffold): nombres inválidos deben lanzar
`ClientNameError` y no dejar ningún artefacto en `clients_root` (CA-04,
TSK-02). Datos sintéticos únicamente (regla "Datos en Bóveda", C-01).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from zeroleak.core.scaffold import (
    ClientNameError,
    NAME_PATTERN,
    TenantExistsError,
    create_client,
)

#: Patrón congelado por la spec (CA-05): allow-list explícita, sin `\w`
#: Unicode amplio. `NAME_PATTERN` debe ser exactamente este string.
FROZEN_NAME_PATTERN = r"^[A-Za-z0-9_\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$"

VALID_NAMES = [
    "x",
    "cliente_01",
    "COMPANY-DEMO",
    "Sanducheria_Ñoño",
    "Café_Málaga",
    "ÁÉÍÓÚüÑ",
]

INVALID_NAMES = [
    "",
    "   ",
    "cliente con espacios",
    "cli/ente",
    "cli\\ente",
    "../escape",
    "клиент",
    "cli😀",
    "x" * 65,
]


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_create_client_nombre_invalido_lanza_client_name_error_sin_tocar_disco(
    name: str, clients_root: Path
) -> None:
    """CA-04: cada nombre inválido lanza ClientNameError sin tocar disco."""
    with pytest.raises(ClientNameError):
        create_client(name, clients_root)

    # clients_root debe seguir limpio: ningún artefacto (ni tenant parcial
    # ni carpeta de staging) fue creado por el intento fallido.
    assert list(clients_root.iterdir()) == []


def test_create_client_sobre_clients_root_limpio_crea_estructura_canonica_completa(
    clients_root: Path,
) -> None:
    """CA-01 (TSK-04): sobre `clients_root` limpio, `create_client` retorna
    `root/"SANDUCHERIA"` y materializa los 6 artefactos canónicos: `client.yaml`,
    los 3 YAMLs de `input/` (`contract_data.yaml`, `business_rules.yaml`,
    `finance.yaml`), `data/{bronze,silver,gold}/` y `data/manifest.json`.
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)

    assert tenant_dir == clients_root / "SANDUCHERIA"

    assert (tenant_dir / "client.yaml").is_file()
    assert (tenant_dir / "input" / "contract_data.yaml").is_file()
    assert (tenant_dir / "input" / "business_rules.yaml").is_file()
    assert (tenant_dir / "input" / "finance.yaml").is_file()
    assert (tenant_dir / "data" / "bronze").is_dir()
    assert (tenant_dir / "data" / "silver").is_dir()
    assert (tenant_dir / "data" / "gold").is_dir()
    assert (tenant_dir / "data" / "manifest.json").is_file()


# --- Caso 3 (TSK-06, CA-05): validación-válidos ---------------------------
#
# Nombres válidos (incl. acentos/ñ/mayúsculas acentuadas) deben crear el
# tenant correctamente, y NAME_PATTERN debe ser exactamente el patrón
# allow-list congelado por la spec (sin `\w` Unicode amplio).


@pytest.mark.parametrize("name", VALID_NAMES)
def test_create_client_nombre_valido_crea_el_tenant(
    name: str, clients_root: Path
) -> None:
    """CA-05: cada nombre válido del conjunto de la spec (incluye acentos,
    ñ y mayúsculas acentuadas) pasa la validación y crea el tenant en
    `clients_root/<name>`.
    """
    tenant_dir = create_client(name, clients_root)

    assert tenant_dir == clients_root / name
    assert tenant_dir.is_dir()


def test_name_pattern_es_exactamente_la_allow_list_congelada_por_la_spec() -> None:
    """CA-05: `NAME_PATTERN` es exactamente el patrón allow-list explícito
    fijado en la spec (`^[A-Za-z0-9_\\-áéíóúüÁÉÍÓÚÜñÑ]{1,64}$`), sin `\\w`
    Unicode amplio. Si el patrón cambiara (aunque fuera equivalente en
    comportamiento, p. ej. usando `\\w` con `re.UNICODE`), este test falla.
    """
    assert NAME_PATTERN == FROZEN_NAME_PATTERN


# --- Caso 4 (TSK-08, CA-07): placeholders-yaml -----------------------------
#
# `client.yaml` y los 3 YAMLs de `input/` deben ser parseables por
# `yaml.safe_load` sin excepcion, tener las claves marcador esperadas con
# valor vacio (None, dado que el placeholder actual usa "clave:" sin valor)
# y al menos un comentario guia ("#"). `client.yaml` ademas trae las 4
# claves de identidad. Ninguno debe contener datos reales/sensibles: se
# comprueba que todas las claves marcador tienen valor vacio.

#: Ruta relativa (dentro del tenant) -> claves marcador esperadas, para cada
#: uno de los 4 YAMLs de placeholder que produce `create_client`.
PLACEHOLDER_YAML_KEYS = {
    "client.yaml": ["client_id", "display_name", "sector_id", "created_at"],
    "input/contract_data.yaml": ["contract_data"],
    "input/business_rules.yaml": ["business_rules"],
    "input/finance.yaml": ["finance"],
}


@pytest.mark.parametrize("rel_path, expected_keys", PLACEHOLDER_YAML_KEYS.items())
def test_placeholder_yaml_es_parseable_con_claves_vacias_y_comentario_guia(
    rel_path: str, expected_keys: list[str], clients_root: Path
) -> None:
    """CA-07: cada uno de los 4 YAML de placeholder (`client.yaml` y los 3
    de `input/`) es parseable por `yaml.safe_load` sin excepcion, contiene
    las claves marcador esperadas con valor vacio y al menos un comentario
    guia ("#" en el texto crudo). Si faltara una clave, si el valor no
    estuviera vacio, o si no hubiera comentario, este test fallaria.
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)
    file_path = tenant_dir / rel_path

    raw_text = file_path.read_text(encoding="utf-8")
    assert "#" in raw_text, f"{rel_path} debe incluir al menos un comentario guia"

    parsed = yaml.safe_load(raw_text)

    assert isinstance(parsed, dict)
    for key in expected_keys:
        assert key in parsed, f"falta la clave marcador {key!r} en {rel_path}"
        # Valor vacio: el placeholder minimo genérico usa "clave:" sin
        # valor, que yaml.safe_load interpreta como None.
        assert not parsed[key], (
            f"la clave {key!r} en {rel_path} no esta vacia (posible dato real): "
            f"{parsed[key]!r}"
        )


def test_client_yaml_incluye_las_4_claves_de_identidad_vacias(
    clients_root: Path,
) -> None:
    """CA-07: `client.yaml` incluye explicitamente `client_id`,
    `display_name`, `sector_id` y `created_at`, todas con valor vacio (sin
    datos reales del tenant).
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)
    parsed = yaml.safe_load((tenant_dir / "client.yaml").read_text(encoding="utf-8"))

    identity_keys = ["client_id", "display_name", "sector_id", "created_at"]
    assert set(identity_keys).issubset(parsed.keys())
    for key in identity_keys:
        assert not parsed[key], f"{key!r} no esta vacio: {parsed[key]!r}"


# --- Caso 5 (TSK-10, CA-08): medallion-manifest ----------------------------
#
# Tras el alta deben existir los tres directorios de la estructura medallion
# (`data/bronze/`, `data/silver/`, `data/gold/`), todos vacios, y
# `data/manifest.json` debe parsear como JSON exactamente igual al ledger
# inicial `{"version": 1, "files": []}` (CA-08).


@pytest.mark.parametrize("bucket", ["bronze", "silver", "gold"])
def test_medallion_dir_existe_y_esta_vacio(bucket: str, clients_root: Path) -> None:
    """CA-08: `data/<bucket>/` existe y no contiene ningun archivo ni
    subdirectorio tras el alta. Si `create_client` dejara algun artefacto
    (p. ej. un `.gitkeep` o cualquier fichero) dentro de estos directorios,
    este test fallaria.
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)
    bucket_dir = tenant_dir / "data" / bucket

    assert bucket_dir.is_dir()
    assert list(bucket_dir.iterdir()) == []


def test_manifest_json_es_el_ledger_inicial_vacio(clients_root: Path) -> None:
    """CA-08: `data/manifest.json` parsea como JSON exactamente igual a
    `{"version": 1, "files": []}` (ledger inicial vacio y valido). Si el
    contenido difiriera en clave, tipo o valor (p. ej. `"version": "1"` o
    `"files": [{}]`), este test fallaria.
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)
    manifest_path = tenant_dir / "data" / "manifest.json"

    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    assert manifest == {"version": 1, "files": []}


# --- Caso 6 (TSK-12, CA-04): sin-residuo-nombre-invalido -------------------
#
# Un nombre invalido debe lanzar ClientNameError SIN dejar ningun residuo en
# `clients_root`: ni un tenant parcial, ni una carpeta `.staging-<uuid>`
# huerfana. Este es el contrato de atomicidad de la spec (CA-04 / "Enfoque
# Tecnico": atomicidad staging+rename). A diferencia del test de Caso 1 (que
# solo comprueba `clients_root` vacio en general), este test es explicito
# sobre el residuo que mas preocupa: la carpeta de staging.

RESIDUE_INVALID_NAMES = [
    "cli/ente",
    "../escape",
]


@pytest.mark.parametrize("name", RESIDUE_INVALID_NAMES)
def test_create_client_nombre_invalido_no_deja_residuo_en_clients_root(
    name: str, clients_root: Path
) -> None:
    """CA-04 (TSK-12): un nombre invalido lanza `ClientNameError` y, tras la
    excepcion, `clients_root` sigue exactamente vacio: ni tenant parcial ni
    carpeta `.staging-*` huerfana. Como la validacion ocurre antes de tocar
    disco (Caso 1/2), se espera que este test pase de inmediato; si
    `create_client` llegara a tocar disco (p. ej. crear el staging) antes de
    validar el nombre, este test detectaria el residuo `.staging-*` y
    fallaria.
    """
    with pytest.raises(ClientNameError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []
    assert list(clients_root.glob(".staging-*")) == []


# --- Caso 7 (TSK-13, CA-04): atomicidad-fallo-io ---------------------------
#
# Un fallo de E/S a mitad de la construccion del arbol (despues de que el
# staging `.staging-<uuid>` ya existe en disco con sus subdirectorios, pero
# antes de que `os.replace` promueva el tenant) debe propagarse tal cual y
# NO dejar ningun residuo en `clients_root`: ni tenant parcial, ni carpeta
# `.staging-*` huerfana (spec CA-04 / Enfoque Tecnico: atomicidad
# staging+rename, bloque try/except con `shutil.rmtree`).
#
# Punto de monkeypatch elegido: `pathlib.Path.write_text`. `_build_tenant_tree`
# primero crea los subdirectorios de `_EMPTY_DIRS` (`input`, `data/bronze`,
# `data/silver`, `data/gold`) con `mkdir` y SOLO DESPUES empieza a escribir
# los archivos de texto (`client.yaml`, los YAML de `input/`, `manifest.json`)
# con `Path.write_text`. Forzando la excepcion en `write_text` se garantiza
# que el `.staging-<uuid>` ya existe en disco (con sus subdirectorios) cuando
# se lanza el fallo: es un fallo "a mitad" de la construccion, no antes de
# empezar. Esto ejercita de verdad el bloque `except: shutil.rmtree(...)` de
# `create_client`.


def test_create_client_fallo_io_a_mitad_no_deja_residuo(
    monkeypatch: pytest.MonkeyPatch, clients_root: Path
) -> None:
    """CA-04 (TSK-13): un fallo de E/S forzado a mitad de la construccion del
    arbol (durante la escritura de archivos, con el staging ya creado en
    disco) se propaga tal cual y `clients_root` queda exactamente vacio tras
    la excepcion: ni tenant parcial ni carpeta `.staging-*` residual.
    """

    def _fake_write_text(self: Path, *args: object, **kwargs: object) -> int:
        raise OSError("disco lleno simulado")

    monkeypatch.setattr(Path, "write_text", _fake_write_text)

    with pytest.raises(OSError, match="disco lleno simulado"):
        create_client("SANDUCHERIA", clients_root)

    assert list(clients_root.iterdir()) == []
    assert list(clients_root.glob(".staging-*")) == []


# --- Caso 8 (TSK-15, CA-06): tenant-existente ------------------------------
#
# No idempotencia: si el tenant ya existe, un segundo `create_client` con el
# mismo nombre debe lanzar `TenantExistsError` (excepcion de dominio, con
# mensaje claro) y el tenant existente debe quedar exactamente igual a como
# estaba antes del reintento (mismo snapshot de rutas + tamanos). Ademas, el
# reintento fallido no debe dejar ninguna carpeta `.staging-*` huerfana en
# `clients_root` (spec CA-06 / Enfoque Tecnico: chequeo previo de existencia
# + `os.replace` como red de seguridad).


def test_create_client_tenant_existente_lanza_tenant_exists_error_y_no_lo_modifica(
    clients_root: Path, tenant_snapshot
) -> None:
    """CA-06 (TSK-15): tras crear el tenant "SANDUCHERIA", un segundo
    `create_client("SANDUCHERIA", clients_root)` lanza `TenantExistsError` y
    el snapshot (rutas relativas + tamanos) del tenant existente es
    identico antes y despues del reintento: no se modifica, agrega ni
    elimina nada. Tampoco queda residuo `.staging-*` en `clients_root`.
    """
    tenant_dir = create_client("SANDUCHERIA", clients_root)

    snapshot_antes = tenant_snapshot(tenant_dir)

    with pytest.raises(TenantExistsError):
        create_client("SANDUCHERIA", clients_root)

    snapshot_despues = tenant_snapshot(tenant_dir)
    assert snapshot_despues == snapshot_antes, (
        "el tenant existente fue modificado por el segundo create_client "
        "(deberia haber quedado intacto)"
    )

    assert list(clients_root.glob(".staging-*")) == []


# --- Caso 12 (TSK-22, CA-09): gitignore-frontera-pii -----------------------
#
# La regla `.gitignore` `clients/*/data/` (C-01, "Datos en Boveda") debe
# cubrir efectivamente `clients/<NOMBRE>/data/` (bronze/silver/gold/
# manifest.json), y NO debe cubrir `client.yaml` ni `input/...` (que son
# versionables). Se verifica el comportamiento REAL de Git con
# `git check-ignore -v`, ejecutado desde la raiz del repo, sobre rutas
# relativas ficticias del patron `clients/DEMO_X/...`. `git check-ignore`
# evalua el path contra las reglas sin requerir que el archivo exista en
# disco, por lo que no se crea ningun tenant real bajo `clients/` (se
# respeta C-01: no se ensucia el repo con datos ni artefactos reales).


def _repo_root() -> Path:
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def _git_check_ignore(rel_path: str) -> bool:
    """Retorna True si `git check-ignore` marca `rel_path` como ignorado.

    Ejecuta el comando con `cwd` en la raiz del repo, sobre una ruta
    relativa ficticia (no requiere que el archivo/directorio exista).
    """
    import subprocess

    result = subprocess.run(
        ["git", "check-ignore", "-v", "--", rel_path],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
    )
    # exit code 0 => la ruta esta ignorada; 1 => no ignorada.
    return result.returncode == 0


IGNORED_PATHS = [
    "clients/DEMO_X/data/",
    "clients/DEMO_X/data/bronze/archivo.parquet",
    "clients/DEMO_X/data/manifest.json",
]

VERSIONABLE_PATHS = [
    "clients/DEMO_X/client.yaml",
    "clients/DEMO_X/input/contract_data.yaml",
]


@pytest.mark.parametrize("rel_path", IGNORED_PATHS)
def test_gitignore_cubre_data_del_tenant(rel_path: str) -> None:
    """CA-09: `git check-ignore` marca como ignorada cualquier ruta bajo
    `clients/<NOMBRE>/data/` (el directorio, un archivo dentro de un bucket
    medallion, y `manifest.json`).
    """
    assert _git_check_ignore(rel_path), (
        f"{rel_path!r} deberia estar cubierto por la regla .gitignore "
        f"'clients/*/data/' (C-01) pero git check-ignore no lo marco"
    )


@pytest.mark.parametrize("rel_path", VERSIONABLE_PATHS)
def test_gitignore_no_cubre_client_yaml_ni_input(rel_path: str) -> None:
    """CA-09: `git check-ignore` NO marca como ignorados `client.yaml` ni los
    YAML de `input/`: deben permanecer versionables.
    """
    assert not _git_check_ignore(rel_path), (
        f"{rel_path!r} NO deberia estar cubierto por .gitignore (es "
        f"versionable) pero git check-ignore lo marco como ignorado"
    )


# --- Caso 13 (TSK-23, CA-10): company-demo-canonico ------------------------
#
# `COMPANY_DEMO` no es un caso especial: `create_client("COMPANY_DEMO", root)`
# debe producir exactamente el mismo andamiaje (mismo conjunto de rutas
# relativas y mismo contenido de placeholders) que cualquier otro tenant
# "real" creado por la misma via (`create_client`/`zlk client new`). Se usan
# dos `clients_root` gemelos en `tmp_path` para que el nombre del tenant no
# contamine la comparacion de rutas: cada snapshot se toma relativo a la
# carpeta del propio tenant (no a `clients_root`), asi "COMPANY_DEMO/" vs
# "SANDUCHERIA/" no aparecen como prefijos distintos.


def test_create_client_company_demo_produce_andamiaje_identico_a_tenant_real(
    tmp_path: Path, tenant_snapshot
) -> None:
    """CA-10 (TSK-23): el conjunto de rutas relativas (estructura canonica)
    producido por `create_client("COMPANY_DEMO", root)` es identico al
    producido por `create_client("SANDUCHERIA", root)` (un tenant real
    cualquiera creado por la misma via). Si `create_client` tuviera una rama
    especial para `COMPANY_DEMO` (p. ej. `if name == "COMPANY_DEMO": ...`)
    que anadiera, quitara o renombrara artefactos, este test lo detectaria
    como una divergencia en el conjunto de rutas relativas.
    """
    root_demo = tmp_path / "clients_root_demo"
    root_demo.mkdir()
    root_real = tmp_path / "clients_root_real"
    root_real.mkdir()

    tenant_demo = create_client("COMPANY_DEMO", root_demo)
    tenant_real = create_client("SANDUCHERIA", root_real)

    rutas_demo = set(tenant_snapshot(tenant_demo).keys())
    rutas_real = set(tenant_snapshot(tenant_real).keys())

    assert rutas_demo == rutas_real, (
        "COMPANY_DEMO no produjo el mismo conjunto de rutas relativas que "
        "un tenant real: recibio un andamiaje especial/distinto"
    )

    # Los placeholders son genericos (no incrustan el nombre del tenant), asi
    # que el contenido byte a byte de cada archivo de texto tambien deberia
    # coincidir entre COMPANY_DEMO y el tenant real.
    for rel_path in sorted(rutas_demo):
        demo_path = tenant_demo / rel_path
        real_path = tenant_real / rel_path
        if demo_path.is_file():
            assert demo_path.read_bytes() == real_path.read_bytes(), (
                f"contenido divergente en {rel_path!r} entre COMPANY_DEMO y "
                f"el tenant real (los placeholders deberian ser genericos)"
            )
