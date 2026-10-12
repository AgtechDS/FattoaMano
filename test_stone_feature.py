"""
==============================================================================
TEST SUITE: BOTTEGA DELLE PIETRE & PERSONALIZZAZIONE (DIDONI STORE)
==============================================================================
Verifica formale:
  1. Integrità del catalogo pietre (pietre_catalog.json)
  2. Presenza e validità degli asset grafici scaricati da Didoni (assets/pietre/)
  3. Logica di adattamento prezzi (pietre base a 10€, pietre rare con margine fornitore es. Serafinite 35€ -> 55€)
  4. Integrazione HTML & Form di richiesta info / personalizzazione
  5. Integrità CSS & Rispetto del Purple Ban
  6. Presenza delle funzioni JavaScript reattive in app.js
  7. Endpoint Backend /api/stone-inquiry e protocollo protocollo ordini
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


class TestStoneWorkshopFeature(unittest.TestCase):

    def setUp(self):
        self.catalog_path = WORKSPACE_DIR / "pietre_catalog.json"
        self.assets_dir = WORKSPACE_DIR / "assets" / "pietre"
        self.index_html_path = WORKSPACE_DIR / "index.html"
        self.style_css_path = WORKSPACE_DIR / "style.css"
        self.app_js_path = WORKSPACE_DIR / "app.js"

    def test_01_stone_catalog_integrity(self):
        """Verifica che pietre_catalog.json contenga almeno 15 pietre ben formate con campi essenziali."""
        self.assertTrue(self.catalog_path.exists(), "pietre_catalog.json non esiste")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            stones = json.load(f)

        self.assertGreaterEqual(len(stones), 15, "Devono essere presenti almeno 15 pietre Didoni")
        
        serafinite_found = False
        for s in stones:
            self.assertIn("id", s)
            self.assertIn("nome", s)
            self.assertIn("prezzo_fornitore", s)
            self.assertIn("prezzo_vendita", s)
            self.assertIn("proprieta", s)
            self.assertIn("immagine_locale", s)
            self.assertIn("immagine_remota", s)
            self.assertGreater(s["prezzo_vendita"], 0)
            
            if "serafinite" in s["id"].lower():
                serafinite_found = True
                self.assertEqual(s["prezzo_fornitore"], 35.0, "Prezzo fornitore Serafinite deve essere 35.0€")
                self.assertGreater(s["prezzo_vendita"], 35.0, "Prezzo vendita Serafinite deve superare il costo fornitore")

        self.assertTrue(serafinite_found, "Grezzo di Serafinite non trovato nel catalogo")
        print(f"\n[Test 1] Integrità catalogo pietre superata ({len(stones)} minerali verificati)")

    def test_02_stone_image_assets_exist(self):
        """Verifica che tutte le immagini locali delle pietre siano presenti e non vuote."""
        self.assertTrue(self.assets_dir.exists(), "Directory assets/pietre non esiste")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            stones = json.load(f)

        for s in stones:
            img_rel = s["immagine_locale"]
            img_path = WORKSPACE_DIR / img_rel
            self.assertTrue(img_path.exists(), f"Immagine locale mancante: {img_rel}")
            self.assertGreater(img_path.stat().st_size, 1000, f"Immagine {img_rel} è vuota o corrotta")

        print(f"\n[Test 2] Tutti gli asset grafici locali verificati con successo ({len(stones)} immagini)")

    def test_03_pricing_adaptation_logic(self):
        """Verifica la logica di adattamento prezzi per garantire margine su pietre fornitore > 10€."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            stones = json.load(f)

        for s in stones:
            cost = s["prezzo_fornitore"]
            price = s["prezzo_vendita"]
            if cost <= 4.0:
                self.assertEqual(price, 10.0, f"Pietra standard {s['nome']} deve avere prezzo fisso 10€")
            else:
                self.assertGreater(price, cost, f"Pietra {s['nome']} (costo {cost}€) deve avere prezzo > costo ({price}€)")
                # Verificare che ci sia margine per lavorazione (almeno +8€)
                self.assertGreaterEqual(price - cost, 8.0, f"Margine insufficiente su {s['nome']}")

        print(f"\n[Test 3] Logica di adattamento prezzi e margini lavorazione validata con successo")

    def test_04_html_integration(self):
        """Verifica che index.html contenga la sezione #bottega-pietre, i link di navigazione, l'atelier e il modal prompt."""
        content = self.index_html_path.read_text(encoding="utf-8")
        
        self.assertIn('id="bottega-pietre"', content, "Sezione #bottega-pietre mancante in index.html")
        self.assertIn('href="#bottega-pietre"', content, "Link di navigazione Bottega Pietre mancante")
        self.assertIn('id="atelierCartBraceletSelect"', content, "Select bracciale cart mancante")
        self.assertIn('id="atelierStonesGrid"', content, "Griglia Atelier Pietre mancante")
        self.assertIn('id="stonePromptModalBackdrop"', content, "Prompt modal pietre mancante")
        self.assertIn('id="stoneMiniCarousel"', content, "Mini-carosello pietre mancante")
        self.assertIn('id="btnPromptAddStone"', content, "Pulsante aggiunta pietra mancante")
        self.assertIn('id="modalCustomizeStoneBtn"', content, "Pulsante personalizza con pietra in modal mancante")

        print(f"\n[Test 4] Integrazione HTML e componenti Atelier validata")

    def test_05_css_luxury_and_purple_ban(self):
        """Verifica la presenza delle classi CSS per la bottega pietre e il rispetto del Purple Ban."""
        css_content = self.style_css_path.read_text(encoding="utf-8")

        self.assertIn('.bottega-pietre-section', css_content)
        self.assertIn('.stone-workshop-grid', css_content)
        self.assertIn('.stone-gem-viewport', css_content)
        self.assertIn('.stone-chip', css_content)

        # Purple Ban: no #800080, #4b0082, #8a2be2, #9370db
        forbidden_purples = ['#800080', '#4b0082', '#8a2be2', '#9370db', '#a855f7', '#8b5cf6', '#7c3aed']
        for color in forbidden_purples:
            self.assertNotIn(color, css_content.lower(), f"Violazione Purple Ban rilevata in style.css: {color}")

        print(f"\n[Test 5] Stili CSS di lusso e Purple Ban verificati con successo")

    def test_06_js_reactive_functions(self):
        """Verifica che app.js contenga e leghi a window tutte le funzioni reattive per la Bottega delle Pietre."""
        js_content = self.app_js_path.read_text(encoding="utf-8")

        self.assertIn('loadStones', js_content)
        self.assertIn('onStoneSelectChange', js_content)
        self.assertIn('addStoneCustomToCart', js_content)
        self.assertIn('handleStoneCustomizationSubmit', js_content)
        self.assertIn('customizeCurrentModalBracelet', js_content)
        self.assertIn('cart-item-stone-badge', js_content)

        # Window exposures
        self.assertIn('window.onStoneSelectChange = onStoneSelectChange', js_content)
        self.assertIn('window.addStoneCustomToCart = addStoneCustomToCart', js_content)
        self.assertIn('window.handleStoneCustomizationSubmit = handleStoneCustomizationSubmit', js_content)

        print(f"\n[Test 6] Funzioni reattive in app.js verificate con successo")

    def test_07_backend_stone_inquiry_endpoint(self):
        """Verifica la funzione log_stone_inquiry del server backend."""
        test_payload = {
            "fullName": "Test Cliente",
            "email": "test@fattoamano.test",
            "phone": "+39 333 9999999",
            "wrist_cm": "18 cm",
            "stone": {
                "id": "pietra_serafinite",
                "name": "Grezzo di Serafinite",
                "price": 55.0,
                "supplier_price": 35.0
            },
            "bracelet": {
                "id": "prod_rame_001",
                "title": "Bracciale Intrecciato 3 Filamenti",
                "price": 30.0
            },
            "notes": "Test inserimento pietra e verifica log",
            "total_estimated": 85.0
        }

        result = server.log_stone_inquiry(test_payload)
        self.assertTrue(result.get("success"), "log_stone_inquiry deve restituire success=True")
        self.assertTrue(result.get("inquiry_id").startswith("INFO-PIETRA-"), "ID protocollo errato")

        # Verifica che il file stone_inquiries.json esista e contenga il record
        inquiries_file = WORKSPACE_DIR / "stone_inquiries.json"
        self.assertTrue(inquiries_file.exists())
        with open(inquiries_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0]["customer_name"], "Test Cliente")
        self.assertEqual(records[0]["total_estimated"], 85.0)

        print(f"\n[Test 7] Backend inquiry logger e protocollo {result.get('inquiry_id')} validato con successo")


if __name__ == "__main__":
    unittest.main()
