"""
==============================================================================
FATTO A MANO — LUXURY E-COMMERCE SERVER & STRIPE GATEWAY
==============================================================================
Microservizio Python ad alte prestazioni per:
  1. Servire l'applicazione web Dark Luxury
  2. Fornire l'API /api/products (Supabase cloud + local JSON cache)
  3. Gestire /api/create-checkout-session (Stripe Checkout ufficiale live)
  4. Gestire /api/privacy-request (Conformità GDPR Art. 12-22 & EU AI Act)
==============================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from dotenv import load_dotenv

# Directory di riferimento
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(__file__).resolve().parents[2] if "Workspace" in str(APP_DIR) else APP_DIR
LOCAL_ENV = APP_DIR / ".env"
ROOT_ENV = ROOT_DIR / ".env"
CACHE_FILE = APP_DIR / "products_cache.json"
PRIVACY_FILE = APP_DIR / "privacy_requests.json"

try:
    import stripe
except ImportError:
    stripe = None

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None


def get_stripe_key() -> str:
    """Recupera la chiave segreta Stripe ricaricando .env se necessario."""
    if LOCAL_ENV.exists():
        load_dotenv(LOCAL_ENV, override=True)
    elif ROOT_ENV.exists():
        load_dotenv(ROOT_ENV, override=True)

    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    return key


def get_supabase_client():
    """Inizializza o restituisce il client Supabase con le credenziali attuali."""
    if not create_client:
        return None
    url = os.getenv("SUPABASE_URL", "https://mkeykuouwsbjezdgwskq.supabase.co").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")).strip()
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            pass
    return None


def get_products():
    """Recupera prodotti da Supabase, con fallback immediato su products_cache.json."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("fattoamano_products").select("*").eq("in_stock", True).order("created_at", desc=True).execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception as e:
            print(f"[Supabase Query Warning, uso cache locale]: {e}")

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return []


