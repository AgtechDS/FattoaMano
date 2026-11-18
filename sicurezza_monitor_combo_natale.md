# TASK PLAN: Sicurezza Totale, Cifratura codX+ Hemdal, Stripe Live Monitor, Combo Natale 100€ & Sponsor

## Obiettivo Generale
Implementare sul sito `agtechdesigne.shop` (progetto `Workspace/FattoAMano`):
1. Hardening di sicurezza MIT / EU (GDPR Art. 32, NIS2, PCI-DSS v4.0, CSP, HSTS, Rate Limiting).
2. Motore crittografico "codX+ Hemdal" per cifratura a riposo e firma di integrità dei dati ordini e PII cliente.
3. Monitor reale di ordini e report Stripe live (saldo, transazioni, conversioni reali).
4. Prodotto bundle dedicato "Combo Natale: Doppio Bracciale + Anello Trama Gemella" a 100€ con checkout Stripe.
5. Inserzione pubblicitaria grafica Dark Luxury Modern con badge micro-sponsor e promo Coming Soon.
6. Strategia di marketing multi-canale per la campagna natalizia.

---

## 1. Sicurezza & Crittografia codX+ Hemdal
- [x] Test connettività Stripe Live verificata con successo (livemode: true, saldo e transazioni reali).
- [ ] Implementazione modulo crittografico in `api/admin_security.py`:
  - Derivazione chiave PBKDF2 da secret di sessione.
  - Cifratura AES-256-GCM per payload PII cliente e ordini.
  - Firma di integrità HMAC-SHA512 (Hemdal integrity digest).
- [ ] Cifratura automatica degli ordini storici in `orders_audit.json`.
- [ ] Configurazione Header di sicurezza su `server.py` e `vercel.json` (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).

## 2. Monitor Ordini & Report Stripe Live
- [ ] Estensione `api/admin_orders.py`:
  - Endpoint `GET /api/admin_orders`: decifratura trasparente solo per sessioni admin autorizzate.
  - Endpoint `GET /api/admin/stripe-report`: recupero saldo Stripe reale, ultime transazioni e metriche.
- [ ] Aggiornamento `admin.html` e `admin.js`:
  - Sezione KPI Stripe (Saldo disponibile, Totale incassato, Transazioni riuscite/fallite).
  - Tabella ordini con status cifratura codX+ Hemdal verificato.

## 3. Scheda Prodotto Bundle Natale 100€ & Checkout
- [ ] Inserimento prodotto bundle in `products_cache.json` (€100.00, sconto natalizio da €135.00).
- [ ] Adattamento `api/create-checkout-session.py` per supportare il bundle con metadati regalo.
- [ ] Integrazione nel catalogo frontend `index.html` e `app.js`.

## 4. Inserzione Grafica & Micro-Sponsor
- [ ] Generazione visual Dark Luxury Modern ad alta definizione per la Combo Natale (Doppio bracciale + Anello trama coordinata).
- [ ] Applicazione nastro diagonale "COMING SOON PROMO NATALE" e slot microsponsor "Official Partner / AgTechDesigne".
- [ ] Salvataggio in `assets/promo_combo_natale_ad.png`.

## 5. Strategia Marketing & Verification Loop
- [ ] Documento strategico con funnel, copy Meta/Instagram/TikTok e calendario promozionale.
- [ ] Test automatizzati di cifratura/decifratura, integrità Hemdal e checkout.
