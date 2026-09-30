from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

# Assicura import del modulo di sicurezza
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from admin_security import verify_session_token, extract_bearer_token
except ImportError:
    from api.admin_security import verify_session_token, extract_bearer_token

BASE_DIR = Path(__file__).resolve().parent.parent
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
        """Elenco di tutti gli ordini registrati."""
        if not self.check_auth():
            self.send_json(401, {"error": "Non autorizzato. Effettua l'accesso admin."})
            return

        orders = get_orders()
        self.send_json(200, {
            "success": True,
            "count": len(orders),
            "orders": orders
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
