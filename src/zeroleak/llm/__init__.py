"""llm — acceso a LLM encapsulado (solo datos sintéticos, nunca PII).

El LLM NO participa del camino de datos reales: su rol es de diseño/desarrollo
usando exclusivamente datos sintéticos (C-01, §7). El motor de auditoría en
ejecución es determinista y sin LLM. Proveedor por defecto: Anthropic (Claude),
detrás de una interfaz estable e intercambiable. Ver system_design §13.
"""
