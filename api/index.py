"""
Fatto a Mano — Luxury Copper E-Commerce
Vercel Serverless Unified Gateway & Static Server
"""

from http.server import SimpleHTTPRequestHandler
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Directory dei file statici su Vercel (/var/task)
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    import stripe
except ImportError:
    stripe = None

import sys
sys.path.append(str(Path(__file__).resolve().parent))
try:
    import api.admin_auth as api_admin_auth
    import api.admin_settings as api_admin_settings
    import api.admin_products as api_admin_products
    import api.admin_orders as api_admin_orders
except ImportError:
    try:
        import admin_auth as api_admin_auth
        import admin_settings as api_admin_settings
        import admin_products as api_admin_products
        import admin_orders as api_admin_orders
    except ImportError:
        api_admin_auth = None
        api_admin_settings = None
        api_admin_products = None
        api_admin_orders = None

try:
    from admin_security import verify_session_token, extract_bearer_token
except ImportError:
    try:
        from api.admin_security import verify_session_token, extract_bearer_token
    except ImportError:
        verify_session_token = lambda t: (False, None, "Security module not loaded")
        extract_bearer_token = lambda h: None

FALLBACK_PRODUCTS = [
    {
        "id": "prod_rame_001",
        "title": "Bracciale Intrecciato 3 Filamenti",
        "price": 30.0,
        "description": "Forgiato a mano con 3 trefoli di rame massiccio ritorti a caldo. Chiusura fatta a mano a gancio S-Hook con battitura a martello. Proprietà armonizzanti ed elevata conducibilità energetica.",
        "category": "Intrecciati",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/bracciale_3_filamenti.jpg"
    },
    {
        "id": "prod_rame_002",
        "title": "Cuff Martellato Ossidato",
        "price": 45.0,
        "description": "Fascia solida in rame grezzo lavorata ad incudine con trama a nido d'ape battuta a mano. Trattamento protettivo biologico con cera d'api vergine per preservare la lucentezza calda nel tempo.",
        "category": "Martellati",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/bracciale_martellato.jpg"
    },
    {
        "id": "prod_rame_003",
        "title": "Bangle Minimal Chisel",
        "price": 25.0,
        "description": "Profilo circolare essenziale in puro rame elettrolitico, impreziosito da delicatissime micro-cesellature perimetrali. Un gioiello scultoreo raffinato e discreto per il benessere quotidiano.",
        "category": "Rigidi",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/bracciale_rigido_puro.jpg"
    }
]


