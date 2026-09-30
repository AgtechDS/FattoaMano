from http.server import BaseHTTPRequestHandler
import json
import os
import time
import base64
import urllib.request
import urllib.parse
import re
import sys
from pathlib import Path

# Assicura import del modulo di sicurezza
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from admin_security import verify_session_token, extract_bearer_token
except ImportError:
    from api.admin_security import verify_session_token, extract_bearer_token

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "products_cache.json"


def get_all_products():
    """Recupera tutti i prodotti (inclusi quelli non attivi o bozze) da Supabase o cache locale."""
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if sb_url and sb_key:
        try:
            req = urllib.request.Request(
                f"{sb_url}/rest/v1/fattoamano_products?select=*&order=created_at.desc",
                headers={
                    "apikey": sb_key,
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    if isinstance(data, list):
                        return data
        except Exception:
            pass

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return []


def save_local_cache(products: list):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Cache save warning]: {e}")


def upload_base64_image(base64_data: str, filename: str, category: str, is_pronta: bool) -> str:
    """Decodifica un'immagine base64, la salva localmente e la carica su Supabase Storage."""
    # Rimuovi prefisso data:image/...;base64, se presente
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]

    img_bytes = base64.b64decode(base64_data)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    if not clean_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        clean_name += ".jpg"

    timestamp_prefix = int(time.time())
    storage_filename = f"{timestamp_prefix}_{clean_name}"

    # 1. Salva localmente nella cartella appropriata
    folder_name = "prontaconsegna" if is_pronta else ("Martellati ossidati" if "martellat" in category.lower() else ("rigidi" if "rigid" in category.lower() else "Intrecciati"))
    target_folder = BASE_DIR / "assets" / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)
    local_path = target_folder / clean_name
    try:
        with open(local_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        print(f"[Local image write warning]: {e}")

    # Percorso relativo per il web
    web_relative_path = f"assets/{folder_name}/{clean_name}"

    # 2. Carica su Supabase Storage bucket 'fattoamano-products'
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if sb_url and sb_key:
        try:
            upload_url = f"{sb_url}/storage/v1/object/fattoamano-products/{storage_filename}"
            req = urllib.request.Request(
                upload_url,
                data=img_bytes,
                headers={
                    "apikey": sb_key,
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "image/jpeg",
                    "x-upsert": "true"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status in (200, 201):
                    return f"{sb_url}/storage/v1/object/public/fattoamano-products/{storage_filename}"
        except Exception as e:
            print(f"[Supabase Storage Upload Warning]: {e}")

    return web_relative_path


class handler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def check_auth(self) -> bool:
        token = extract_bearer_token(self.headers)
        is_valid, _, _ = verify_session_token(token)
        return is_valid

    def do_GET(self):
        """Elenco completo di tutti i prodotti per la dashboard admin."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        products = get_all_products()
        self.send_json(200, {"success": True, "products": products})

    def do_POST(self):
        """Aggiunta nuovo gioiello/prodotto con upload opzionale della foto."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            item = json.loads(body_raw)
        except Exception:
            self.send_json(400, {"error": "Payload JSON non valido"})
            return

        title = str(item.get("title", "")).strip()
        price = float(item.get("price", 30.0))
        if not title:
            self.send_json(400, {"error": "Il titolo dell'opera è obbligatorio"})
            return

        category = item.get("category", "Intrecciati")
        is_pronta = bool(item.get("pronta_consegna", False))
        
        # Gestione Immagine
        img_url = item.get("image_url", "").strip()
        if "image_base64" in item and item["image_base64"]:
            filename = item.get("image_filename") or f"{title.lower().replace(' ', '_')}.jpg"
            img_url = upload_base64_image(item["image_base64"], filename, category, is_pronta)

        prod_id = item.get("id") or f"prod_fam_{int(time.time() * 1000) % 10000000:07d}"
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        new_product = {
            "id": prod_id,
            "title": title,
            "price": price,
            "currency": "EUR",
            "image_url": img_url or "assets/Intrecciati/bracciale_3_filamenti.jpg",
            "purity": item.get("purity", "99.9% Rame Puro"),
            "category": category,
            "description": item.get("description", "Forgiato a mano in puro rame 99.9% ad incudine."),
            "details": item.get("details", "Fatto a mano • Rame puro 99.9% • Lucidatura biologica"),
            "in_stock": bool(item.get("in_stock", True)),
            "pronta_consegna": is_pronta,
            "stock_qty": int(item.get("stock_qty", 1)),
            "shipping_note": item.get("shipping_note", "Disponibile subito" if is_pronta else "Forgiato su misura • Consegna 3-5 gg"),
            "created_at": now_iso
        }

        # Inserisci in Supabase DB
        sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if sb_url and sb_key:
            try:
                req = urllib.request.Request(
                    f"{sb_url}/rest/v1/fattoamano_products",
                    data=json.dumps(new_product).encode("utf-8"),
                    headers={
                        "apikey": sb_key,
                        "Authorization": f"Bearer {sb_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    pass
            except Exception as e:
                print(f"[Supabase Insert Warning]: {e}")

        # Aggiorna cache locale
        current_list = get_all_products()
        current_list.insert(0, new_product)
        save_local_cache(current_list)

        self.send_json(201, {
            "success": True,
            "message": "Opera aggiunta al catalogo con successo",
            "product": new_product
        })

    def do_PUT(self):
        """Modifica di un prodotto esistente."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            item = json.loads(body_raw)
        except Exception:
            self.send_json(400, {"error": "Payload JSON non valido"})
            return

        prod_id = item.get("id")
        if not prod_id:
            self.send_json(400, {"error": "ID prodotto mancante"})
            return

        # Se c'è una nuova immagine caricata
        if "image_base64" in item and item["image_base64"]:
            category = item.get("category", "Intrecciati")
            is_pronta = bool(item.get("pronta_consegna", False))
            filename = item.get("image_filename") or f"{prod_id}.jpg"
            item["image_url"] = upload_base64_image(item["image_base64"], filename, category, is_pronta)
            del item["image_base64"]
            if "image_filename" in item:
                del item["image_filename"]

        # Aggiorna Supabase DB
        sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if sb_url and sb_key:
            try:
                req = urllib.request.Request(
                    f"{sb_url}/rest/v1/fattoamano_products?id=eq.{urllib.parse.quote(str(prod_id))}",
                    data=json.dumps(item).encode("utf-8"),
                    headers={
                        "apikey": sb_key,
                        "Authorization": f"Bearer {sb_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    method="PATCH"
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    pass
            except Exception as e:
                print(f"[Supabase Update Warning]: {e}")

        # Aggiorna cache locale
        current_list = get_all_products()
        updated = False
        for i, p in enumerate(current_list):
            if p.get("id") == prod_id:
                current_list[i].update(item)
                updated = True
                break
        if not updated:
            current_list.append(item)
        save_local_cache(current_list)

        self.send_json(200, {
            "success": True,
            "message": "Opera modificata con successo",
            "product": item
        })

    def do_DELETE(self):
        """Eliminazione di un prodotto dal catalogo."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        prod_id = qs.get("id", [None])[0]

        if not prod_id:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                try:
                    data = json.loads(self.rfile.read(content_length).decode("utf-8"))
                    prod_id = data.get("id")
                except Exception:
                    pass

        if not prod_id:
            self.send_json(400, {"error": "ID prodotto da eliminare non specificato"})
            return

        # Elimina da Supabase DB
        sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if sb_url and sb_key:
            try:
                req = urllib.request.Request(
                    f"{sb_url}/rest/v1/fattoamano_products?id=eq.{urllib.parse.quote(str(prod_id))}",
                    headers={
                        "apikey": sb_key,
                        "Authorization": f"Bearer {sb_key}",
                        "Content-Type": "application/json"
                    },
                    method="DELETE"
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    pass
            except Exception as e:
                print(f"[Supabase Delete Warning]: {e}")

        # Rimuovi dalla cache locale
        current_list = get_all_products()
        current_list = [p for p in current_list if p.get("id") != prod_id]
        save_local_cache(current_list)

        self.send_json(200, {
            "success": True,
            "message": f"Opera {prod_id} rimossa dal catalogo"
        })
