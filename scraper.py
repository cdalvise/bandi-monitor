"""
Monitor Bandi Regionali Italiani
Scraper principale che controlla i siti ufficiali delle regioni italiane
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
from datetime import datetime
from typing import Optional
import time
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Headers per sembrare un browser normale
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Configurazione siti regionali
REGIONI = [
    {
        "nome": "Lombardia",
        "url": "https://www.regione.lombardia.it/wps/portal/istituzionale/HP/bandi-e-finanziamenti",
        "selettore_lista": "div.bandi-list article, ul.bandi li, .bando-item",
        "selettore_titolo": "h2, h3, .titolo, a",
        "selettore_link": "a",
        "selettore_data": ".data, time, .date",
        "selettore_scadenza": ".scadenza, .deadline, .data-scadenza, [class*='scad']",
    },
    {
        "nome": "Piemonte",
        "url": "https://bandi.regione.piemonte.it/contributi-finanziamenti",
        "selettore_lista": ".views-row, article.bando, li.bando",
        "selettore_titolo": "h3, h2, .views-field-title a",
        "selettore_link": "a",
        "selettore_data": ".field-date, .views-field-field-data, time",
        "selettore_scadenza": ".views-field-field-scadenza, .scadenza, [class*='scad']",
    },
    {
        "nome": "Veneto",
        "url": "https://bandi.regione.veneto.it/Public/Regione",
        "selettore_lista": "tr.bando-row, .bando-item, .risultato",
        "selettore_titolo": "td.titolo a, .titolo-bando, h3",
        "selettore_link": "a",
        "selettore_data": "td.data, .data-bando",
        "selettore_scadenza": "td.scadenza, .data-scadenza, [class*='scad']",
    },
    {
        "nome": "Emilia-Romagna",
        "url": "https://bandi.regione.emilia-romagna.it/",
        "selettore_lista": ".bando-row, article.bando, .field-items .field-item",
        "selettore_titolo": "h3 a, h2 a, .titolo a",
        "selettore_link": "a",
        "selettore_data": ".field-date, .data, time",
        "selettore_scadenza": ".field-scadenza, .scadenza, [class*='scad']",
    },
    {
        "nome": "Toscana",
        "url": "https://www.regione.toscana.it/bandi",
        "selettore_lista": ".list-item, .bando, article",
        "selettore_titolo": "h3, h2, .item-title",
        "selettore_link": "a",
        "selettore_data": ".date, .data",
        "selettore_scadenza": ".scadenza, .deadline, [class*='scad']",
    },
    {
        "nome": "Lazio",
        "url": "https://www.lazioeuropa.it/bandi/",
        "selettore_lista": ".bando-item, article, .row-bando",
        "selettore_titolo": "h3, h2, .title",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad'], .deadline",
    },
    {
        "nome": "Campania",
        "url": "https://www.regione.campania.it/regione/it/tematiche/bandi-e-contributi",
        "selettore_lista": ".list-group-item, article, .bando",
        "selettore_titolo": "h4, h3, a.titolo",
        "selettore_link": "a",
        "selettore_data": ".data, .field-date",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Sicilia",
        "url": "https://www.regione.sicilia.it/istituzioni/servizi-informativi/bandi",
        "selettore_lista": ".field-item, .bando-row, article",
        "selettore_titolo": "h3, h2, .titolo",
        "selettore_link": "a",
        "selettore_data": ".data, .date, time",
        "selettore_scadenza": ".scadenza, td.scadenza, [class*='scad']",
    },
    {
        "nome": "Puglia",
        "url": "https://www.regione.puglia.it/web/guest/contributi-e-finanziamenti",
        "selettore_lista": ".list-item, article.bando, .portlet-body li",
        "selettore_titolo": "h3, h2, a.asset-title",
        "selettore_link": "a",
        "selettore_data": ".publish-date, .data, time",
        "selettore_scadenza": ".expiration-date, .scadenza, [class*='scad']",
    },
    {
        "nome": "Sardegna",
        "url": "https://www.regione.sardegna.it/argomenti/bandi-e-concorsi/",
        "selettore_lista": ".bando, li.item, article",
        "selettore_titolo": "h3, h2, .titolo",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Liguria",
        "url": "https://www.regione.liguria.it/home-regione/bandi-contributi-finanziamenti.html",
        "selettore_lista": ".bando-item, article, .item",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Friuli Venezia Giulia",
        "url": "https://www.regione.fvg.it/rafvg/cms/RAFVG/economia-imprese/agevolazioni-e-finanziamenti/",
        "selettore_lista": ".bando, li, article",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Trentino-Alto Adige",
        "url": "https://www.regione.taa.it/it/economia-e-lavoro/bandi-contributi",
        "selettore_lista": ".bando, article, li",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Valle d'Aosta",
        "url": "https://www.regione.vda.it/aziende/bandi_contributi_i.aspx",
        "selettore_lista": ".bando, tr, li",
        "selettore_titolo": "h3, h2, td a, a",
        "selettore_link": "a",
        "selettore_data": "td, .data",
        "selettore_scadenza": ".scadenza, td.scadenza, [class*='scad']",
    },
    {
        "nome": "Marche",
        "url": "https://www.regione.marche.it/Regione-Utile/Bandi-di-gara-e-concorsi",
        "selettore_lista": "article, .bando-item, li",
        "selettore_titolo": "h3, h2, .titolo",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Abruzzo",
        "url": "https://www.regione.abruzzo.it/content/bandi-e-avvisi",
        "selettore_lista": "article, .bando, li",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Molise",
        "url": "https://www3.regione.molise.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/7290",
        "selettore_lista": "article, li, .bando",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Basilicata",
        "url": "https://www.basilicatanet.it/basilicata/bandi_e_gare.jsp",
        "selettore_lista": "article, li, .bando",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Calabria",
        "url": "https://www.regione.calabria.it/website/portaltemplates/view/view.cfm?14318",
        "selettore_lista": "article, li, .bando",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
    {
        "nome": "Umbria",
        "url": "https://www.regione.umbria.it/lavoro-economia/bandi-e-avvisi",
        "selettore_lista": "article, .bando, li",
        "selettore_titolo": "h3, h2, a",
        "selettore_link": "a",
        "selettore_data": ".data, time",
        "selettore_scadenza": ".scadenza, [class*='scad']",
    },
]



_PATTERN_SCADENZA = re.compile(
    r"(?:scadenza|scade il|termine[:\s]+|entro il|entro[:\s]+il|chiusura[:\s]+)"
    r"\s*[:\-]?\s*"
    r"(\d{1,2}[\s./\-]\w+[\s./\-]\d{2,4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.IGNORECASE,
)


def _estrai_scadenza_da_testo(testo: str) -> str:
    """Cerca una data di scadenza nel testo libero tramite regex."""
    m = _PATTERN_SCADENZA.search(testo)
    return m.group(1).strip() if m else ""


def genera_id(titolo: str, url: str) -> str:
    """Genera un ID univoco per un bando basato su titolo e URL."""
    contenuto = f"{titolo.strip().lower()}{url.strip().lower()}"
    return hashlib.md5(contenuto.encode()).hexdigest()


def carica_bandi_visti(filepath: str) -> set:
    """Carica il set dei bandi già visti dal file JSON."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("ids_visti", []))
    return set()