def fetch_products():
    # 1. Supabase PostgREST
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if sb_url and sb_key:
        try:
            endpoint = f"{sb_url}/rest/v1/fattoamano_products?select=*&in_stock=eq.true&order=created_at.desc"
            req = urllib.request.Request(endpoint, headers={
                "apikey": sb_key,
                "Authorization": f"Bearer {sb_key}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    if isinstance(data, list) and len(data) > 0:
                        return data
        except Exception:
            pass

    # 2. Cache su disco
    cache_paths = [
        BASE_DIR / "products_cache.json",
        Path("products_cache.json")
    ]
    for p in cache_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception:
                pass

    return FALLBACK_PRODUCTS


class handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def send_json(self, status_code, data_dict):
        payload = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def get_client_ip(self) -> str:
        forwarded = self.headers.get("x-forwarded-for") or self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0] if hasattr(self, "client_address") and self.client_address else "127.0.0.1"

    def check_auth(self) -> bool:
        token = extract_bearer_token(self.headers)
        is_valid, _, _ = verify_session_token(token)
        return is_valid

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        # 1. Routing Static Admin Assets
        if path in ("/admin", "/admin/", "/admin.html"):
            for candidate in [BASE_DIR / "admin.html", Path("admin.html")]:
                if candidate.exists():
                    raw = candidate.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return

        if path.startswith("/admin.js"):
            for candidate in [BASE_DIR / "admin.js", Path("admin.js")]:
                if candidate.exists():
                    raw = candidate.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/javascript; charset=utf-8")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return

        if path.startswith("/admin.css"):
            for candidate in [BASE_DIR / "admin.css", Path("admin.css")]:
                if candidate.exists():
                    raw = candidate.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/css; charset=utf-8")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return

        # 2. Admin APIs GET
        if path == "/api/admin_auth" or path.endswith("/admin_auth"):
            if api_admin_auth:
                return api_admin_auth.handler.do_GET(self)
        if path == "/api/admin_settings" or path.endswith("/admin_settings"):
            if api_admin_settings:
                return api_admin_settings.handler.do_GET(self)
        if path == "/api/admin_products" or path.endswith("/admin_products"):
            if api_admin_products:
                return api_admin_products.handler.do_GET(self)
        if path == "/api/admin_orders" or path.endswith("/admin_orders"):
            if api_admin_orders:
                return api_admin_orders.handler.do_GET(self)

        # 3. Public API Products
        if path == "/api/products" or path.endswith("/products"):
            products = fetch_products()
            self.send_json(200, products)
            return

        # 4. API Health
        if path == "/api/health" or path.endswith("/health"):
            self.send_json(200, {
                "status": "healthy",
                "service": "fatto-a-mano-cloud",
                "admin_configured": bool(os.environ.get("ADMIN_ACCESS_CODE")),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "runtime": "Vercel Serverless Python"
            })
            return

        # Static files fallback
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Admin APIs POST
        if path == "/api/admin_auth" or path.endswith("/admin_auth"):
            if api_admin_auth:
                return api_admin_auth.handler.do_POST(self)
        if path == "/api/admin_settings" or path.endswith("/admin_settings"):
            if api_admin_settings:
                return api_admin_settings.handler.do_POST(self)
        if path == "/api/admin_products" or path.endswith("/admin_products"):
            if api_admin_products:
                return api_admin_products.handler.do_POST(self)

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            data = json.loads(body_raw)
        except Exception:
            data = {}

        # API Privacy Request (GDPR / EU AI Act)
        if path == "/api/privacy-request" or path.endswith("/privacy-request"):
            protocol = f"GDPR-REQ-{int(time.time())}"
            self.send_json(200, {
                "success": True,
                "protocol": protocol,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "message": "Richiesta acquisita e protocollata a norma del Regolamento UE 2016/679"
            })
            return

        # API Stripe Checkout Session
        if path == "/api/create-checkout-session" or path.endswith("/create-checkout-session"):
            stripe_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            items = data.get("items", [])

            host_header = self.headers.get("Host", "fattoamano.vercel.app")
            origin = self.headers.get("Origin") or f"https://{host_header}"

            success_url = data.get("success_url") or f"{origin}/success.html"
            cancel_url = data.get("cancel_url") or f"{origin}/"

            if not stripe_key:
                self.send_json(400, {
                    "error": "STRIPE_SECRET_KEY non configurata.",
                    "url": cancel_url
                })
                return

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

            # Tentativo 1: Stripe SDK
            if stripe:
                stripe.api_key = stripe_key
                try:
                    line_items = []
                    for it in items:
                        price_val = float(it.get("price", 30))
                        price_cents = int(price_val * 100)
                        title = it.get("title", "Bracciale in Puro Rame 99.9%")
                        img_url = it.get("image_url", "")
                        images = [img_url] if (img_url.startswith("http://") or img_url.startswith("https://")) else []

                        line_items.append({
                            "price_data": {
                                "currency": "eur",
                                "product_data": {
                                    "name": title,
                                    "description": "Bracciale fatto a mano in puro rame 99.9% Fatto a Mano",
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

                    self.send_json(200, {
                        "id": session.id,
                        "url": session.url
                    })
                    return
                except Exception:
                    pass

            # Tentativo 2: Stripe REST nativo (zero dipendenze)
            try:
                form_payload = [
                    ("payment_method_types[]", "card"),
                    ("mode", "payment"),
                    ("shipping_options[0][shipping_rate_data][type]", "fixed_amount"),
                    ("shipping_options[0][shipping_rate_data][fixed_amount][amount]", "600"),
                    ("shipping_options[0][shipping_rate_data][fixed_amount][currency]", "eur"),
                    ("shipping_options[0][shipping_rate_data][display_name]", "Spedizione Corriere Espresso (Tutta Italia)"),
                    ("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]", "business_day"),
                    ("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]", "3"),
                    ("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]", "business_day"),
                    ("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]", "5"),
                    ("shipping_address_collection[allowed_countries][0]", "IT"),
                    ("success_url", success_url),
                    ("cancel_url", cancel_url),
                ]

                if customer_email:
                    form_payload.append(("customer_email", customer_email))

                for mk, mv in shipping_metadata.items():
                    if mv:
                        form_payload.append((f"metadata[{mk}]", mv))
                for idx, it in enumerate(items):
                    price_val = float(it.get("price", 30))
                    price_cents = int(price_val * 100)
                    title = it.get("title", "Bracciale in Puro Rame 99.9%")
                    img_url = it.get("image_url", "")

                    form_payload.append((f"line_items[{idx}][quantity]", str(int(it.get("quantity", 1)))))
                    form_payload.append((f"line_items[{idx}][price_data][currency]", "eur"))
                    form_payload.append((f"line_items[{idx}][price_data][unit_amount]", str(price_cents)))
                    form_payload.append((f"line_items[{idx}][price_data][product_data][name]", title))
                    form_payload.append((f"line_items[{idx}][price_data][product_data][description]", "Bracciale fatto a mano in puro rame 99.9%"))
                    if img_url.startswith("http://") or img_url.startswith("https://"):
                        form_payload.append((f"line_items[{idx}][price_data][product_data][images][0]", img_url))

                encoded_data = urllib.parse.urlencode(form_payload).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.stripe.com/v1/checkout/sessions",
                    data=encoded_data,
                    headers={
                        "Authorization": f"Bearer {stripe_key}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as res:
                    res_body = json.loads(res.read().decode("utf-8"))
                    self.send_json(200, {
                        "id": res_body.get("id"),
                        "url": res_body.get("url")
                    })
                    return
            except urllib.error.HTTPError as he:
                err_text = he.read().decode("utf-8")
                self.send_json(he.code, {"error": f"Errore Stripe: {err_text}"})
            except Exception as e:
                self.send_json(500, {"error": f"Impossibile creare sessione Stripe: {str(e)}"})
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/admin_settings" or path.endswith("/admin_settings"):
            if api_admin_settings:
                return api_admin_settings.handler.do_PUT(self)
        if path == "/api/admin_products" or path.endswith("/admin_products"):
            if api_admin_products:
                return api_admin_products.handler.do_PUT(self)
        if path == "/api/admin_orders" or path.endswith("/admin_orders"):
            if api_admin_orders:
                return api_admin_orders.handler.do_PUT(self)
        self.send_json(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/admin_products" or path.endswith("/admin_products"):
            if api_admin_products:
                return api_admin_products.handler.do_DELETE(self)
        self.send_json(404, {"error": "Endpoint not found"})

