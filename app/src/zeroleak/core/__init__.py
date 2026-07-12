"""core — el motor: orquestación del pipeline y abstracciones de tenant.

Aloja el pipeline de auditoría, `ClientContext` (resolución de rutas del
tenant), los contratos de entrada/salida y el scaffolding de tenants
(`create_client`, que materializa `clients/<CLIENTE>/`). Ver system_design §4, §11, §12.
"""
