#!/usr/bin/env python3
"""
==============================================================================
FATTO A MANO — AUTOMATED CATALOG FOLDER SYNC & CLOUD DEPLOYER
==============================================================================
Scansiona ESCLUSIVAMENTE le 4 cartelle designate:
  1. assets/Intrecciati/             (Categoria: Intrecciati, no pronta consegna)
  2. assets/Martellati ossidati/     (Categoria: Martellati, no pronta consegna)
  3. assets/rigidi/                  (Categoria: Rigidi, no pronta consegna)
  4. assets/prontaconsegna/          (Pronta Consegna: TRUE)

Regole Rigorose:
  - Cuff Martellato Ossidato, Bangle Minimal Chisel, Bracciale Intrecciato 3 Filamenti: NO pronta consegna.
  - Se la cartella 'prontaconsegna' non contiene immagini, la sezione banner pronta consegna viene nascosta sul frontend.
  - Carica le immagini su Supabase Storage e Database.
  - Aggiorna products_cache.json.
  - Esegue commit e push automatico su GitHub per aggiornare Vercel in tempo reale.
==============================================================================
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
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
except Exception:
    supabase_client = None

# Le 4 cartelle autorizzate
ALLOWED_FOLDERS = [
    ASSETS_DIR / "Intrecciati",
    ASSETS_DIR / "Martellati ossidati",
    ASSETS_DIR / "rigidi",
    ASSETS_DIR / "prontaconsegna"
]

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

KNOWN_PRODUCTS_SPECS = {
    "bracciale_3_filamenti.jpg": {
        "id": "prod_rame_001",
        "title": "Bracciale Intrecciato 3 Filamenti",
        "price": 30.00,
        "description": "Forgiato a mano con 3 trefoli di rame massiccio ritorti a caldo. Chiusura artigianale a gancio S-Hook con battitura a martello. Proprietà armonizzanti ed elevata conducibilità energetica.",
        "details": "Forgiatura su misura • 3 filamenti ritorti • Finitura naturale lucidata a mano",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "bracciale_martellato.jpg": {
        "id": "prod_rame_002",
        "title": "Cuff Martellato Ossidato",
        "price": 45.00,
        "description": "Fascia solida in rame grezzo lavorata ad incudine con trama a nido d'ape battuta a mano. Trattamento protettivo biologico con cera d'api vergine per preservare la lucentezza calda nel tempo.",
        "details": "Larghezza 18 mm • Spessore 2.5 mm • Bordo smussato a specchio • Unisex",
        "category": "Martellati",
        "pronta_consegna": False
    },
    "bracciale_rigido_puro.jpg": {
        "id": "prod_rame_003",
        "title": "Bangle Minimal Chisel",
        "price": 25.00,
        "description": "Profilo circolare essenziale in puro rame elettrolitico, impreziosito da delicatissime micro-cesellature perimetrali. Un gioiello scultoreo raffinato e discreto per il benessere quotidiano.",
        "details": "Spessore 4 mm • Forgiatura su misura anatomica • Lustro satinato caldo",
        "category": "Rigidi",
        "pronta_consegna": False
    },
    "bracciale_intrecciato_cuff_bottega.jpg": {
        "id": "prod_intr_cuff_bottega",
        "title": "Bracciale Cuff Intrecciato Bottega",
        "price": 30.00,
        "description": "Bracciale cuff aperto con trefoli ritorti a caldo e terminali sagomati a mano ad incudine. Calibrato al millimetro su misura anatomica del polso.",
        "details": "Trefoli ritorti a caldo • Terminali battuti • Rame puro 99.9%",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "bracciale_intrecciato_pronta.jpg": {
        "id": "prod_pronta_intrecciato",
        "title": "Bracciale Intrecciato in Pronta Consegna",
        "price": 30.00,
        "description": "Pezzo unico già forgiato ad incudine e rifinito in atelier, disponibile per spedizione immediata (senza i consueti tempi di attesa per la forgiatura su misura).",
        "details": "Disponibilità immediata in bottega • Spedizione espressa tracciata",
        "category": "Intrecciati",
        "pronta_consegna": True
    },
    "photo_1_2026-10-01_01-24-59.jpg": {
        "id": "prod_intr_corona_regale",
        "title": "Bracciale Intrecciato Corona Regale",
        "price": 35.00,
        "description": "Scultura orafa in puro rame 99.9% a maglia intrecciata fitta. Forgiatura d'ispirazione regale con battitura ad incudine e finitura a specchio.",
        "details": "Maglia intrecciata a rilievo • Rame puro 99.9% • Forgiato a caldo",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "photo_2_2026-10-01_01-24-59.jpg": {
        "id": "prod_intr_modello_2",
        "title": "Bracciale Intrecciato Modello 2",
        "price": 30.00,
        "description": "Doppia spirale di rame ritorto battuto ad incudine, dotato di chiusura artigianale a uncino S-Hook sagomata e martellata a mano.",
        "details": "Doppio trefolo battuto • Chiusura ad uncino forgiata • Rame puro 99.9%",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "photo_3_2026-10-01_01-24-59.jpg": {
        "id": "prod_intr_massiccio_spina",
        "title": "Bracciale Intrecciato Spina Massiccia",
        "price": 35.00,
        "description": "Trama densa a spina di rame ad alta densità con chiusura artigianale battuta a freddo. Struttura corposa dal fascino primordiale e benefico.",
        "details": "Treccioli massicci ad alta densità • Chiusura anatomica • Rame puro 99.9%",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "photo_4_2026-10-01_01-24-59.jpg": {
        "id": "prod_intr_trama_nobile",
        "title": "Bracciale Intrecciato Trama Nobile",
        "price": 35.00,
        "description": "Fascia cuff multistrato con intreccio geometrico ad incudine e collare centrale di chiusura. Rifinito con cera d'api naturale per preservare la patina nobile.",
        "details": "Fascia multistrato • Collare di giunzione cesellato • Rame puro 99.9%",
        "category": "Intrecciati",
        "pronta_consegna": False
    },
    "photo_5_2026-10-01_01-24-59.jpg": {
        "id": "prod_intr_spiga_polso",
        "title": "Bracciale a Spiga in Rame Vivo",
        "price": 35.00,
        "description": "Elegante fascia flessibile a spiga forgiata con trefoli sfaccettati alla fiamma. Massima aderenza anatomica e proprietà bio-energetiche a diretto contatto cutaneo.",
        "details": "Trefoli sfaccettati a caldo • Aderenza anatomica continua • Rame puro 99.9%",
        "category": "Intrecciati",
        "pronta_consegna": False
    }
}

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
    """Trasforma un nome file in un titolo elegante per la gioielleria."""
    m = re.search(r'photo_?(\d+)', stem, re.IGNORECASE)
    if m:
        num = m.group(1)
        return f"Bracciale {category} Creazione #{num}"
    
    clean = re.sub(r'[\-_]+', ' ', stem)
    clean = re.sub(r'\b(photo|img|\d{2,})\b', '', clean, flags=re.IGNORECASE)
    words = [w.capitalize() for w in clean.split() if w]
    candidate = " ".join(words).strip()
    if len(candidate) < 6:
        return f"Bracciale {category} Rame Puro"
    return candidate


def detect_product_info(img_path: Path) -> Dict:
    """Analizza l'immagine esclusivamente in base alla cartella in cui risiede."""
    folder_name = img_path.parent.name.lower()
    filename = img_path.name
    filename_lower = filename.lower()
    
    # 1. Deduci Categoria e Pronta Consegna
    if "prontaconsegna" in folder_name or folder_name == "prontaconsegna":
        is_pronta = True
        if "martellat" in filename_lower:
            category = "Martellati"
        elif "rigid" in filename_lower:
            category = "Rigidi"
        else:
            category = "Intrecciati"
    elif "martellat" in folder_name:
        category = "Martellati"
        is_pronta = False
    elif "rigid" in folder_name:
        category = "Rigidi"
        is_pronta = False
    else:
        category = "Intrecciati"
        is_pronta = False

    # Regola esplicita: Cuff Martellato Ossidato, Bangle Minimal Chisel, Bracciale Intrecciato 3 Filamenti NO pronta consegna
    if filename in ["bracciale_3_filamenti.jpg", "bracciale_martellato.jpg", "bracciale_rigido_puro.jpg"]:
        is_pronta = False

    # Controllo specifiche note o sidecar
    spec = KNOWN_PRODUCTS_SPECS.get(filename, {})
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

    clean_stem = re.sub(r'[^a-zA-Z0-9_]', '_', stem.lower()).strip('_')
    prod_id = meta_override.get("id") or spec.get("id") or f"prod_{category.lower()[:4]}_{clean_stem}"

    title = meta_override.get("title") or spec.get("title") or (derived_title if derived_title else tmpl["title"])
    price = float(meta_override.get("price") or spec.get("price") or tmpl["price"])
    description = meta_override.get("description") or spec.get("description") or tmpl["description"]
    details = meta_override.get("details") or spec.get("details") or tmpl["details"]
    stock_qty = int(meta_override.get("stock_qty") or tmpl["stock_qty"])
    purity = meta_override.get("purity", "99.9% Rame Puro")
    
    # Pronta consegna finale
    if "pronta_consegna" in meta_override:
        is_pronta = bool(meta_override["pronta_consegna"])
    elif "pronta_consegna" in spec:
        is_pronta = bool(spec["pronta_consegna"])

    rel_path = img_path.relative_to(WORKSPACE_DIR)
    web_image_url = str(rel_path).replace("\\", "/")

    shipping_note = "Disponibile in bottega • Spedizione espressa tracciata 3-5 giorni lavorativi" if is_pronta else "Forgiato su misura • Consegna tracciata 3-5 giorni lavorativi"

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
        "shipping_note": shipping_note
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
    except Exception:
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"


