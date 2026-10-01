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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
ORDERS_AUDIT_FILE = APP_DIR / "orders_audit.json"

if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV)
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=True)

try:
    import stripe
except ImportError:
    stripe = None

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

# Import moduli Admin Dashboard
sys.path.append(str(APP_DIR / "api"))
import api.admin_auth as api_admin_auth
import api.admin_settings as api_admin_settings
import api.admin_products as api_admin_products
import api.admin_orders as api_admin_orders
from api.admin_security import verify_session_token, extract_bearer_token


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


def log_and_dispatch_order(data: dict) -> dict:
    """Registra l'ordine nel registro ordini locale e invia la notifica email ad agtechdesigne@gmail.com."""
    order_id = data.get("order_id") or f"FAM-{int(time.time() * 1000) % 1000000:06d}"
    shipping_info = data.get("shipping_info", {})
    items = data.get("items", [])
    total = float(data.get("total", 0.0))
    subtotal = float(data.get("subtotal", total - 6.0 if total > 6.0 else total))
    shipping_fee = float(data.get("shipping_fee", 6.0))

    record = {
        "order_id": order_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "customer": shipping_info,
        "items": items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "total": total,
        "status": "NOTIFIED"
    }

    orders = []
    if ORDERS_AUDIT_FILE.exists():
        try:
            with open(ORDERS_AUDIT_FILE, "r", encoding="utf-8") as f:
                orders = json.load(f)
        except Exception:
            orders = []

    orders.insert(0, record)
    with open(ORDERS_AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

    # Verifica configurazione SMTP per invio email reale
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port_val = os.getenv("SMTP_PORT", "587").strip()
    smtp_port = int(smtp_port_val) if smtp_port_val.isdigit() else 587
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    target_email = os.getenv("ORDER_NOTIFICATION_EMAIL", "agtechdesigne@gmail.com").strip()

    smtp_sent = False
    notice = f"Ordine #{order_id} protocollato con successo in orders_audit.json"

    if smtp_user and smtp_pass:
        try:
            subject = f"📦 [Nuovo Ordine Fatto a Mano] #{order_id} - €{total:.2f}"
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = target_email

            items_rows = "".join([
                f"<tr><td style='padding:8px 0;border-bottom:1px solid #282832;'>{it.get('title', 'Bracciale Rame Puro')} (x{it.get('quantity', 1)})</td>"
                f"<td style='padding:8px 0;text-align:right;border-bottom:1px solid #282832;'>€{float(it.get('price', 0))*int(it.get('quantity', 1)):.2f}</td></tr>"
                for it in items
            ])

            html_content = f"""
            <div style="background-color: #0a0a0c; color: #f5efe6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; border: 1px solid #c87d55; border-radius: 12px; max-width: 620px; margin: 0 auto;">
              <div style="background: linear-gradient(90deg, #c87d55, #e0946b); height: 4px; margin-bottom: 20px; border-radius: 2px;"></div>
              <h2 style="color: #ffffff; letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 6px 0;">FATTO A MANO — NUOVO ORDINE #{order_id}</h2>
              <div style="font-size: 12px; color: #c87d55; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 20px;">Atelier del Rame Puro 99.9%</div>
              
              <div style="background: #181820; padding: 18px; border-left: 3px solid #c87d55; border-radius: 6px; margin-bottom: 20px;">
                <div style="font-size: 13px; font-weight: bold; color: #e69870; text-transform: uppercase; margin-bottom: 10px;">🚚 Recapito & Spedizione Corriere Espresso:</div>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Destinatario:</strong> {shipping_info.get('fullName', '')}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Email Cliente:</strong> {shipping_info.get('email', '')}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Cellulare:</strong> {shipping_info.get('phone', '')}</p>
                <p style="margin: 4px 0; font-size: 14px; color: #e69870;"><strong>📏 Misura Polso Calibrata:</strong> <span style="background: rgba(200,125,85,0.25); border: 1px solid #c87d55; padding: 2px 8px; border-radius: 4px; font-weight: bold; color: #ffffff;">{shipping_info.get('wristCm', 'Calibratura Standard')}</span></p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Indirizzo:</strong> {shipping_info.get('address', '')}, {shipping_info.get('cap', '')} {shipping_info.get('city', '')} ({shipping_info.get('province', '')})</p>
                <p style="margin: 4px 0; font-size: 14px; font-style: italic; color: #aba8b6;"><strong>Note Corriere:</strong> {shipping_info.get('notes', 'Nessuna istruzione particolare')}</p>
              </div>

              <div style="font-size: 13px; font-weight: bold; color: #e69870; text-transform: uppercase; margin-bottom: 10px;">💍 Creazioni Ordinate:</div>
              <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 20px;">
                {items_rows}
                <tr>
                  <td style="padding: 10px 0; color: #aba8b6;">Spedizione Corriere Espresso (3-5gg):</td>
                  <td style="padding: 10px 0; text-align: right; color: #aba8b6;">€{shipping_fee:.2f}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 0; font-weight: bold; font-size: 16px; color: #e69870; border-top: 1px solid #c87d55;">TOTALE ORDINE:</td>
                  <td style="padding: 12px 0; text-align: right; font-weight: bold; font-size: 18px; color: #ffffff; border-top: 1px solid #c87d55;">€{total:.2f}</td>
                </tr>
              </table>

              <div style="font-size: 11px; color: #716f7c; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px;">
                Conforme al Protocollo di Tracciabilità Bottega Fatto A Mano • Notifica destinata ad {target_email}
              </div>
            </div>
            """
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as s:
                s.starttls()
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)

            smtp_sent = True
            notice = f"Notifica inviata con successo via SMTP a {target_email}"
            print(f"[Order Dispatcher] Email inviata con successo via SMTP a {target_email} per l'ordine #{order_id}")
        except Exception as e:
            notice = f"Errore invio SMTP ({e}), ordine regolarmente salvato in orders_audit.json"
            print(f"[Order Dispatcher SMTP Error]: {e}")
    else:
        print(f"[Order Dispatcher] Ordine #{order_id} registrato in orders_audit.json (destinatario notifica: {target_email})")

    # Tentativo invio automatico tramite EmailJS REST API
    emailjs_service = os.getenv("EMAILJS_SERVICE_ID", "service_1m1tfyq").strip()
    emailjs_template = os.getenv("EMAILJS_TEMPLATE_ID", "template_i4boqs9").strip()
    emailjs_public = os.getenv("EMAILJS_PUBLIC_KEY", "Ts44-OGlmsSUV73rR").strip()
    emailjs_private = os.getenv("EMAILJS_PRIVATE_KEY", "").strip()
    emailjs_sent = False

    if emailjs_service and emailjs_template and emailjs_public:
        try:
            payload_js = {
                "service_id": emailjs_service,
                "template_id": emailjs_template,
                "user_id": emailjs_public,
                "template_params": {
                    "to_email": target_email,
                    "email": shipping_info.get("email", target_email),
                    "order_id": order_id,
                    "data_ordine": time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()),
                    "destinatario_nome": shipping_info.get("fullName", ""),
                    "destinatario_email": shipping_info.get("email", ""),
                    "destinatario_telefono": shipping_info.get("phone", ""),
                    "indirizzo": shipping_info.get("address", ""),
                    "cap": shipping_info.get("cap", ""),
                    "citta": shipping_info.get("city", ""),
                    "provincia": shipping_info.get("province", ""),
                    "note_consegna": shipping_info.get("notes", "Nessuna istruzione particolare"),
                    "subtotal": f"{subtotal:.2f}",
                    "spese_spedizione": f"{shipping_fee:.2f}",
                    "totale_ordine": f"{total:.2f}"
                }
            }
            if emailjs_private:
                payload_js["accessToken"] = emailjs_private

            req = urllib.request.Request(
                "https://api.emailjs.com/api/v1.0/email/send",
                data=json.dumps(payload_js).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status in (200, 201):
                    emailjs_sent = True
                    notice += " • Inviata via EmailJS"
                    print(f"[EmailJS Server Dispatch] Notifica inviata con successo via EmailJS ad {target_email}")
        except urllib.error.HTTPError as he:
            err_txt = he.read().decode("utf-8", errors="ignore")
            print(f"[EmailJS Server Dispatch Notice]: HTTP {he.code} ({err_txt.strip()})")
        except Exception as ee:
            print(f"[EmailJS Server Exception]: {ee}")

    return {
        "success": True,
        "order_id": order_id,
        "smtp_sent": smtp_sent,
        "emailjs_sent": emailjs_sent,
        "target_email": target_email,
        "message": notice
    }


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

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # Route /admin pulita verso admin.html
        if parsed.path in ("/admin", "/admin/"):
            self.path = "/admin.html"
            return super().do_GET()

        # Admin API endpoints
        if parsed.path == "/api/admin_auth":
            api_admin_auth.handler.do_GET(self)
            return

        if parsed.path == "/api/admin_settings":
            api_admin_settings.handler.do_GET(self)
            return

        if parsed.path == "/api/admin_products":
            api_admin_products.handler.do_GET(self)
            return

        if parsed.path == "/api/admin_orders":
            api_admin_orders.handler.do_GET(self)
            return

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

        # Admin API POST
        if parsed.path == "/api/admin_auth":
            api_admin_auth.handler.do_POST(self)
            return

        if parsed.path == "/api/admin_settings":
            api_admin_settings.handler.do_POST(self)
            return

        if parsed.path == "/api/admin_products":
            api_admin_products.handler.do_POST(self)
            return

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

        # Endpoint: Notifica Nuovo Ordine & Invio Email ad agtechdesigne@gmail.com
        if parsed.path == "/api/send-order-notification":
            result = log_and_dispatch_order(data)
            self.send_json(200, result)
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

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/admin_settings":
            api_admin_settings.handler.do_PUT(self)
            return

        if parsed.path == "/api/admin_products":
            api_admin_products.handler.do_PUT(self)
            return

        if parsed.path == "/api/admin_orders":
            api_admin_orders.handler.do_PUT(self)
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/admin_products":
            api_admin_products.handler.do_DELETE(self)
            return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()


def run_server(port=None):
    if port is None:
        port_env = os.getenv("PORT", "8092")
        port = int(port_env) if str(port_env).isdigit() else 8092

    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, FattoAManoHandler)
    stripe_key = get_stripe_key()
    print(f"\n=======================================================")
    print(f"  FATTO A MANO — CREAZIONI RAME PURO FATTO A MANO")
    print(f"  URL Locale:     http://localhost:{port}")
    print(f"  Dashboard Admin: http://localhost:{port}/admin")
    print(f"  API Health:     http://localhost:{port}/api/health")
    print(f"  API Products:   http://localhost:{port}/api/products")
    print(f"  API Privacy:    http://localhost:{port}/api/privacy-request")
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
