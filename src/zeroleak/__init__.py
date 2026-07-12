"""ZeroLeak — auditor de fugas de dinero ocultas en los datos (COQD).

Motor local determinista de la Fase Servicio: consume datos del cliente
(CSV/Excel) + configuración (YAML) y produce un diagnóstico financiero
(JSON + CSVs masticados + reporte). Diseñado "como una API" para evolucionar
a SaaS sin reescribir el núcleo.

Ver `700_architecture/system_design.md`.
"""

__version__ = "0.1.0"
