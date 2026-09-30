#!/usr/bin/env python3
"""
==============================================================================
FATTO A MANO — AUTOMATED CATALOG FOLDER SYNC & CLOUD DEPLOYER
==============================================================================
Consente all'artigiano di copiare/incollare immagini nelle cartelle:
  - assets/Intrecciati/
  - assets/Martellati ossidati/ (o assets/Martellati/)
  - assets/rigidi/ (o assets/Rigidi/)
  - assets/ProntaConsegna/ (o sottocartelle 'prontaconsegna')

Il tool scansiona automaticamente le foto, genera le schede prodotto,
le carica su Supabase Storage e Database, aggiorna la cache e pubblica
il sito live su Vercel via GitHub in 1 solo comando!
==============================================================================
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# UTF-8 Console per Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = WORKSPACE_DIR / "assets"
CACHE_FILE = WORKSPACE_DIR / "products_cache.json"
ENV_FILE = WORKSPACE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mkeykuouwsbjezdgwskq.supabase.co").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")).strip()

try:
    from supabase import create_client
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None
except Exception as e:
    supabase_client = None

# File di sistema/asset da escludere dalla scansione prodotti
SYSTEM_EXCLUDED_FILES = {
    "favicon.ico", "favicon.svg", "favicon-16x16.png", "favicon-32x32.png", 
    "apple-touch-icon.png", "photo_5_2026-09-27_20-01-48.jpg"
}

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DEFAULT_CATEGORY_TEMPLATES = {
    "Intrecciati": {
        "title": "Bracciale Intrecciato Rame Puro 99.9%",
        "price": 30.00,
        "description": "Forgiato a mano con filamenti di puro rame 99.9% ritorti a caldo. Finitura biologica protettiva con cera d'api vergine e chiusura ergonomica.",
        "details": "Trefoli ritorti a caldo • Chiusura anatomica • Finitura naturale",
        "stock_qty": 2
    },
    "Martellati": {
        "title": "Cuff Martellato Ossidato",
        "price": 45.00,
        "description": "Fascia solida in rame grezzo battuta a caldo ad incudine con trama a nido d'ape. Una scultura viva da indossare a contatto con la pelle.",
        "details": "Larghezza fascia 18 mm • Spessore 2.5 mm • Bordo smussato a specchio",
        "stock_qty": 1
    },
    "Rigidi": {
        "title": "Bangle Minimal Rame Massiccio",
        "price": 25.00,
        "description": "Profilo circolare essenziale in puro rame elettrolitico purissimo al 99.9%, sagomato per adagiarsi morbidamente e favorire il benessere quotidiano.",
        "details": "Spessore 4 mm • Forgiatura calibrata anatomica • Lustro satinato caldo",
        "stock_qty": 3
    }
}


def clean_title_from_stem(stem: str, category: str) -> str:
    """Trasforma un nome file tipo 'bracciale_intrecciato_cuff' in un titolo elegante."""
    clean = re.sub(r'[\-_]+', ' ', stem)
    clean = re.sub(r'\b(photo|\d{4,})\b', '', clean, flags=re.IGNORECASE)
    words = [w.capitalize() for w in clean.split() if w]
    candidate = " ".join(words).strip()
    if len(candidate) < 6:
        return f"Bracciale {category} Rame Puro"
    return candidate


def detect_product_info(img_path: Path) -> Dict:
    """Analizza il path dell'immagine per dedurre categoria, pronta_consegna e metadati."""
    rel_path = img_path.relative_to(WORKSPACE_DIR)
    rel_parts = [p.lower() for p in rel_path.parts]
    filename_lower = img_path.name.lower()
    
    # 1. Deduci Categoria
    category = "Intrecciati"
    for part in rel_parts:
        if "martellat" in part:
            category = "Martellati"
            break
        elif "rigid" in part:
            category = "Rigidi"
            break
        elif "intrecc" in part:
            category = "Intrecciati"
            break

    # 2. Deduci Pronta Consegna
    is_pronta = False
    if any("pronta" in part for part in rel_parts) or "pronta" in filename_lower:
        is_pronta = True
    elif img_path.name in ["bracciale_3_filamenti.jpg", "bracciale_martellato.jpg", "bracciale_rigido_puro.jpg"]:
        is_pronta = True

    # 3. Controlla eventuale sidecar .json o .txt (opzionale)
    sidecar_json = img_path.with_suffix('.json')
    meta_override = {}
    if sidecar_json.exists():
        try:
            with open(sidecar_json, 'r', encoding='utf-8') as f:
                meta_override = json.load(f)
        except Exception:
            pass

    tmpl = DEFAULT_CATEGORY_TEMPLATES.get(category, DEFAULT_CATEGORY_TEMPLATES["Intrecciati"])
    stem = img_path.stem
    derived_title = clean_title_from_stem(stem, category)

    # Identificativo univoco stabile
    clean_stem = re.sub(r'[^a-zA-Z0-9_]', '_', stem.lower()).strip('_')
    prod_id = meta_override.get("id") or f"prod_{category.lower()[:4]}_{clean_stem}"

    title = meta_override.get("title", derived_title if derived_title else tmpl["title"])
    price = float(meta_override.get("price", tmpl["price"]))
    description = meta_override.get("description", tmpl["description"])
    details = meta_override.get("details", tmpl["details"])
    stock_qty = int(meta_override.get("stock_qty", tmpl["stock_qty"]))
    purity = meta_override.get("purity", "99.9% Rame Puro")
    
    if "pronta_consegna" in meta_override:
        is_pronta = bool(meta_override["pronta_consegna"])

    # Path web relativo (per Next.js/Vercel)
    web_image_url = str(rel_path).replace("\\", "/")

    return {
        "id": prod_id,
        "title": title,
        "description": description,
        "price": price,
        "currency": "EUR",
        "image_url": web_image_url,
        "local_path": img_path,
        "purity": purity,
        "category": category,
        "details": details,
        "in_stock": True,
        "pronta_consegna": is_pronta,
        "stock_qty": stock_qty,
        "shipping_note": "Disponibile in bottega • Spedizione espressa tracciata 3-5 giorni lavorativi" if is_pronta else "Forgiato su misura • Consegna tracciata 3-5 giorni lavorativi"
    }


