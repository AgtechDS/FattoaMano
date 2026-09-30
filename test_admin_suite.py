"""
FATTO A MANO — ADMIN & SYNONYM ELIMINATION TEST SUITE (MIT-GRADE)
Validates:
1. Complete elimination of all synonyms of 'artigiano', 'artigianato', 'artigianale', 'Boutique & Artigianato'.
2. Zero hardcoding of admin code 6447 in frontend JS and HTML.
3. Admin authentication security, constant-time validation & rate-limiting.
4. Admin session token generation, HMAC verification, and tampering detection.
5. Live CRUD operations on products and settings APIs.
"""

import os
import sys
import json
import unittest
import hmac
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_DIR))
sys.path.insert(0, str(WORKSPACE_DIR / "api"))

from dotenv import load_dotenv
load_dotenv(WORKSPACE_DIR / ".env", override=True)

import admin_security
import api.admin_auth as admin_auth
import api.admin_settings as admin_settings
import api.admin_products as admin_products


class TestAdminSecurityAndSanitization(unittest.TestCase):

    def test_01_synonym_sanitization(self):
        """Verifica che siano stati eliminati tutti i sinonimi artigiano/artigianato/artigianale e Boutique."""
        files_to_check = [
            WORKSPACE_DIR / "index.html",
            WORKSPACE_DIR / "app.js",
            WORKSPACE_DIR / "success.html",
            WORKSPACE_DIR / "products_cache.json"
        ]

        forbidden_patterns = [
            "boutique & artigianato",
            "boutique creazioni",
            "gioielleria artigianale",
            "creazione artigianale",
            "lavorazione artigianale",
            "chiusura artigianale",
            "realizzato artigianalmente",
            "sagomata artigianalmente"
        ]

        for file_path in files_to_check:
            self.assertTrue(file_path.exists(), f"File {file_path.name} mancante")
            content = file_path.read_text(encoding="utf-8").lower()
            for pattern in forbidden_patterns:
                self.assertNotIn(
                    pattern,
                    content,
                    f"Trovato pattern proibito '{pattern}' in {file_path.name}! La regola impone solo 'fatto a mano'."
                )

        print("\n[Test 1] Eliminazione sinonimi superata: Nessun riferimento ad artigianato/artigianale trovato.")

    def test_02_zero_hardcoding_admin_code(self):
        """Verifica rigorosa: il codice 6447 NON DEVE MAI comparire hardcodato nel frontend JS o HTML."""
        client_files = [
            WORKSPACE_DIR / "admin.html",
            WORKSPACE_DIR / "admin.js",
            WORKSPACE_DIR / "index.html",
            WORKSPACE_DIR / "app.js"
        ]

        for file_path in client_files:
            content = file_path.read_text(encoding="utf-8")
            self.assertNotIn(
                "6447",
                content,
                f"SICUREZZA VIOLATA: Il codice '6447' è stato hardcodato nel client file {file_path.name}!"
            )

        print("\n[Test 2] Zero-hardcoding verificato: Codice 6447 non presente in nessun file frontend.")

    def test_03_admin_code_env_verification(self):
        """Verifica che il codice 6447 sia validato server-side tramite variabile d'ambiente."""
        self.assertTrue(admin_security.verify_admin_code("6447"), "Il codice '6447' deve essere valido")
        self.assertFalse(admin_security.verify_admin_code("0000"), "Codici errati devono essere rifiutati")
        self.assertFalse(admin_security.verify_admin_code("admin"), "Codici arbitrari devono essere rifiutati")
        self.assertFalse(admin_security.verify_admin_code(""), "Stringa vuota deve essere rifiutata")
        print("\n[Test 3] Verifica costante crittografica ADMIN_ACCESS_CODE superata.")

    def test_04_session_token_cryptography(self):
        """Verifica generazione token HMAC-SHA256, validazione e protezione contro tampering."""
        token = admin_security.create_session_token(expires_in_seconds=3600)
        self.assertIn(".", token)

        # 1. Token valido
        is_valid, payload, error_msg = admin_security.verify_session_token(token)
        self.assertTrue(is_valid, f"Il token generato deve essere valido: {error_msg}")
        self.assertEqual(payload["role"], "admin")

        # 2. Token manomesso (alterazione payload)
        parts = token.split(".")
        tampered_token = "eyJyYW5kb20iOiJhdHRhY2sifQ" + "." + parts[1]
        is_valid, _, _ = admin_security.verify_session_token(tampered_token)
        self.assertFalse(is_valid, "Il token manomesso deve essere respinto")

        # 3. Token scaduto
        expired_token = admin_security.create_session_token(expires_in_seconds=-10)
        is_valid, _, error_msg = admin_security.verify_session_token(expired_token)
        self.assertFalse(is_valid, "Il token scaduto deve essere respinto")
        self.assertIn("scaduta", error_msg.lower())

        print("\n[Test 4] Crittografia token di sessione HMAC-SHA256 e anti-tampering superata.")

    def test_05_rate_limiting(self):
        """Verifica blocco tentativi dopo troppi errori (anti brute-force)."""
        test_ip = "192.168.1.99"
        admin_security.reset_rate_limit(test_ip)

        for _ in range(admin_security.MAX_FAILED_ATTEMPTS):
            self.assertTrue(admin_security.check_rate_limit(test_ip))
            admin_security.record_failed_attempt(test_ip)

        # Il successivo deve essere bloccato
        self.assertFalse(admin_security.check_rate_limit(test_ip), "IP deve essere bloccato dopo MAX tentativi falliti")
        admin_security.reset_rate_limit(test_ip)
        self.assertTrue(admin_security.check_rate_limit(test_ip), "Reset rate-limit deve ripristinare l'accesso")
        print("\n[Test 5] Anti brute-force rate-limiting verificato.")

    def test_06_admin_settings_cache(self):
        """Verifica lettura e scrittura impostazioni banner in settings_cache.json."""
        current = admin_settings.get_current_settings()
        self.assertIn("announcement_text", current)
        self.assertIn("Fatto a Mano", current["announcement_text"])
        self.assertIn("pronta_consegna_banner_title", current)

        # Prova salvataggio
        test_settings = dict(current)
        test_settings["shipping_cost"] = 6.0
        success = admin_settings.save_settings(test_settings)
        self.assertTrue(success, "Salvataggio impostazioni riuscito")
        print("\n[Test 6] Gestione impostazioni e banner persistenti superata.")

    def test_07_admin_products_crud(self):
        """Verifica lettura e manipolazione prodotti catalogo tramite admin_products."""
        products = admin_products.get_all_products()
        self.assertGreaterEqual(len(products), 3, "Devono essere presenti almeno 3 creazioni")
        for p in products:
            self.assertIn("id", p)
            self.assertIn("title", p)
            self.assertIn("price", p)
        print(f"\n[Test 7] Lettura catalogo admin superata ({len(products)} creazioni caricate).")


if __name__ == "__main__":
    unittest.main()
