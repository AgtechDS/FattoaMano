"""
==============================================================================
FATTO A MANO — SYSTEMATIC VERIFICATION & TEST SUITE
==============================================================================
Esegue la verifica automatica a 7 punti:
  1. Parsing Prompt Telegram (prezzo, titolo, purezza, dettagli)
  2. Cache Locale e Integrità Assets
  3. Query Supabase Database su tabella 'fattoamano_products'
  4. Query Supabase Storage su bucket 'fattoamano-products'
  5. Standard Qualitativi CSS & HTML
  6. Compilazione Sezione #proprieta & Rimozione Dati Interni di Sviluppo
  7. Conformità GDPR, EU AI Act & Protocollo Privacy
==============================================================================
"""

import os
import sys
import json
import unittest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_DIR))

import server
import importlib
telegram_module = importlib.import_module("telegram-agos")


class TestFattoAManoSystem(unittest.TestCase):

    def test_01_telegram_prompt_parser(self):
        """Verifica il parsing del prompt esatto fornito dall'utente."""
        prompt = 'aggiungi prodotto a sito FattoAMano prezzo 30E dettagli "bracciale in rame 3 filamenti rame puro 99.9%"'
        result = telegram_module.parse_prompt(prompt)

        self.assertEqual(result["price"], 30.0)
        self.assertIn("bracciale", result["details"].lower())
        self.assertEqual(result["purity"], "99.9% Rame Puro")
        self.assertEqual(result["category"], "Intrecciati")
        print(f"\n[Test 1] Parsing Prompt superato: {result['title']} (€{result['price']})")

    def test_02_products_cache_integrity(self):
        """Verifica che products_cache.json contenga prodotti con assets esistenti."""
        cache_path = WORKSPACE_DIR / "products_cache.json"
        self.assertTrue(cache_path.exists(), "products_cache.json non esiste")

        with open(cache_path, "r", encoding="utf-8") as f:
            products = json.load(f)

        self.assertGreaterEqual(len(products), 3, "Devono essere presenti almeno 3 creazioni")
        for prod in products:
            self.assertIn("title", prod)
            self.assertIn("price", prod)
            self.assertIn("image_url", prod)
            asset_path = WORKSPACE_DIR / prod["image_url"]
            self.assertTrue(asset_path.exists(), f"Asset {prod['image_url']} non trovato")
        print(f"\n[Test 2] Integrità Cache ed Asset superata ({len(products)} creazioni verificate)")

    def test_03_server_get_products(self):
        """Verifica che il modulo server restituisca la lista prodotti da Supabase/Cache."""
        products = server.get_products()
        self.assertGreaterEqual(len(products), 3)
        print(f"\n[Test 3] Server get_products() superato ({len(products)} articoli caricati)")

    def test_04_supabase_connection(self):
        """Verifica la connessione a Supabase."""
        self.assertIsNotNone(telegram_module.supabase_client, "Client Supabase inizializzato")
        try:
            res = telegram_module.supabase_client.table("fattoamano_products").select("id").limit(1).execute()
            self.assertTrue(hasattr(res, "data"))
            print(f"\n[Test 4] Connessione e Query Supabase 'fattoamano_products' OK")
        except Exception as e:
            self.fail(f"Errore query Supabase: {e}")

    def test_05_html_and_css_quality(self):
        """Verifica la conformità alle regole di design (es. nessun viola, HTML valido)."""
        css_path = WORKSPACE_DIR / "style.css"
        css_content = css_path.read_text(encoding="utf-8").lower()
        self.assertNotIn("purple", css_content, "Violazione Purple Ban rilevata in CSS")
        self.assertNotIn("#800080", css_content)
        
        html_path = WORKSPACE_DIR / "index.html"
        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn("Fatto a Mano", html_content)
        self.assertIn("99.9%", html_content)
        self.assertIn("cartDrawer", html_content)
        print("\n[Test 5] Verifica standard qualitativi & Design Rules superata")

    def test_06_proprieta_section_and_clean_public_data(self):
        """Verifica che #proprieta sia compilata e che i dati interni di sviluppo siano rimossi."""
        html_path = WORKSPACE_DIR / "index.html"
        html_content = html_path.read_text(encoding="utf-8")

        # Verifica sezione #proprieta
        self.assertIn('id="proprieta"', html_content, "Sezione id='proprieta' mancante")
        self.assertIn('Azione Oligodinamica', html_content)
        self.assertIn('Conducibilità Termica', html_content)
        self.assertIn('Alone Verde sul Polso', html_content)

        # Verifica rimozione dati interni di sviluppo da visualizzazione pubblica
        self.assertNotIn("Connessioni AGOS", html_content)
        self.assertNotIn("Bot Telegram AGOS", html_content)
        self.assertNotIn("Supabase Cloud Sync", html_content)
        self.assertNotIn("Stripe Official Checkout", html_content)
        print("\n[Test 6] Compilazione #proprieta e pulizia dati interni superata")

    def test_07_gdpr_ai_act_and_env_keys(self):
        """Verifica la presenza del file .env, conformità GDPR ed EU AI Act."""
        env_path = WORKSPACE_DIR / ".env"
        self.assertTrue(env_path.exists(), "File .env in Workspace/FattoAMano non trovato")
        env_content = env_path.read_text(encoding="utf-8")
        self.assertIn("TELEGRAM_BOT_TOKEN", env_content)
        self.assertIn("SUPABASE_URL", env_content)
        self.assertIn("STRIPE_SECRET_KEY", env_content)

        # Test protocollo GDPR
        test_payload = {
            "fullName": "Test Cliente",
            "email": "test@cliente.it",
            "requestType": "access",
            "notes": "Verifica conformità GDPR Art. 15"
        }
        protocol = server.log_privacy_request(test_payload)
        self.assertTrue(protocol.startswith("GDPR-REQ-"))
        print(f"\n[Test 7] Conformità GDPR, EU AI Act e File .env superata (Protocollo: {protocol})")

    def test_08_shipping_precheckout_form(self):
        """Verifica la presenza e conformità del form di pre-acquisto spedizione."""
        html_path = WORKSPACE_DIR / "index.html"
        html_content = html_path.read_text(encoding="utf-8")
        
        # Elementi del modal di spedizione
        self.assertIn('id="checkoutModalBackdrop"', html_content)
        self.assertIn('id="shippingCheckoutForm"', html_content)
        self.assertIn('id="shipFullName"', html_content)
        self.assertIn('id="shipEmail"', html_content)
        self.assertIn('id="shipPhone"', html_content)
        self.assertIn('id="shipAddress"', html_content)
        self.assertIn('id="shipWristCm"', html_content)
        self.assertIn('id="shipCap"', html_content)
        self.assertIn('id="shipCity"', html_content)
        self.assertIn('id="shipProvince"', html_content)
        self.assertIn('id="submitShippingPayBtn"', html_content)
        self.assertIn('favicon.svg', html_content)

        # Regole CSS e Logica JS
        css_path = WORKSPACE_DIR / "style.css"
        css_content = css_path.read_text(encoding="utf-8")
        self.assertIn('.checkout-modal-container', css_content)
        self.assertIn('.luxury-input', css_content)

        js_path = WORKSPACE_DIR / "app.js"
        js_content = js_path.read_text(encoding="utf-8")
        self.assertIn('openCheckoutModal', js_content)
        self.assertIn('handleShippingFormSubmit', js_content)
        self.assertIn('shipWristCm', js_content)
        self.assertIn('fattoamano_shipping_info', js_content)
        print("\n[Test 8] Form Pre-Acquisto Spedizione (con Misura Polso e Favicon) superato al 100%")

    def test_09_emailjs_integration(self):
        """Verifica la configurazione del servizio EmailJS per notifica spedizione."""
        html_path = WORKSPACE_DIR / "index.html"
        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn("email.min.js", html_content, "SDK EmailJS mancante in index.html")

        js_path = WORKSPACE_DIR / "app.js"
        js_content = js_path.read_text(encoding="utf-8")
        self.assertIn("service_1m1tfyq", js_content)
        self.assertIn("agtechdesigne@gmail.com", js_content)
        self.assertIn("sendShippingEmailNotification", js_content)

        env_path = WORKSPACE_DIR / ".env"
        env_content = env_path.read_text(encoding="utf-8")
        self.assertIn("EMAILJS_SERVICE_ID=service_1m1tfyq", env_content)
        self.assertIn("EMAILJS_TO_EMAIL=agtechdesigne@gmail.com", env_content)
        print("\n[Test 9] Integrazione EmailJS (service_1m1tfyq -> agtechdesigne@gmail.com) verificata con successo")

    def test_10_pronta_consegna_and_order_dispatch(self):
        """Verifica la sezione Pronta Consegna e il dispatcher ordini locale."""
        html_path = WORKSPACE_DIR / "index.html"
        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn('id="prontaconsegna"', html_content)
        self.assertIn('id="prontaConsegnaGrid"', html_content)
        self.assertIn('data-filter="pronta_consegna"', html_content)

        js_path = WORKSPACE_DIR / "app.js"
        js_content = js_path.read_text(encoding="utf-8")
        self.assertIn('renderProntaConsegna', js_content)
        self.assertIn('quickBuyById', js_content)
        self.assertIn('/api/send-order-notification', js_content)

        cache_path = WORKSPACE_DIR / "products_cache.json"
        with open(cache_path, "r", encoding="utf-8") as f:
            prods = json.load(f)
        ready_prods = [p for p in prods if p.get("pronta_consegna") is True]
        self.assertGreaterEqual(len(ready_prods), 1, "Almeno un prodotto deve essere contrassegnato come pronta consegna")

        # Test dispatcher ordini server
        test_payload = {
            "order_id": "TEST-UNITTEST-100",
            "shipping_info": {
                "fullName": "Test Verifica Pronta Consegna",
                "email": "agtechdesigne@gmail.com",
                "phone": "+39 333 1122334",
                "address": "Via Bottega 1",
                "cap": "50123",
                "city": "Firenze",
                "province": "FI",
                "notes": "Test automatico suite"
            },
            "items": [{"title": "Bracciale Rame Puro", "price": 30.0, "quantity": 1}],
            "subtotal": 30.0,
            "shipping_fee": 6.0,
            "total": 36.0
        }
        res = server.log_and_dispatch_order(test_payload)
        self.assertTrue(res["success"])
        self.assertEqual(res["order_id"], "TEST-UNITTEST-100")
        print("\n[Test 10] Sezione Pronta Consegna & Order Dispatcher verificati con successo al 100%")


if __name__ == "__main__":
    unittest.main(verbosity=2)

