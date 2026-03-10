# 🏛️ Monitor Bandi Regionali Italiani

Monitora automaticamente ogni giorno i siti ufficiali delle **20 regioni italiane** e ti invia una **notifica email** con tutti i nuovi bandi pubblicati.

## ✅ Funzionalità

- Scraping di tutti i siti regionali ufficiali (20 regioni)
- Rilevamento automatico dei nuovi bandi (nessuna duplicazione)
- Notifica email con layout HTML professionale, raggruppata per regione
- Esecuzione automatica ogni giorno alle 08:00 (ora italiana) via GitHub Actions
- Completamente **gratuito** — non richiede server o abbonamenti

---

## 🚀 Setup in 5 minuti

### Prerequisiti
- Un account [GitHub](https://github.com) (gratuito)
- Un account Gmail (o altro provider email con SMTP)

---

### Step 1 — Carica il progetto su GitHub

1. Crea un nuovo repository su GitHub (es. `bandi-monitor`)
2. Carica tutti i file di questo progetto nel repository
3. Assicurati che la struttura sia:
   ```
   bandi-monitor/
   ├── .github/
   │   └── workflows/
   │       └── monitor.yml
   ├── data/
   │   └── bandi_visti.json
   ├── main.py
   ├── scraper.py
   ├── notifica_email.py
   └── requirements.txt
   ```

---

### Step 2 — Configura Gmail per l'invio email

> ⚠️ **Non usare la password normale di Gmail.** Devi creare una "App Password".

1. Vai su [myaccount.google.com](https://myaccount.google.com)
2. **Sicurezza** → **Verifica in due passaggi** (deve essere attiva)
3. Cerca **"App Password"** → Crea una nuova password per "Altro (nome personalizzato)"
4. Copia la password di 16 caratteri generata

---

### Step 3 — Aggiungi i Secrets su GitHub

1. Nel tuo repository GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Clicca **"New repository secret"** e aggiungi questi 3 secrets:

| Nome Secret | Valore |
|---|---|
| `EMAIL_MITTENTE` | La tua email Gmail (es. `tuonome@gmail.com`) |
| `EMAIL_PASSWORD` | La App Password di 16 caratteri (Step 2) |
| `EMAIL_DESTINATARI` | Email/e che ricevono le notifiche (es. `tu@email.it` oppure `a@email.it,b@email.it` per più destinatari) |

---

### Step 4 — Attiva GitHub Actions

1. Nel repository → tab **Actions**
2. Se appare un avviso "Workflows disabled", clicca **"I understand my workflows, go ahead and enable them"**
3. Clicca sul workflow **"Monitor Bandi Regionali"** → **"Run workflow"** per testarlo subito!

---

## ⏰ Quando viene eseguito?

Il monitor gira automaticamente ogni giorno alle **08:00 ora italiana**.

Se vuoi cambiare orario, modifica la riga `cron` in `.github/workflows/monitor.yml`:
```yaml
# Formato: minuto ora giorno mese giorno_settimana
- cron: '0 7 * * *'   # 07:00 UTC = 08:00 CET / 09:00 CEST
```

Per eseguirlo manualmente: tab **Actions** → **"Monitor Bandi Regionali"** → **"Run workflow"**.

---

## 📬 Esempio di notifica email

L'email che ricevi contiene:
- Numero totale di nuovi bandi trovati
- Bandi raggruppati per regione
- Titolo, data e link diretto al bando originale

---

## 🔧 Esecuzione locale

```bash
# Installa dipendenze
pip install -r requirements.txt

# Configura variabili d'ambiente
export EMAIL_MITTENTE="tua@gmail.com"
export EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
export EMAIL_DESTINATARI="destinatario@email.it"

# Esegui
python main.py
```

---

## 🗺️ Regioni monitorate

| | | | |
|---|---|---|---|
| Abruzzo | Basilicata | Calabria | Campania |
| Emilia-Romagna | Friuli Venezia Giulia | Lazio | Liguria |
| Lombardia | Marche | Molise | Piemonte |
| Puglia | Sardegna | Sicilia | Toscana |
| Trentino-Alto Adige | Umbria | Valle d'Aosta | Veneto |

---

## ❓ FAQ

**Non ricevo email anche se ci sono nuovi bandi?**
Controlla che i Secrets siano scritti correttamente. Prova l'esecuzione manuale dal tab Actions e guarda i log.

**Ricevo un errore di autenticazione Gmail?**
Assicurati di usare l'App Password (16 caratteri) e non la password normale. La verifica in due passaggi deve essere attiva.

**Come aggiungo una regione non inclusa?**
Modifica `scraper.py` aggiungendo un nuovo dizionario nella lista `REGIONI` con URL e selettori CSS del sito.

**Il workflow non parte automaticamente?**
GitHub potrebbe disabilitare i workflow schedulati se il repository non ha attività da 60 giorni. Esegui manualmente ogni tanto per tenerlo attivo.
