"""
Modulo per l'invio delle notifiche email sui nuovi bandi regionali.
Usa Gmail SMTP (o qualsiasi provider SMTP).
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def raggruppa_per_regione(bandi: list[dict]) -> dict:
    per_regione = {}
    for b in bandi:
        regione = b.get("regione", "Sconosciuta")
        if regione not in per_regione:
            per_regione[regione] = []
        per_regione[regione].append(b)
    return dict(sorted(per_regione.items()))


def _tag_parole(parole: list[str]) -> str:
    if not parole:
        return ""
    badges = "".join(
        f'<span style="display:inline-block; background:#e8f5e9; color:#2e7d32; '
        f'font-size:10px; padding:2px 7px; border-radius:10px; margin:2px 2px 0 0; '
        f'border:1px solid #a5d6a7;">{p}</span>'
        for p in parole
    )
    return f'<div style="margin-top:5px;">{badges}</div>'


def _banner_filtro(stats: dict) -> str:
    if not stats or not stats.get("filtro_attivo"):
        return ""
    parole = stats.get("parole_chiave", [])
    totale = stats.get("totale_prima", 0)
    filtrati = stats.get("filtrati", 0)
    esclusi = stats.get("esclusi", 0)
    etichette = " ".join(
        f'<span style="background:rgba(255,255,255,0.25); padding:2px 8px; '
        f'border-radius:10px; font-size:11px; margin:2px;">{p}</span>'
        for p in parole[:10]
    )
    return f"""
    <div style="background:linear-gradient(135deg,#2e7d32,#43a047); color:white;
                padding:14px 20px; border-radius:8px; margin-bottom:20px; font-size:13px;">
      <strong>🔍 Filtro attivo</strong> — {filtrati} bandi su {totale} corrispondono
      <span style="float:right; opacity:0.85; font-size:12px;">{esclusi} esclusi</span>
      <div style="margin-top:8px; line-height:1.8;">{etichette}</div>
    </div>"""


def genera_html(bandi: list[dict], stats_filtro: Optional[dict] = None) -> str:
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    per_regione = raggruppa_per_regione(bandi)

    sezioni_html = ""
    for regione, lista in per_regione.items():
        righe = ""
        for b in lista:
            titolo = b.get("titolo", "N/D")
            url = b.get("url", "#")
            data = b.get("data", "")
            parole = b.get("parole_trovate", [])
            data_html = f'<span style="color:#888; font-size:12px;">📅 {data}</span>' if data else ""
            tags_html = _tag_parole(parole)
            righe += f"""
            <tr>
              <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0; vertical-align:top;">
                <a href="{url}" style="color:#1a73e8; text-decoration:none; font-weight:500; font-size:14px;">{titolo}</a>
                <br>{data_html}
                {tags_html}
                <br><span style="color:#aaa; font-size:11px;">{url[:80]}{'...' if len(url) > 80 else ''}</span>
              </td>
            </tr>"""

        sezioni_html += f"""
        <div style="margin-bottom:28px;">
          <div style="background:#1a73e8; color:white; padding:10px 16px; border-radius:6px 6px 0 0;">
            <strong>🗺️ {regione}</strong>
            <span style="float:right; font-size:12px; opacity:0.8;">{len(lista)} nuovo/i bando/i</span>
          </div>
          <table style="width:100%; border-collapse:collapse; background:white; border:1px solid #e8e8e8; border-top:none; border-radius:0 0 6px 6px; overflow:hidden;">
            {righe}
          </table>
        </div>"""

    banner = _banner_filtro(stats_filtro)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#f5f7fa;margin:0;padding:20px;">
  <div style="max-width:700px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#1a73e8 0%,#0d47a1 100%);color:white;padding:28px 32px;border-radius:12px 12px 0 0;text-align:center;">
      <div style="font-size:36px;margin-bottom:8px;">🏛️</div>
      <h1 style="margin:0;font-size:22px;font-weight:700;">Monitor Bandi Regionali</h1>
      <p style="margin:8px 0 0;opacity:0.85;font-size:14px;">{data_oggi} — {len(bandi)} nuovi bandi in {len(per_regione)} regioni</p>
    </div>
    <div style="background:#f5f7fa;padding:24px 0;">
      {banner}
      {sezioni_html}
    </div>
    <div style="background:#e8ecf0;padding:16px 24px;border-radius:0 0 12px 12px;text-align:center;">
      <p style="margin:0;font-size:12px;color:#666;">
        Notifica automatica — <strong>Monitor Bandi Regionali Italiani</strong><br>
        Modifica parole chiave in <code>config.json</code> · Disabilita da GitHub Actions.
      </p>
    </div>
  </div>
</body></html>"""
    return html


