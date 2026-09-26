# Fatto a Mano — Boutique Orafa del Rame Puro (99.9%)

> **E-Commerce Web App Dark Luxury + Automazione Telegram AGOS con Supabase e Stripe**

---

## 💎 Panoramica del Progetto

**Fatto a Mano** è una boutique e-commerce esclusiva, progettata con stile **Dark Luxury & Copper Glow** per valorizzare bracciali artigianali in puro rame al 99.9%.

Il sistema elimina qualsiasi form macchinoso di caricamento: l'artigiano scatta una foto al bracciale e la invia al bot Telegram AGOS (`telegram-agos.py`). L'agente autonomo elabora il prompt naturale, carica la foto su **Supabase Storage**, registra il prodotto e prezzo su **Stripe**, memorizza i dati nel database **Supabase** e aggiorna in tempo reale la vetrina web, eseguendo un ciclo di verifica formale con notifica di conferma.

---

## 🌟 Caratteristiche Principali

1. **Design System Sartoriale (Dark Luxury & Copper Glow):**
   - Palette cromatica: Rame Nobile (`#c87d55`, `#d9824c`, `#e8986a`) su Carbone profondo (`#0a0a0c`, `#121216`).
   - Nessun colore fuori tema (rispetto rigoroso della Purple Ban).
   - Tipografia editoriale d'alta gioielleria (*Cormorant Garamond* + *Plus Jakarta Sans*).
   - Animazioni di lucentezza metallica, micro-interazioni e rendering responsive da mobile a desktop.

2. **Esperienza di Acquisto Fluida:**
   - **Slide-over Drawer Cart**: carrello laterale estraibile con blur di sfondo, controlli quantità e calcolatore soglia spedizione assicurata gratuita.
   - **Stripe Checkout Ufficiale**: integrazione con Stripe Checkout Sessions (`/api/create-checkout-session`) per pagamenti protetti e crittografati a 256-bit.
   - **Modal Dettaglio con Certificato**: scheda tecnica e Certificato di Autenticità Digitale per ogni pezzo unico.
   - **Filtri Rapidi**: Intrecciati, Martellati, Rigidi.

3. **Integrazione Cloud Supabase:**
   - Tabella `public.fattoamano_products` con RLS abilitata per lettura pubblica.
   - Storage Bucket `fattoamano-products` (pubblico) con CDN globale per le immagini.
   - Resiliente offline con cache sincronizzata `products_cache.json`.

4. **Automazione Telegram AGOS (`telegram-agos.py`):**
   - Invia la foto al bot Telegram allegando il prompt operativo, ad esempio:
     ```text
     aggiungi prodotto a sito FattoAMano prezzo 30E dettagli "bracciale in rame 3 filamenti rame puro 99.9%"
     ```
   - Parsing intelligente di prezzo, categoria, titolo e specifiche.
   - Caricamento automatico su Supabase + Stripe.
   - **Verifica automatica a 4 fattori**:
     - `image_file_ok` (acquisizione locale integra)
     - `image_url_ok` (HTTP 200 CDN Supabase)
     - `cache_synced` (database e cache coerenti)
     - `stripe_status` (gateway verificato)
   - Risposta Telegram con report di integrità e link immediato alla boutique live.

---

## 🚀 Avvio Rapido

### 1. Avviare la Boutique Web
Dalla cartella `Workspace/FattoAMano`:
```cmd
start_fattoamano.bat
```
oppure da riga di comando:
```bash
python Workspace/FattoAMano/server.py 8092
```
Apri il browser su: **http://localhost:8092**

### 2. Avviare il Bot Telegram AGOS
Dalla root o dalla cartella `Workspace/FattoAMano`:
```cmd
start_telegram_fattoamano.bat
```
oppure da riga di comando:
```bash
python telegram-agos.py
```

### 3. Test Rapido della Pipeline via CLI
Per testare la pubblicazione immediata senza aprire Telegram:
```bash
python telegram-agos.py --cli
```

### 4. Eseguire la Test Suite Completa
```bash
python Workspace/FattoAMano/test_suite.py
```

---

## 📁 Struttura File

```
Workspace/FattoAMano/
├── index.html                   # Web App Single Page E-Commerce
├── style.css                    # Dark Luxury & Copper Glow Design System
├── app.js                       # Logica carrello reattivo, drawer, Stripe & Supabase
├── success.html                 # Pagina di conferma ordine Stripe Checkout
├── server.py                    # Server HTTP & API REST (/api/products, /api/create-checkout-session)
├── telegram-agos.py             # Daemon Telegram AGOS con auto-verifica
├── schema.sql                   # Schema DDL Supabase & Storage Policies
├── products_cache.json          # Cache locale & Seeding iniziale
├── test_suite.py                # Test automatizzati a 5 livelli
├── start_fattoamano.bat         # Launcher Windows Store Web
├── start_telegram_fattoamano.bat# Launcher Windows Bot Telegram
└── assets/                      # Immagini HD bracciali in puro rame 99.9%
```
