"""Capa de recuperacion semantica (RAG).

DONDE VIVE ESTA CAPA — leelo antes de tocar nada:

El retrieval NO decide configuraciones. Nunca. La decision es del solver
(app/solver/engine.py) y esa garantia es el producto entero. Esta capa hace dos
cosas, ambas ANTES o DESPUES de la decision, jamas durante:

  1. ANTES  (app/retrieval/profiles.py)  Traduce como habla el cliente
     ("banda transportadora en zona de lavado") a restricciones CANDIDATAS
     que el cliente confirma y el solver valida. Si son imposibles, sale el
     nucleo insatisfacible igual que siempre.

  2. DESPUES (app/retrieval/chunks.py)   Respalda con documentacion oficial lo
     que el agente afirma en prosa, con documento y pagina citables.

Si alguna vez una funcion de este paquete devuelve una configuracion armada,
esta mal escrita: bajala a proponer restricciones y deja que el solver resuelva.
"""