def log_privacy_request(data: dict) -> str:
    """Registra una richiesta GDPR e assegna un protocollo ufficiale."""
    protocol = f"GDPR-REQ-{int(time.time())}"
    record = {
        "protocol": protocol,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "fullName": data.get("fullName", "").strip(),
        "email": data.get("email", "").strip(),
        "requestType": data.get("requestType", "access"),
        "notes": data.get("notes", "").strip(),
        "status": "ACQUIRED"
    }

    requests = []
    if PRIVACY_FILE.exists():
        try:
            with open(PRIVACY_FILE, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except Exception:
            requests = []

    requests.insert(0, record)
    with open(PRIVACY_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)

    return protocol


class FattoAManoHandler(SimpleHTTPRequestHandler):
    """Handler personalizzato per servire static files e endpoint API."""

    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def send_json(self, status_code: int, data_dict: dict):
        """Invia payload JSON con Content-Length per completare la risposta HTTP istantaneamente."""
        payload = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/products":
            products = get_products()
            self.send_json(200, products)
            return

        if parsed.path == "/api/health":
            stripe_key = get_stripe_key()
            status = {
                "status": "healthy",
                "stripe_configured": bool(stripe and stripe_key and not stripe_key.startswith("sk_test_placeholder")),
                "stripe_key_preview": f"{stripe_key[:8]}...{stripe_key[-4:]}" if stripe_key else None,
                "supabase_configured": bool(get_supabase_client() is not None),
                "products_count": len(get_products()),
                "compliance": ["GDPR_UE_2016_679", "EU_AI_ACT_2024_1689"]
            }
            self.send_json(200, status)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            data = json.loads(body_raw)
        except Exception:
            data = {}

        # Endpoint 1: Richiesta GDPR & Diritti Privacy
        if parsed.path == "/api/privacy-request":
            protocol = log_privacy_request(data)
            response_payload = {
                "success": True,
                "protocol": protocol,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "message": "Richiesta acquisita e protocollata a norma del Regolamento UE 2016/679"
            }
            self.send_json(200, response_payload)
            return

        # Endpoint 2: Stripe Checkout Session
        if parsed.path == "/api/create-checkout-session":
            stripe_key = get_stripe_key()
            items = data.get("items", [])
            host_header = self.headers.get("Host", "localhost:8092")
            origin = f"http://{host_header}"

            success_url = data.get("success_url") or f"{origin}/success.html"
            cancel_url = data.get("cancel_url") or f"{origin}/"

            if stripe and stripe_key and not stripe_key.startswith("sk_test_placeholder"):
                stripe.api_key = stripe_key
                try:
                    shipping_info = data.get("shipping_info", {})
                    customer_email = shipping_info.get("email", "").strip() or None

                    shipping_metadata = {
                        "cliente_nome": str(shipping_info.get("fullName", ""))[:100],
                        "telefono": str(shipping_info.get("phone", ""))[:50],
                        "indirizzo": str(shipping_info.get("address", ""))[:150],
                        "cap": str(shipping_info.get("cap", ""))[:10],
                        "citta": str(shipping_info.get("city", ""))[:60],
                        "provincia": str(shipping_info.get("province", ""))[:10],
                        "note_consegna": str(shipping_info.get("notes", ""))[:200]
                    }

                    line_items = []
                    for it in items:
                        price_val = float(it.get("price", 30))
                        price_cents = int(price_val * 100)
                        title = it.get("title", "Bracciale in Puro Rame 99.9%")
                        
                        img_url = it.get("image_url", "")
                        images = [img_url] if img_url.startswith("http") else []

                        line_items.append({
                            "price_data": {
                                "currency": "eur",
                                "product_data": {
                                    "name": title,
                                    "description": "Bracciale artigianale in puro rame 99.9% forgiato a mano Fatto a Mano",
                                    "images": images,
                                },
                                "unit_amount": price_cents,
                            },
                            "quantity": int(it.get("quantity", 1)),
                        })

                    session_params = {
                        "payment_method_types": ["card"],
                        "line_items": line_items,
                        "mode": "payment",
                        "shipping_options": [
                            {
                                "shipping_rate_data": {
                                    "type": "fixed_amount",
                                    "fixed_amount": {"amount": 600, "currency": "eur"},
                                    "display_name": "Spedizione Corriere Espresso (Tutta Italia)",
                                    "delivery_estimate": {
                                        "minimum": {"unit": "business_day", "value": 3},
                                        "maximum": {"unit": "business_day", "value": 5},
                                    },
                                },
                            }
                        ],
                        "shipping_address_collection": {"allowed_countries": ["IT"]},
                        "metadata": {k: v for k, v in shipping_metadata.items() if v},
                        "success_url": success_url,
                        "cancel_url": cancel_url,
                    }

                    if customer_email:
                        session_params["customer_email"] = customer_email

                    session = stripe.checkout.Session.create(**session_params)

                    print(f"[Stripe Live Checkout] Creata sessione {session.id} per {len(items)} articoli -> {session.url}")
                    self.send_json(200, {"url": session.url})
                    return
                except Exception as e:
                    print(f"[Stripe Checkout Error]: {e}")
                    self.send_json(500, {"error": str(e), "url": None})
                    return

            # Risposta se la chiave non è presente
            self.send_json(200, {
                "notice": "Chiave STRIPE_SECRET_KEY non rilevata in Workspace/FattoAMano/.env",
                "url": None
            })
            return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port=None):
    if port is None:
        port_env = os.getenv("PORT", "8092")
        port = int(port_env) if str(port_env).isdigit() else 8092

    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, FattoAManoHandler)
    stripe_key = get_stripe_key()
    print(f"\n=======================================================")
    print(f"  FATTO A MANO — BOUTIQUE RAME PURO ATTIVA")
    print(f"  URL Locale: http://localhost:{port}")
    print(f"  API Health: http://localhost:{port}/api/health")
    print(f"  API Products: http://localhost:{port}/api/products")
    print(f"  API Privacy:  http://localhost:{port}/api/privacy-request")
    print(f"  Stripe Live:  {'ATTIVO (' + stripe_key[:8] + '...)' if stripe_key else 'NON CONFIGURATO'}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto server completato.")
        httpd.server_close()


if __name__ == "__main__":
    port = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