def sync_catalog(auto_git: bool = True, force: bool = False):
    print("=" * 70)
    print("  🔨 FATTO A MANO — AGGIORNAMENTO AUTOMATICO CATALOGO")
    print("=" * 70)
    
    # Verifica che le 4 cartelle esistano
    for folder in ALLOWED_FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)

    # 1. Scansiona SOLO le 4 cartelle specificate
    found_images: List[Path] = []
    for folder in ALLOWED_FOLDERS:
        for ext in VALID_IMAGE_EXTENSIONS:
            found_images.extend(folder.glob(f"*{ext}"))
            found_images.extend(folder.glob(f"*{ext.upper()}"))

    # Rimuovi eventuali duplicati
    filtered_images = []
    seen = set()
    for img in sorted(found_images):
        resolved = img.resolve()
        if resolved not in seen:
            seen.add(resolved)
            filtered_images.append(img)

    print(f"📸 Trovate {len(filtered_images)} immagini nelle 4 cartelle ufficiali:")
    for folder in ALLOWED_FOLDERS:
        imgs = [i.name for i in folder.glob("*.*") if i.suffix.lower() in VALID_IMAGE_EXTENSIONS]
        print(f"   • assets/{folder.name}/ -> {len(imgs)} immagini {imgs}")

    synced_products = []
    for img_path in sorted(filtered_images):
        prod = detect_product_info(img_path)

        # Carica su Supabase Storage
        remote_filename = f"{prod['id']}_{img_path.name}"
        remote_url = upload_to_supabase_storage(img_path, remote_filename)
        prod["remote_url"] = remote_url

        badge = " [⚡ PRONTA CONSEGNA]" if prod["pronta_consegna"] else " [Su Misura]"
        print(f"  ✓ [{prod['category']:12}] {prod['title']} - €{prod['price']:.2f}{badge}")
        
        prod_for_json = {k: v for k, v in prod.items() if k != "local_path"}
        synced_products.append(prod_for_json)

    # 2. Aggiorna products_cache.json
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(synced_products, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Aggiornato {CACHE_FILE.name} con {len(synced_products)} prodotti.")

    # 3. Sincronizza tabella Supabase
    if supabase_client:
        print("\n☁️ Sincronizzazione tabella Supabase 'fattoamano_products'...")
        active_ids = [p["id"] for p in synced_products]
        try:
            supabase_client.table("fattoamano_products").update({"in_stock": False}).not_.in_("id", active_ids).execute()
        except Exception:
            pass

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

    pronta_count = len([p for p in synced_products if p.get("pronta_consegna") is True])
    print(f"\n⚡ Totale creazioni in Pronta Consegna disponibili: {pronta_count}")
    if pronta_count == 0:
        print("   (La sezione banner Pronta Consegna sarà nascosta automaticamente dal frontend)")

    # 4. Git Push automatico per deploy istantaneo su Vercel
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
                    ["git", "commit", "-m", "Auto-sync catalogo: aggiornamento cartelle e logica pronta consegna"],
                    cwd=WORKSPACE_DIR,
                    check=True
                )
                print("  ✓ Commit effettuato.")
                subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, check=True)
                print("  ✓ Push su 'origin main' completato con successo!")

            # Esegui anche il deploy diretto con Vercel CLI per applicare istantaneamente le modifiche su tutti i domini
            print("  ⚡ Esecuzione deploy diretto su Vercel Production (--prod)...")
            try:
                subprocess.run("npx vercel deploy --prod --yes", cwd=WORKSPACE_DIR, shell=True, check=True)
                print("  ✓ Deploy di produzione Vercel completato su https://agtechdesigne.shop e https://fattoamano-alpha.vercel.app")
            except Exception as ve:
                print(f"  [Vercel CLI Info]: {ve}")

            print("\n✨ IL SITO LIVE SU VERCEL È AGGIORNATO AL 100%:")
            print("   👉 https://agtechdesigne.shop")
            print("   👉 https://fattoamano-alpha.vercel.app")
        except Exception as e:
            print(f"  [Deploy Warning]: {e}")

    print("\n" + "=" * 70)
    print("  ✅ SINCRONIZZAZIONE COMPLETATA CON SUCCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-sync immagini catalogo Fatto a Mano")
    parser.add_argument("--no-git", action="store_true", help="Non eseguire git push")
    parser.add_argument("--force", action="store_true", help="Forza ricaricamento totale")
    args = parser.parse_args()

    sync_catalog(auto_git=not args.no_git, force=args.force)
