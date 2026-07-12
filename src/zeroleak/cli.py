"""Fachada CLI del Científico de Datos: comando `zlk`.

Es la primera fachada del motor (system_design §2.5, §4); mañana el frontend
web del SaaS será otra fachada sobre el mismo motor. La lógica real de cada
subcomando —empezando por `zlk client new <NOMBRE_CLIENTE>`— se construye como
feature con el flujo SDD+TDD. Aquí solo vive el punto de entrada del esqueleto.
"""


def main() -> None:
    """Punto de entrada de la consola `zlk` (placeholder del esqueleto, T-11)."""
    raise SystemExit(
        "zlk: CLI aún no implementada. El primer subcomando "
        "(`zlk client new <NOMBRE_CLIENTE>`) llegará como feature."
    )
