from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import sys
from pathlib import Path

# Assicura che la directory api sia nel path per import locali
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from admin_security import (
        verify_admin_code,
        create_session_token,
        verify_session_token,
        extract_bearer_token,
        check_rate_limit,
        record_failed_attempt,
        reset_rate_limit
    )
except ImportError:
    from api.admin_security import (
        verify_admin_code,
        create_session_token,
        verify_session_token,
        extract_bearer_token,
        check_rate_limit,
        record_failed_attempt,
        reset_rate_limit
    )


class handler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def get_client_ip(self) -> str:
        forwarded = self.headers.get("x-forwarded-for") or self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0] if hasattr(self, "client_address") and self.client_address else "127.0.0.1"

    def do_GET(self):
        """Verifica se il token di sessione fornito in Authorization è ancora valido."""
        token = extract_bearer_token(self.headers)
        if not token:
            self.send_json(401, {"authenticated": False, "error": "Token mancante"})
            return

        is_valid, payload, error_msg = verify_session_token(token)
        if is_valid:
            self.send_json(200, {
                "authenticated": True,
                "role": payload.get("role", "admin"),
                "expires_at": payload.get("exp")
            })
        else:
            self.send_json(401, {"authenticated": False, "error": error_msg})

    def do_POST(self):
        """Autenticazione con codice PIN d'accesso (confrontato con variabile d'ambiente ADMIN_ACCESS_CODE)."""
        client_ip = self.get_client_ip()

        # Controllo anti-bruteforce
        if not check_rate_limit(client_ip):
            self.send_json(429, {
                "success": False,
                "error": "Troppi tentativi falliti. Accesso temporaneamente bloccato per motivi di sicurezza (10 min)."
            })
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body_raw)
        except Exception:
            data = {}

        code = str(data.get("code", "")).strip()
        if not code:
            self.send_json(400, {"success": False, "error": "Inserire il codice di accesso"})
            return

        # Verifica sicura contro ADMIN_ACCESS_CODE d'ambiente
        if verify_admin_code(code):
            reset_rate_limit(client_ip)
            token = create_session_token(expires_in_seconds=86400)
            self.send_json(200, {
                "success": True,
                "token": token,
                "expires_in": 86400,
                "message": "Autenticazione atelier completata con successo"
            })
        else:
            record_failed_attempt(client_ip)
            self.send_json(401, {
                "success": False,
                "error": "Codice di accesso non valido. Riprova."
            })
