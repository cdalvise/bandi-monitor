"""
Script principale — Monitor Bandi Regionali Italiani
Esegui questo file per avviare il controllo manualmente o tramite scheduler.
"""

import sys
import logging
from scraper import trova_nuovi_bandi
from filtro import filtra_bandi
from excel_export import esporta_excel
from notifica_email import invia_da_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

EXCEL_PATH = "data/bandi_export.xlsx"


def main():
    logger.info("=" * 60)
    logger.info("  MONITOR BANDI REGIONALI ITALIANI")
    logger.info("=" * 60)

    # 1. Scrape tutte le regioni
    logger.info("\n📡 Avvio scraping siti regionali...")
    nuovi_bandi = trova_nuovi_bandi(data_filepath="data/bandi_visti.json")

    if not nuovi_bandi:
        logger.info("\n✅ Nessun nuovo bando oggi. Nessuna azione necessaria.")
        logger.info("=" * 60)
        return

    logger.info(f"\n🔍 Trovati {len(nuovi_bandi)} nuovi bandi. Applico filtri...")

    # 2. Filtra per parole chiave
    bandi_filtrati, stats_filtro = filtra_bandi(nuovi_bandi)

    if stats_filtro.get("filtro_attivo"):
        logger.info(
            f"   Filtro: {stats_filtro['totale_prima']} totali → "
            f"{stats_filtro['filtrati']} corrispondenze "
            f"({stats_filtro['esclusi']} esclusi)"
        )

    if not bandi_filtrati:
        logger.info("\n✅ Nessun bando corrisponde alle parole chiave configurate.")
        logger.info("=" * 60)
        return

    # 3. Esporta in Excel
    logger.info(f"\n📊 Esporto {len(bandi_filtrati)} bandi in Excel...")
    try:
        percorso_excel = esporta_excel(bandi_filtrati, filepath=EXCEL_PATH, storico=True)
        logger.info(f"   ✅ Excel salvato: {percorso_excel}")
    except Exception as e:
        logger.error(f"   ⚠️  Errore export Excel: {e}")
        percorso_excel = None

    # 4. Invia notifica email
    logger.info(f"\n📬 Invio notifica email per {len(bandi_filtrati)} bandi...")
    successo = invia_da_env(bandi_filtrati, stats_filtro=stats_filtro, excel_path=percorso_excel)

    if successo:
        logger.info("✅ Processo completato con successo!")
    else:
        logger.error("⚠️  Bandi trovati ma errore nell'invio email.")
        sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