def genera_testo_plain(bandi: list[dict], stats_filtro: Optional[dict] = None) -> str:
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    per_regione = raggruppa_per_regione(bandi)
    lines = [f"MONITOR BANDI REGIONALI ITALIANI — {data_oggi}", f"Trovati {len(bandi)} nuovi bandi"]
    if stats_filtro and stats_filtro.get("filtro_attivo"):
        lines.append(f"Filtro: {stats_filtro['filtrati']}/{stats_filtro['totale_prima']} corrispondenze")
    lines += ["=" * 60, ""]
    for regione, lista in per_regione.items():
        lines.append(f"📍 {regione.upper()} ({len(lista)} bandi)")
        lines.append("-" * 40)
        for b in lista:
            lines.append(f"• {b.get('titolo', 'N/D')}")
            if b.get("data"):
                lines.append(f"  Data: {b['data']}")
            if b.get("parole_trovate"):
                lines.append(f"  Parole chiave: {', '.join(b['parole_trovate'])}")
            lines.append(f"  Link: {b.get('url', 'N/D')}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


def invia_email(
    bandi: list[dict],
    mittente: str,
    destinatari: list[str],
    password_smtp: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
    oggetto_prefisso: str = "🏛️ Nuovi Bandi Regionali",
    stats_filtro: Optional[dict] = None,
    excel_path: Optional[str] = None,
) -> bool:
    if not bandi:
        logger.info("Nessun nuovo bando da notificare.")
        return True

    data_oggi = datetime.now().strftime("%d/%m/%Y")
    oggetto = f"{oggetto_prefisso} — {len(bandi)} nuovi ({data_oggi})"

    msg = MIMEMultipart("mixed")
    msg["Subject"] = oggetto
    msg["From"] = mittente
    msg["To"] = ", ".join(destinatari)

    corpo = MIMEMultipart("alternative")
    corpo.attach(MIMEText(genera_testo_plain(bandi, stats_filtro), "plain", "utf-8"))
    corpo.attach(MIMEText(genera_html(bandi, stats_filtro), "html", "utf-8"))
    msg.attach(corpo)

    if excel_path and os.path.exists(excel_path):
        from email.mime.base import MIMEBase
        from email import encoders
        nome_file = f"bandi_{datetime.now().strftime('%Y%m%d')}.xlsx"
        with open(excel_path, "rb") as f:
            allegato = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            allegato.set_payload(f.read())
        encoders.encode_base64(allegato)
        allegato.add_header("Content-Disposition", f'attachment; filename="{nome_file}"')
        msg.attach(allegato)
        logger.info(f"📎 Excel allegato: {nome_file}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(mittente, password_smtp)
            server.sendmail(mittente, destinatari, msg.as_string())
        logger.info(f"✅ Email inviata con successo a {', '.join(destinatari)}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Errore autenticazione SMTP. Verifica email e password.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ Errore SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Errore generico invio email: {e}")
        return False


def invia_da_env(
    bandi: list[dict],
    stats_filtro: Optional[dict] = None,
    excel_path: Optional[str] = None,
) -> bool:
    mittente = os.environ.get("EMAIL_MITTENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    destinatari_raw = os.environ.get("EMAIL_DESTINATARI", "")
    destinatari = [e.strip() for e in destinatari_raw.split(",") if e.strip()]

    if not all([mittente, password, destinatari]):
        logger.error("❌ Variabili d'ambiente mancanti: EMAIL_MITTENTE, EMAIL_PASSWORD, EMAIL_DESTINATARI")
        return False

    return invia_email(bandi, mittente, destinatari, password, stats_filtro=stats_filtro, excel_path=excel_path)
