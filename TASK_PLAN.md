# Task Plan: FattoAMano — Luxury Copper E-Commerce & AGOS Telegram Integration

> **Workspace:** `Workspace/FattoAMano`  
> **Status:** In Execution  
> **Primary Agents:** `orchestrator`, `frontend-specialist`, `backend-specialist`

---

## 1. Vision & Architecture Overview

FattoAMano is an exclusive e-commerce boutique dedicated to bespoke, hand-forged 99.9% pure copper jewelry, paired with an autonomous Telegram Bridge (`telegram-agos.py`). The artisan directly uploads product photos, prices, and specifications via Telegram, which are automatically parsed, uploaded to Supabase Storage, cataloged in Supabase DB, registered on Stripe, and rendered live on the website with instant verification.

### Tech Stack
- **Frontend:** HTML5 Semantic, Bespoke Modern CSS (Dark Luxury & Copper Glow aesthetic, Rame Nobile & Carbone palette, CSS custom properties, fluid typography, no standard templates, micro-interactions, responsive design), Modular Vanilla JavaScript with reactive cart state.
- **Backend API:** Python lightweight HTTP/FastAPI microservice (`server.py`) handling Stripe Checkout sessions, dynamic product querying, and local cache synchronization.
- **Database & Storage:** Supabase PostgreSQL table `fattoamano_products`, public Storage bucket `fattoamano-products`, and resilient local fallback `products_cache.json`.
- **Payment Gateway:** Stripe Checkout Sessions with direct redirect and cart line items.
- **Telegram Bot Automation:** `telegram-agos.py` listening to photo uploads with structured natural language prompts (e.g., *"aggiungi prodotto a sito FattoAMano prezzo 30E dettagli "bracciale in rame 3 filamenti rame puro 99.9%"*).

---

## 2. Phase Breakdown & Execution Steps

### Phase 1: Database Schema & Storage Setup (Supabase)
- [x] Create SQL schema file `schema.sql` defining `fattoamano_products` table and storage policies.
- [ ] Create Python setup script `setup_supabase.py` to create the bucket and tables automatically via Supabase API / MCP.
- [ ] Initialize `products_cache.json` with initial luxury showcase products featuring the generated photorealistic copper jewelry assets.

### Phase 2: High-End Web App Frontend
- [ ] Copy generated high-res jewelry images to `Workspace/FattoAMano/assets/`.
- [ ] Implement `index.html`:
  - Luxury Editorial Navbar with Brand Crest and interactive Cart Drawer trigger.
  - Cinematic Hero Section featuring pure copper glow, brand manifesto ("Forgiato a Mano • 99.9% Rame Puro").
  - Filterable Product Gallery (Tutti, Intrecciati, Martellati, Rigidi).
  - Dynamic Product Cards with hover metallic shimmer, carature/purity badges, and "Aggiungi al Carrello" / "Acquista Ora".
  - Interactive Slide-over Drawer Cart with quantity controls, subtotal, free insured shipping threshold, and Stripe Checkout button.
  - High-res Product Detail Modal with digital certificate of authenticity.
  - Toast notification engine with copper border styling.
- [ ] Implement `style.css`:
  - Custom design tokens (Charcoal `#0d0d0f`, Copper `#c87d55`, Rose Glow `#d9824c`, Sand `#f4ece1`).
  - No purple/violet accents (per design rules).
  - Glassmorphic backdrop filters, custom scrollbars, and fluid animations.
- [ ] Implement `app.js`:
  - Supabase REST client with automatic fallback to local JSON cache.
  - Shopping cart state persistence in `localStorage`.
  - Stripe checkout trigger.

### Phase 3: Stripe Backend API & Local Server
- [ ] Implement `server.py`:
  - Serves static assets and provides REST API endpoints:
    - `POST /api/create-checkout-session`: generates Stripe Checkout URL.
    - `GET /api/products`: returns product list from Supabase or local cache.
    - `GET /api/health`: diagnostics.

### Phase 4: Autonomous Telegram Bridge (`telegram-agos.py`)
- [ ] Implement `telegram-agos.py`:
  - Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_ID` from `.env`.
  - Photo message handler with smart regex + NLP parser:
    - Detects: `aggiungi prodotto [a sito FattoAMano] prezzo [30E / 30€ / 30 eur] dettagli [titolo / specifiche]`.
  - Downloads high-resolution photo from Telegram.
  - Uploads photo directly to Supabase Storage bucket `fattoamano-products`.
  - Creates Product and Price in Stripe API.
  - Inserts product record into Supabase `fattoamano_products`.
  - Updates `products_cache.json` so web app immediately updates without restart.
  - Formal Verification Loop: tests HTTP 200 on image URL, verifies DB entry, verifies Stripe price.
  - Sends rich Telegram feedback message with live verification report.

### Phase 5: Verification, Testing & Launch
- [ ] Run test suite verifying frontend rendering, cart functionality, and telegram parser.
- [ ] Provide one-click launcher scripts: `start_app.bat` and `start_telegram.bat`.
