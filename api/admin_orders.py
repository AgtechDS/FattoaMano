from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Carica .env
BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_ENV = BASE_DIR / ".env"
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=True)

# Assicura import del modulo di sicurezza
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from admin_security import (
        verify_session_token,
        extract_bearer_token,
        codx_hemdal_encrypt,
        codx_hemdal_decrypt,
        mask_pii
    )
except ImportError:
    from api.admin_security import (
        verify_session_token,
        extract_bearer_token,
        codx_hemdal_encrypt,
        codx_hemdal_decrypt,
        mask_pii
    )

try:
    import stripe
except ImportError:
    stripe = None

ORDERS_FILE = BASE_DIR / "orders_audit.json"


def get_orders() -> list:
    if ORDERS_FILE.exists():
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_orders(orders: list):
    try:
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Orders file write warning]: {e}")


def fetch_stripe_live_report() -> dict:
    """Interroga Stripe live per estrarre il report ufficiale reale."""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not stripe_key:
        return {
            "error": "STRIPE_SECRET_KEY non configurata",
            "available_eur": 0.0,
            "pending_eur": 0.0,
            "livemode": False,
            "charges": []
        }

    if not stripe:
        return {
            "error": "Modulo Python 'stripe' non installato",
            "available_eur": 0.0,
            "pending_eur": 0.0,
            "livemode": False,
            "charges": []
        }

    stripe.api_key = stripe_key
    report = {
        "livemode": True,
        "available_eur": 0.0,
        "pending_eur": 0.0,
        "total_succeeded_eur": 0.0,
        "total_charges_count": 0,
        "succeeded_count": 0,
        "failed_count": 0,
        "recent_charges": [],
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "security_compliance": "PCI-DSS-v4.0 / EU-GDPR Tokenized"
    }

    # 1. Saldo Stripe reale
    try:
        bal = stripe.Balance.retrieve()
        report["livemode"] = bal.get("livemode", True)
        for av in bal.get("available", []):
            if av.get("currency") == "eur":
                report["available_eur"] += av.get("amount", 0) / 100.0
        for pe in bal.get("pending", []):
            if pe.get("currency") == "eur":
                report["pending_eur"] += pe.get("amount", 0) / 100.0
    except Exception as e:
        report["balance_error"] = str(e)

    # 2. Ultime transazioni
    try:
        charges = stripe.Charge.list(limit=25)
        charge_items = []
        tot_succeeded = 0.0
        succeeded_cnt = 0
        failed_cnt = 0

        for ch in charges.data:
            amt_eur = ch.amount / 100.0 if ch.amount else 0.0
            is_succeeded = (ch.status == "succeeded")
            if is_succeeded:
                tot_succeeded += amt_eur
                succeeded_cnt += 1
            else:
                failed_cnt += 1

            receipt_mail = ch.receipt_email or (ch.billing_details.email if ch.billing_details else "")
            charge_items.append({
                "id": ch.id,
                "amount_eur": amt_eur,
                "currency": ch.currency.upper(),
                "status": ch.status,
                "paid": ch.paid,
                "customer_email_masked": mask_pii(receipt_mail) if receipt_mail else "N/D",
                "payment_method": ch.payment_method_details.type if ch.payment_method_details else "card",
                "created": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ch.created)) if ch.created else "N/D"
            })

        report["recent_charges"] = charge_items
        report["total_charges_count"] = len(charges.data)
        report["succeeded_count"] = succeeded_cnt
        report["failed_count"] = failed_cnt
        report["total_succeeded_eur"] = round(tot_succeeded, 2)
    except Exception as e:
        report["charges_error"] = str(e)

    return report


class handler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def check_auth(self) -> bool:
        token = extract_bearer_token(self.headers)
        is_valid, _, _ = verify_session_token(token)
        return is_valid

    def do_GET(self):
        """Elenco di tutti gli ordini registrati o report Stripe live."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        # Se richiesta report Stripe
        if qs.get("action", [""])[0] == "stripe_report":
            report_data = fetch_stripe_live_report()
            self.send_json(200, {
                "success": True,
                "report": report_data
            })
            return

        # Elenco ordini con decifratura trasparente codX+ Hemdal per admin autenticato
        raw_orders = get_orders()
        decrypted_orders = []
        tamper_alerts = []

        for ord_item in raw_orders:
            item_copy = dict(ord_item)
            if item_copy.get("hemdal_vault"):
                ok, vault_data, err = codx_hemdal_decrypt(item_copy["hemdal_vault"])
                if ok:
                    item_copy["customer"] = vault_data.get("customer", {})
                    if "items" in vault_data and not item_copy.get("items"):
                        item_copy["items"] = vault_data.get("items")
                    item_copy["hemdal_verified"] = True
                    item_copy["cipher_suite"] = item_copy["hemdal_vault"].get("cipher_suite")
                else:
                    item_copy["hemdal_verified"] = False
                    item_copy["hemdal_tamper_warning"] = err
                    tamper_alerts.append(f"Ordine {item_copy.get('order_id')}: {err}")
            decrypted_orders.append(item_copy)

        self.send_json(200, {
            "success": True,
            "count": len(decrypted_orders),
            "orders": decrypted_orders,
            "security": {
                "cipher_engine": "AgTechDesigne codX+ Hemdal",
                "encryption": "AES-256-GCM + HMAC-SHA512",
                "tamper_alerts": tamper_alerts,
                "all_integrity_passed": len(tamper_alerts) == 0
            }
        })

    def do_PUT(self):
        """Aggiornamento stato ordine (es. Spedito, In Lavorazione, Codice Tracking)."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body_raw)
        except Exception:
            self.send_json(400, {"error": "Payload JSON non valido"})
            return

        order_id = data.get("order_id")
        new_status = data.get("status")
        tracking_number = data.get("tracking_number")

        orders = get_orders()
        updated = False
        for ord_item in orders:
            if ord_item.get("order_id") == order_id:
                if new_status:
                    ord_item["status"] = new_status
                if tracking_number is not None:
                    ord_item["tracking_number"] = tracking_number
                updated = True
                break

        if updated:
            save_orders(orders)
            self.send_json(200, {"success": True, "message": f"Ordine {order_id} aggiornato"})
        else:
            self.send_json(404, {"error": f"Ordine {order_id} non trovato"})
