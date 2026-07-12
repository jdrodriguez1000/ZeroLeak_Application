"""vault — "Datos en Bóveda": binarización Drop & Detach (bronze → silver).

Lee bronze (con PII) localmente, crea columnas bandera (1/0) y elimina de raíz
las columnas de texto sensible, produciendo `data/silver/` sin PII. Frontera
física de PII que hace auditable el cumplimiento de C-01. Ver system_design §7.
"""