def salva_bandi_visti(filepath: str, ids: set):
    """Salva il set aggiornato dei bandi visti."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "ids_visti": list(ids),
            "ultimo_aggiornamento": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)


def scrape_regione(regione: dict) -> list[dict]:
    """Scrape una singola regione e restituisce i bandi trovati."""
    bandi = []
    try:
        logger.info(f"Scraping {regione['nome']}...")
        resp = requests.get(regione["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        elementi = soup.select(regione["selettore_lista"])

        if not elementi:
            # Fallback: cerca tutti i link con parole chiave bando
            elementi = soup.find_all("a", string=lambda t: t and any(
                k in t.lower() for k in ["bando", "avviso", "finanziamento", "contributo", "gara"]
            ))
            for el in elementi[:20]:
                href = el.get("href", "")
                if href and not href.startswith("#"):
                    url_completo = href if href.startswith("http") else f"{regione['url'].rstrip('/')}/{href.lstrip('/')}"
                    bandi.append({
                        "regione": regione["nome"],
                        "titolo": el.get_text(strip=True),
                        "url": url_completo,
                        "data": "",
                        "scadenza": "",
                        "fonte": regione["url"],
                    })
            return bandi

        for el in elementi[:30]:  # Massimo 30 bandi per regione
            try:
                # Titolo
                titolo_el = el.select_one(regione["selettore_titolo"])
                titolo = titolo_el.get_text(strip=True) if titolo_el else el.get_text(strip=True)[:150]

                if not titolo or len(titolo) < 5:
                    continue

                # Link
                link_el = el.select_one(regione["selettore_link"])
                href = link_el.get("href", "") if link_el else ""
                if not href:
                    href = el.get("href", "")
                url_bando = href if href.startswith("http") else f"{regione['url'].rstrip('/')}/{href.lstrip('/')}"

                # Data pubblicazione
                data_el = el.select_one(regione["selettore_data"])
                data_str = data_el.get_text(strip=True) if data_el else ""

                # Scadenza — selettore CSS dedicato, poi fallback regex sul testo
                scadenza_str = ""
                sel_scad = regione.get("selettore_scadenza", "")
                if sel_scad:
                    scad_el = el.select_one(sel_scad)
                    if scad_el:
                        scadenza_str = scad_el.get_text(strip=True)[:50]
                if not scadenza_str:
                    scadenza_str = _estrai_scadenza_da_testo(el.get_text(" ", strip=True))[:50]

                bandi.append({
                    "regione": regione["nome"],
                    "titolo": titolo[:200],
                    "url": url_bando,
                    "data": data_str[:50],
                    "scadenza": scadenza_str,
                    "fonte": regione["url"],
                })
            except Exception as e:
                logger.debug(f"Errore elemento in {regione['nome']}: {e}")
                continue

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout per {regione['nome']}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connessione fallita per {regione['nome']}")
    except Exception as e:
        logger.error(f"Errore scraping {regione['nome']}: {e}")

    logger.info(f"  → {len(bandi)} bandi trovati in {regione['nome']}")
    return bandi


def trova_nuovi_bandi(data_filepath: str = "data/bandi_visti.json") -> list[dict]:
    """
    Funzione principale: scrape tutte le regioni e restituisce solo i nuovi bandi.
    """
    ids_visti = carica_bandi_visti(data_filepath)
    tutti_bandi = []
    nuovi_bandi = []

    for regione in REGIONI:
        bandi = scrape_regione(regione)
        tutti_bandi.extend(bandi)
        time.sleep(1)  # Pausa cortesia tra le richieste

    for bando in tutti_bandi:
        bando_id = genera_id(bando["titolo"], bando["url"])
        if bando_id not in ids_visti:
            nuovi_bandi.append(bando)
            ids_visti.add(bando_id)

    salva_bandi_visti(data_filepath, ids_visti)

    logger.info(f"Totale bandi trovati: {len(tutti_bandi)}, Nuovi: {len(nuovi_bandi)}")
    return nuovi_bandi


if __name__ == "__main__":
    nuovi = trova_nuovi_bandi()
    print(f"\nNuovi bandi trovati: {len(nuovi)}")
    for b in nuovi:
        print(f"  [{b['regione']}] {b['titolo'][:80]}")
