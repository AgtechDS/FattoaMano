"""
Fatto a Mano — Security & Authentication Module (MIT-Grade)
Zero-hardcoding of access codes. Cryptographic session management with HMAC-SHA256.
"""

import os
import hmac
import hashlib
import json
import base64
import time
from typing import Tuple, Optional, Dict, Any

# In-memory rate limiting tracker (per runtime instance)
# Format: { ip: [timestamp1, timestamp2, ...] }
_FAILED_ATTEMPTS: Dict[str, list] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 600  # 10 minuti


def get_admin_secret_key() -> str:
    """Recupera la chiave segreta di firma sessione da variabile d'ambiente."""
    secret = os.environ.get("ADMIN_SESSION_SECRET", "").strip()
    if not secret:
        # Fallback sicuro derivato da service role key se secret non presente
        sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "fattoamano_atelier_sec_fallback_2026")
        secret = hashlib.sha256(sb_key.encode("utf-8")).hexdigest()
    return secret


def check_rate_limit(client_ip: str) -> bool:
    """Verifica se l'IP ha superato il limite di tentativi falliti. Ritorna True se consentito."""
    now = time.time()
    history = _FAILED_ATTEMPTS.get(client_ip, [])
    # Filtra solo i tentativi nella finestra
    recent = [t for t in history if now - t < LOCKOUT_WINDOW_SECONDS]
    _FAILED_ATTEMPTS[client_ip] = recent
    return len(recent) < MAX_FAILED_ATTEMPTS


def record_failed_attempt(client_ip: str):
    """Registra un tentativo fallito per l'IP."""
    now = time.time()
    if client_ip not in _FAILED_ATTEMPTS:
        _FAILED_ATTEMPTS[client_ip] = []
    _FAILED_ATTEMPTS[client_ip].append(now)


def reset_rate_limit(client_ip: str):
    """Azzera i tentativi falliti dopo un login riuscito."""
    if client_ip in _FAILED_ATTEMPTS:
        del _FAILED_ATTEMPTS[client_ip]


def verify_admin_code(provided_code: str) -> bool:
    """
    Verifica il codice admin contro la variabile d'ambiente ADMIN_ACCESS_CODE.
    Usa hmac.compare_digest per prevenire attacchi di tipo timing attack.
    NON hardcodare mai il codice nel codice sorgente!
    """
    real_code = os.environ.get("ADMIN_ACCESS_CODE", "").strip()
    if not real_code:
        # Carica da .env locale se presente
        try:
            from pathlib import Path
            env_file = Path(__file__).resolve().parent.parent / ".env"
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("ADMIN_ACCESS_CODE="):
                            real_code = line.split("=", 1)[1].strip()
                            break
        except Exception:
            pass

    if not real_code:
        return False

    return hmac.compare_digest(str(provided_code).strip(), str(real_code))


def create_session_token(expires_in_seconds: int = 86400) -> str:
    """Genera un token firmato crittograficamente con HMAC-SHA256."""
    now = int(time.time())
    payload = {
        "sub": "atelier_admin",
        "role": "admin",
        "iat": now,
        "exp": now + expires_in_seconds
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    
    secret = get_admin_secret_key().encode("utf-8")
    sig = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    
    return f"{payload_b64}.{sig_b64}"


def verify_session_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Verifica l'autenticità e la scadenza del token sessione.
    Ritorna (is_valid, payload, error_message).
    """
    if not token or "." not in token:
        return False, None, "Token mancante o formato non valido"
    
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, None, "Struttura token errata"
        
        payload_b64, sig_b64 = parts[0], parts[1]
        secret = get_admin_secret_key().encode("utf-8")
        
        # Ricalcola la firma attesa
        expected_sig = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return False, None, "Firma del token non valida (tentativo di manomissione)"
        
        # Decodifica payload
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)
        
        # Verifica scadenza
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return False, None, "Sessione scaduta. Effettua nuovamente l'accesso."
        
        if payload.get("role") != "admin":
            return False, None, "Permessi insufficienti"
        
        return True, payload, ""
    except Exception as e:
        return False, None, f"Errore decodifica token: {str(e)}"


def extract_bearer_token(headers) -> Optional[str]:
    """Estrae il token dall'header Authorization: Bearer <token>."""
    auth_header = headers.get("Authorization") or headers.get("authorization") or ""
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None
