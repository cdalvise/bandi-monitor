"""
Modulo filtro per parole chiave.
Filtra i bandi in base alle parole chiave configurate in config.json.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def carica_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"filtro_attivo": False, "parole_chiave": []}


def bando_corrisponde(bando: dict, parole_chiave: list[str]) -> tuple[bool, list[str]]:
    """
    Verifica se un bando contiene almeno una parola chiave.
    Restituisce (corrisponde, [parole_trovate]).
    """
    if not parole_chiave:
        return True, []

    testo = f"{bando.get('titolo', '')} {bando.get('descrizione', '')}".lower()
    trovate = [p for p in parole_chiave if p.lower() in testo]
    return len(trovate) > 0, trovate


def filtra_bandi(bandi: list[dict]) -> tuple[list[dict], dict]:
    """
    Filtra la lista di bandi in base alla configurazione.

    Restituisce:
        - lista dei bandi filtrati (con campo 'parole_trovate' aggiunto)
        - dict con statistiche del filtraggio
    """
    config = carica_config()

    if not config.get("filtro_attivo", False) or not config.get("parole_chiave"):
        logger.info("Filtro parole chiave disattivato — restituisco tutti i bandi.")
        return bandi, {"filtro_attivo": False, "totale": len(bandi), "filtrati": len(bandi)}

    parole_chiave = config["parole_chiave"]
    logger.info(f"Filtro attivo con {len(parole_chiave)} parole chiave.")

    bandi_filtrati = []
    for bando in bandi:
        corrisponde, trovate = bando_corrisponde(bando, parole_chiave)
        if corrisponde:
            bando["parole_trovate"] = trovate
            bandi_filtrati.append(bando)

    stats = {
        "filtro_attivo": True,
        "parole_chiave": parole_chiave,
        "totale_prima": len(bandi),
        "filtrati": len(bandi_filtrati),
        "esclusi": len(bandi) - len(bandi_filtrati),
    }

    logger.info(f"Filtro: {len(bandi)} bandi → {len(bandi_filtrati)} corrispondenze")
    return bandi_filtrati, stats
