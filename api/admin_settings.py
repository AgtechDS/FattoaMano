from http.server import BaseHTTPRequestHandler
import json
import os
import time
import urllib.request
import urllib.error
import sys
from pathlib import Path

# Assicura import del modulo di sicurezza
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from admin_security import verify_session_token, extract_bearer_token
except ImportError:
    from api.admin_security import verify_session_token, extract_bearer_token

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_SETTINGS_FILE = BASE_DIR / "settings_cache.json"

DEFAULT_SETTINGS = {
    "announcement_text": "✦ Spedizione Gratuita in tutta Italia per ordini superiori a 80€ ✦ Rame Puro 99.9% Fatto a Mano",
    "announcement_active": True,
    "pronta_consegna_banner_title": "Pronta Consegna",
    "pronta_consegna_banner_subtitle": "Opere esclusive già forgiate ad incudine, pronte per la spedizione immediata",
    "pronta_consegna_badge": "✦ PEZZI UNICI DISPONIBILI",
    "free_shipping_threshold": 80.0,
    "shipping_cost": 10.0,
    "updated_at": "2026-11-18T00:00:00Z"
}


def get_current_settings() -> dict:
    """Legge le impostazioni correnti da Supabase o fallback cache locale."""
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if sb_url and sb_key:
        try:
            req = urllib.request.Request(
                f"{sb_url}/rest/v1/fattoamano_settings?key=eq.general&select=value,updated_at",
                headers={
                    "apikey": sb_key,
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=4) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    if isinstance(data, list) and len(data) > 0 and "value" in data[0]:
                        val = data[0]["value"]
                        if isinstance(val, dict):
                            val["updated_at"] = data[0].get("updated_at")
                            return val
        except Exception as e:
            print(f"[Supabase Settings Read Warning]: {e}")

    if CACHE_SETTINGS_FILE.exists():
        try:
            with open(CACHE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return DEFAULT_SETTINGS


def save_settings(new_settings: dict) -> bool:
    """Salva le impostazioni su Supabase (PATCH/POST) e sulla cache locale se scrivibile."""
    new_settings["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # 1. Salva cache locale (gestisce in sicurezza ambienti read-only come Vercel Lambda)
    try:
        with open(CACHE_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        # Ignora errori di filesystem read-only su ambienti serverless
        pass

    # 2. Salva su Supabase
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if sb_url and sb_key:
        payload_bytes = json.dumps({
            "key": "general",
            "value": new_settings,
            "updated_at": new_settings["updated_at"]
        }).encode("utf-8")

        # Tentativo A: PATCH mirata su chiave esistente
        try:
            req_patch = urllib.request.Request(
                f"{sb_url}/rest/v1/fattoamano_settings?key=eq.general",
                data=payload_bytes,
                headers={
                    "apikey": sb_key,
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                method="PATCH"
            )
            with urllib.request.urlopen(req_patch, timeout=5) as res_patch:
                if res_patch.status in (200, 204):
                    return True
        except Exception as e_patch:
            print(f"[Supabase PATCH warning]: {e_patch}")

        # Tentativo B: Upsert POST fallback
        try:
            req_post = urllib.request.Request(
                f"{sb_url}/rest/v1/fattoamano_settings",
                data=payload_bytes,
                headers={
                    "apikey": sb_key,
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                },
                method="POST"
            )
            with urllib.request.urlopen(req_post, timeout=5) as res_post:
                return res_post.status in (200, 201, 204)
        except Exception as e_post:
            print(f"[Supabase POST warning]: {e_post}")
            return False

    return True


def execute_save(handler_instance):
    """
    Funzione di salvataggio autonoma compatibile sia con handler Vercel
    che con chiamate delegate da index.py / server.py.
    """
    token = extract_bearer_token(handler_instance.headers)
    is_valid, _, error_msg = verify_session_token(token)
    if not is_valid:
        send_response_json(handler_instance, 401, {"success": False, "error": f"Accesso non autorizzato: {error_msg}"})
        return

    content_length = int(handler_instance.headers.get("Content-Length", 0))
    body_raw = handler_instance.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
    try:
        incoming = json.loads(body_raw)
    except Exception:
        send_response_json(handler_instance, 400, {"success": False, "error": "Payload JSON non valido"})
        return

    current = get_current_settings()
    for key in ["announcement_text", "announcement_active", "pronta_consegna_banner_title",
                "pronta_consegna_banner_subtitle", "pronta_consegna_badge",
                "free_shipping_threshold", "shipping_cost"]:
        if key in incoming:
            current[key] = incoming[key]

    success = save_settings(current)
    send_response_json(handler_instance, 200, {
        "success": success,
        "message": "Impostazioni e costi di spedizione aggiornati con successo",
        "settings": current
    })


def send_response_json(handler_instance, status_code: int, data: dict):
    """Utility di invio JSON sicura, funzionante con qualsiasi classe handler HTTP."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler_instance.send_response(status_code)
    handler_instance.send_header("Content-Type", "application/json; charset=utf-8")
    handler_instance.send_header("Content-Length", str(len(payload)))
    handler_instance.send_header("Access-Control-Allow-Origin", "*")
    handler_instance.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
    handler_instance.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler_instance.end_headers()
    handler_instance.wfile.write(payload)


class handler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        send_response_json(self, status_code, data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        settings = get_current_settings()
        send_response_json(self, 200, settings)

    def do_POST(self):
        execute_save(self)

    def do_PUT(self):
        execute_save(self)