def upload_to_supabase_storage(local_path: Path, filename: str) -> Optional[str]:
    """Carica l'immagine nel bucket Supabase 'fattoamano-products'."""
    bucket_name = "fattoamano-products"
    if not supabase_client:
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"

    try:
        with open(local_path, "rb") as f:
            file_bytes = f.read()

        supabase_client.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        url = supabase_client.storage.from_(bucket_name).get_public_url(filename)
        return url
    except Exception as e:
        # Fallback public URL
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"


def sync_catalog(auto_git: bool = True, force: bool = False):
    print("=" * 70)
    print("  🔨 FATTO A MANO — AGGIORNAMENTO AUTOMATICO CATALOGO & SITO")
    print("=" * 70)
    
    # 1. Carica la cache attuale per preservare id o customizzazioni
    existing_catalog = []
    existing_by_path = {}
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                existing_catalog = json.load(f)
                for item in existing_catalog:
                    existing_by_path[item.get("image_url")] = item
        except Exception as e:
            print(f"[Avviso]: Errore lettura cache: {e}")

    # 2. Trova tutte le immagini nelle cartelle
    found_images: List[Path] = []
    for ext in VALID_IMAGE_EXTENSIONS:
        found_images.extend(ASSETS_DIR.rglob(f"*{ext}"))
        found_images.extend(ASSETS_DIR.rglob(f"*{ext.upper()}"))

    # Rimuovi duplicati e file esclusi
    filtered_images = []
    seen = set()
    for img in found_images:
        resolved = img.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if img.name in SYSTEM_EXCLUDED_FILES:
            continue
        filtered_images.append(img)

    print(f"📸 Trovate {len(filtered_images)} immagini prodotto in {ASSETS_DIR.name}/")

    synced_products = []
    for img_path in sorted(filtered_images):
        prod = detect_product_info(img_path)
        web_path = prod["image_url"]

        # Se già esisteva nella cache, preserva id stabile e titolo se personalizzato
        if web_path in existing_by_path:
            old = existing_by_path[web_path]
            prod["id"] = old.get("id", prod["id"])
            if old.get("title") and not old.get("title").startswith("Bracciale"):
                prod["title"] = old.get("title")
            if "price" in old:
                prod["price"] = old.get("price")
            if "pronta_consegna" in old:
                prod["pronta_consegna"] = old.get("pronta_consegna")

        # 3. Carica su Supabase Storage
        remote_filename = f"{prod['id']}_{img_path.name}"
        remote_url = upload_to_supabase_storage(img_path, remote_filename)
        prod["remote_url"] = remote_url

        # Mostra anteprima riga
        badge = " [⚡ PRONTA CONSEGNA]" if prod["pronta_consegna"] else ""
        print(f"  ✓ [{prod['category']:12}] {prod['title']} - €{prod['price']:.2f}{badge}")
        
        # Elimina local_path prima di salvare in json
        prod_for_json = {k: v for k, v in prod.items() if k != "local_path"}
        synced_products.append(prod_for_json)

    # 4. Aggiorna products_cache.json
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(synced_products, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Aggiornato {CACHE_FILE.name} con {len(synced_products)} prodotti.")

    # 5. Sincronizza tabella Supabase
    if supabase_client:
        print("\n☁️ Sincronizzazione tabella Supabase 'fattoamano_products'...")
        success_db = 0
        for p in synced_products:
            db_record = {
                "id": p["id"],
                "title": p["title"],
                "description": p["description"],
                "price": p["price"],
                "currency": p.get("currency", "EUR"),
                "image_url": p["image_url"],
                "purity": p.get("purity", "99.9% Rame Puro"),
                "category": p.get("category", "Intrecciati"),
                "details": p.get("details", ""),
                "in_stock": p.get("in_stock", True),
                "pronta_consegna": p.get("pronta_consegna", False),
                "stock_qty": p.get("stock_qty", 1),
                "shipping_note": p.get("shipping_note", "")
            }
            try:
                supabase_client.table("fattoamano_products").upsert(db_record).execute()
                success_db += 1
            except Exception as e:
                print(f"  [DB Warning per {p['id']}]: {e}")
        print(f"  ✓ Sincronizzati {success_db}/{len(synced_products)} prodotti su Supabase DB.")

    # 6. Git Push automatico per deploy istantaneo su Vercel
    if auto_git:
        print("\n🚀 Avvio deploy automatico su GitHub & Vercel...")
        try:
            subprocess.run(["git", "add", "."], cwd=WORKSPACE_DIR, check=True)
            status_res = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=WORKSPACE_DIR, 
                capture_output=True, 
                text=True, 
                check=True
            )
            if status_res.stdout.strip():
                subprocess.run(
                    ["git", "commit", "-m", "Auto-sync catalogo Fatto a Mano: aggiornamento creazioni e pronta consegna"],
                    cwd=WORKSPACE_DIR,
                    check=True
                )
                print("  ✓ Commit effettuato.")
                subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, check=True)
                print("  ✓ Push su 'origin main' completato con successo!")
                print("\n✨ IL SITO LIVE SU VERCEL SI AGGIORNA AUTOMATICAMENTE IN ~30 SECONDI:")
                print("   👉 https://fattoamano-alpha.vercel.app")
            else:
                print("  ✓ Nessuna nuova modifica da committare su Git.")
        except Exception as e:
            print(f"  [Git Warning]: {e}")

    print("\n" + "=" * 70)
    print("  ✅ SINCRONIZZAZIONE COMPLETATA CON SUCCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-sync immagini catalogo Fatto a Mano")
    parser.add_argument("--no-git", action="store_true", help="Non eseguire git push")
    parser.add_argument("--force", action="store_true", help="Forza ricaricamento totale")
    args = parser.parse_args()

    sync_catalog(auto_git=not args.no_git, force=args.force)
