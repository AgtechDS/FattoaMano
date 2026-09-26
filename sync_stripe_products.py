"""
==============================================================================
FATTO A MANO — STRIPE PRODUCTS SYNC & VERIFICATION TOOL
==============================================================================
Testa le credenziali Stripe configurate in .env, crea i prodotti e i relativi
prezzi su Stripe, e aggiorna i record in Supabase e nella cache locale.
==============================================================================
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Forza codifica UTF-8 su Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent
ENV_FILE = WORKSPACE_DIR / ".env"
CACHE_FILE = WORKSPACE_DIR / "products_cache.json"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")).strip()

try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    print("[Error] stripe module non installato")
    sys.exit(1)

try:
    from supabase import create_client
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None
except Exception:
    supabase_client = None


def test_stripe_connection():
    """Verifica l'autenticità e le autorizzazioni della chiave Stripe."""
    print("=" * 60)
    print("  VERIFICA CONNESSIONE STRIPE API")
    print(f"  Key Type: {'Live Key (rk_live / sk_live)' if 'live' in STRIPE_SECRET_KEY else 'Test Key'}")
    print(f"  Key Preview: {STRIPE_SECRET_KEY[:8]}...{STRIPE_SECRET_KEY[-6:]}")
    print("=" * 60)

    try:
        existing_products = stripe.Product.list(limit=5)
        print("[Stripe] Connessione riuscita!")
        print(f"[Stripe] Prodotti rilevati sul conto Stripe: {len(existing_products.data)}")
        for p in existing_products.data:
            print(f"  - ID: {p.id} | Nome: {p.name}")
        return True
    except stripe.AuthenticationError as e:
        print(f"[Stripe Auth Error]: {e}")
        return False
    except stripe.PermissionError as e:
        print(f"[Stripe Permission Error]: {e}")
        return False
    except Exception as e:
        print(f"[Stripe Error]: {e}")
        return False


def sync_products_to_stripe():
    """Crea o sincronizza i prodotti dell'atelier Fatto a Mano su Stripe."""
    if not CACHE_FILE.exists():
        print("[Error] products_cache.json non trovato!")
        return []

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Recupera i prodotti esistenti su Stripe per evitare duplicati
    try:
        existing = stripe.Product.list(limit=100)
        existing_map = {p.name.strip().lower(): p for p in existing.data}
    except Exception as e:
        print(f"[Warning] Impossibile listare prodotti esistenti: {e}")
        existing_map = {}

    updated = False

    print("\n" + "=" * 60)
    print("  CREAZIONE / SINCRONIZZAZIONE PRODOTTI SU STRIPE")
    print("=" * 60)

    for item in products:
        title = item["title"].strip()
        price = float(item["price"])
        price_cents = int(price * 100)
        item_id = item["id"]
        norm_title = title.lower()

        stripe_prod = existing_map.get(norm_title)

        if not stripe_prod:
            print(f"\n[Stripe Create] Creazione Prodotto: '{title}' (€{price:.2f})...")
            try:
                stripe_prod = stripe.Product.create(
                    name=title,
                    description=item.get("description", "Bracciale in puro rame 99.9% forgiato a mano Fatto a Mano"),
                    metadata={
                        "fattoamano_id": item_id,
                        "purity": item.get("purity", "99.9% Rame Puro"),
                        "category": item.get("category", "Intrecciati"),
                        "brand": "Fatto a Mano Atelier"
                    }
                )
                print(f"  [+] Creato Prodotto Stripe ID: {stripe_prod.id}")
            except Exception as e:
                print(f"  [!] Errore creazione prodotto: {e}")
                continue
        else:
            print(f"\n[Stripe Found] Prodotto già presente su Stripe: '{title}' -> ID: {stripe_prod.id}")

        # Verifica se esiste già un prezzo associato o creane uno
        stripe_price_id = item.get("stripe_price_id")
        if not stripe_price_id:
            try:
                prices = stripe.Price.list(product=stripe_prod.id, active=True, limit=5)
                matching_price = next((pr for pr in prices.data if pr.unit_amount == price_cents and pr.currency == "eur"), None)
                
                if matching_price:
                    stripe_price_id = matching_price.id
                    print(f"  [+] Prezzo corrispondente trovato: {stripe_price_id}")
                else:
                    new_price = stripe.Price.create(
                        product=stripe_prod.id,
                        unit_amount=price_cents,
                        currency="eur"
                    )
                    stripe_price_id = new_price.id
                    print(f"  [+] Creato Nuovo Prezzo Stripe ID: {stripe_price_id} (€{price:.2f})")
            except Exception as e:
                print(f"  [!] Errore gestione prezzo: {e}")

        # Aggiorna record
        if item.get("stripe_product_id") != stripe_prod.id or item.get("stripe_price_id") != stripe_price_id:
            item["stripe_product_id"] = stripe_prod.id
            item["stripe_price_id"] = stripe_price_id
            updated = True

            # Aggiorna anche in Supabase se collegato
            if supabase_client:
                try:
                    supabase_client.table("fattoamano_products").update({
                        "stripe_product_id": stripe_prod.id,
                        "stripe_price_id": stripe_price_id
                    }).eq("id", item_id).execute()
                    print(f"  [Supabase Sync] Aggiornato record {item_id} con chiavi Stripe")
                except Exception as e:
                    print(f"  [Supabase Sync Warning]: {e}")

    # Salva cache locale aggiornata
    if updated:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print("\n[Cache Updated] products_cache.json aggiornato con Stripe IDs!")

    return products


def test_create_checkout_session(sample_product):
    """Testa la creazione di una Checkout Session reale con Stripe."""
    print("\n" + "=" * 60)
    print("  TEST CHECKOUT SESSION UFFICIALE")
    print("=" * 60)

    price_id = sample_product.get("stripe_price_id")
    if not price_id:
        print("[Warning] Nessun stripe_price_id disponibile per il test di checkout")
        return None

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="payment",
            success_url="http://localhost:8092/success.html",
            cancel_url="http://localhost:8092/",
        )
        print(f"[Stripe Checkout OK] Checkout Session creata con successo!")
        print(f"  - Prodotto: {sample_product.get('title')}")
        print(f"  - Session ID: {session.id}")
        print(f"  - URL di Pagamento Ufficiale: {session.url}")
        print(f"  - Importo: €{session.amount_total / 100:.2f} {session.currency.upper()}")
        return session.url
    except Exception as e:
        print(f"[Stripe Checkout Error]: {e}")
        return None


if __name__ == "__main__":
    ok = test_stripe_connection()
    if not ok:
        print("\n[Errore] Connessione a Stripe fallita. Verifica i permessi della chiave.")
        sys.exit(1)

    prods = sync_products_to_stripe()
    if prods and len(prods) > 0:
        first_with_price = next((p for p in prods if p.get("stripe_price_id")), None)
        if first_with_price:
            test_create_checkout_session(first_with_price)
