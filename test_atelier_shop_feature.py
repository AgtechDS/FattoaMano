"""
==============================================================================
TEST SUITE: ATELIER PIETRE SHOP & MODELLI FILTRO DEDICATI
==============================================================================
Verifica formale della nuova architettura:
  1. Integrità del file atelier-pietre.html (Markup, Header, Drawer, Toolbar, Griglia)
  2. Compattamento della Homepage (index.html): anteprima controllata per evitare full scroll
  3. Presenza del pulsante CTA Atelier Pietre (#btnGoToAtelierShop) e banner nello shop
  4. Motore di filtraggio in base agli oggetti presenti in shop (Bracciali)
  5. Filtro Smart Cart ("Solo per il bracciale nel mio carrello")
  6. Integrità JS in app.js e Window Bindings per le funzioni dello shop
  7. Conformità CSS e rispetto rigoroso del Purple Ban
  8. Integrità catalogo minerali (35 pietre con asset locali verificati)
==============================================================================
"""

import unittest
from pathlib import Path
import json

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestAtelierShopFeature(unittest.TestCase):

    def setUp(self):
        self.atelier_html_path = WORKSPACE_DIR / "atelier-pietre.html"
        self.index_html_path = WORKSPACE_DIR / "index.html"
        self.css_path = WORKSPACE_DIR / "style.css"
        self.js_path = WORKSPACE_DIR / "app.js"
        self.catalog_path = WORKSPACE_DIR / "pietre_catalog.json"
        self.assets_dir = WORKSPACE_DIR / "assets" / "pietre"

        self.atelier_html = self.atelier_html_path.read_text(encoding="utf-8")
        self.index_html = self.index_html_path.read_text(encoding="utf-8")
        self.css = self.css_path.read_text(encoding="utf-8")
        self.js = self.js_path.read_text(encoding="utf-8")

    def test_01_atelier_html_structure(self):
        """Verifica che atelier-pietre.html esista e contenga la struttura completa dello Shop Pietre."""
        self.assertTrue(self.atelier_html_path.exists(), "atelier-pietre.html non trovato")
        self.assertIn('id="mainHeader"', self.atelier_html)
        self.assertIn('class="breadcrumb-wrap"', self.atelier_html)
        self.assertIn('id="atelierShopToolbar"', self.atelier_html)
        self.assertIn('id="shopModelFilterPills"', self.atelier_html)
        self.assertIn('id="filterByCartBraceletBtn"', self.atelier_html)
        self.assertIn('id="stoneShopSearchInput"', self.atelier_html)
        self.assertIn('id="stoneResultsCount"', self.atelier_html)
        self.assertIn('id="atelierShopFullGrid"', self.atelier_html)
        self.assertIn('id="cartDrawer"', self.atelier_html)
        self.assertIn('id="checkoutModal"', self.atelier_html)
        self.assertIn('id="toastContainer"', self.atelier_html)
        print("\n[Atelier Test 1] Struttura pagina atelier-pietre.html verificata al 100%")

    def test_02_home_anti_full_scroll_and_cta_button(self):
        """Verifica che la Home abbia il pulsante CTA Atelier Pietre e non crei un sito full scroll."""
        self.assertIn('id="btnGoToAtelierShop"', self.index_html, "Pulsante CTA #btnGoToAtelierShop mancante in index.html")
        self.assertIn('href="atelier-pietre.html"', self.index_html, "Link diretto ad atelier-pietre.html mancante in index.html")
        self.assertIn('class="atelier-shop-cta-card"', self.index_html)
        self.assertIn('class="atelier-explore-more-wrap"', self.index_html)
        
        # In app.js la griglia della home viene limitata per non saturare la pagina
        self.assertIn('slice(0, 6)', self.js, "Compattamento griglia home (slice top 6) mancante in app.js")
        print("\n[Atelier Test 2] Anti-Full Scroll e CTA Atelier Pietre sulla Home validati")

    def test_03_filter_by_shop_items(self):
        """Verifica la presenza dei filtri per gli oggetti presenti nello shop (modelli di bracciali)."""
        required_models = [
            'prod_rame_001',
            'prod_intr_cuff_bottega',
            'prod_intr_corona_regale',
            'prod_intr_modello_2',
            'prod_intr_massiccio_spina',
            'prod_intr_trama_nobile',
            'prod_intr_spiga_polso',
            'prod_rame_002',
            'prod_rame_003',
            'prod_pronta_intrecciato'
        ]
        for model in required_models:
            self.assertIn(f'data-model="{model}"', self.atelier_html, f"Pill filtro per modello {model} mancante")

        print(f"\n[Atelier Test 3] Tutti i {len(required_models)} modelli di bracciali dello shop integrati nei filtri")

    def test_04_smart_cart_filter(self):
        """Verifica il filtro dinamico per bracciale presente nel carrello."""
        self.assertIn('id="filterByCartBraceletBtn"', self.atelier_html)
        self.assertIn('onclick="toggleCartBraceletFilter()"', self.atelier_html)
        self.assertIn('function toggleCartBraceletFilter', self.js)
        self.assertIn('window.toggleCartBraceletFilter = toggleCartBraceletFilter', self.js)
        print("\n[Atelier Test 4] Filtro Smart Cart validato e connesso alle funzioni reattive")

    def test_05_js_shop_engine_functions(self):
        """Verifica le funzioni JS in app.js per il motore dello shop."""
        shop_funcs = [
            'initAtelierShopPage',
            'filterByShopModel',
            'toggleCartBraceletFilter',
            'onStoneSearchInput',
            'onStoneTypeFilterChange',
            'onStoneChakraFilterChange',
            'onStoneElementFilterChange',
            'resetAllStoneFilters',
            'renderAtelierShopFullGrid',
            'addStoneFromShopCard',
            'onShopCardTargetChange'
        ]
        for fn in shop_funcs:
            self.assertIn(f"function {fn}", self.js, f"Funzione JS mancante: {fn}")
            self.assertIn(f"window.{fn} = {fn}", self.js, f"Window binding mancante: {fn}")

        print(f"\n[Atelier Test 5] Tutte le {len(shop_funcs)} funzioni JS dell'Atelier Shop verificate con successo")

    def test_06_css_styling_and_purple_ban(self):
        """Verifica le classi CSS dedicate e il rispetto assoluto del Purple Ban."""
        css_lower = self.css.lower()
        self.assertNotIn("purple", css_lower, "Purple Ban violato in CSS")
        self.assertNotIn("#800080", css_lower)
        self.assertNotIn("#4b0082", css_lower)

        required_classes = [
            '.atelier-shop-cta-card',
            '.stone-shop-toolbar',
            '.shop-filter-pill',
            '.filter-cart-btn',
            '.atelier-full-grid',
            '.stone-shop-card',
            '.stone-compatible-box'
        ]
        for cls in required_classes:
            self.assertIn(cls, self.css, f"Classe CSS mancante: {cls}")

        print("\n[Atelier Test 6] Standard grafici CSS e Purple Ban verificati al 100%")

    def test_07_stone_catalog_and_assets_integrity(self):
        """Verifica che il catalogo contenga 35 minerali con immagini valide in assets/pietre/."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            stones = json.load(f)

        self.assertEqual(len(stones), 35, "Il catalogo deve contenere esattamente 35 pietre autentiche")
        for s in stones:
            self.assertIn("id", s)
            self.assertIn("nome", s)
            self.assertIn("prezzo_vendita", s)
            self.assertIn("compatibilita_bracciali", s, f"Mappatura compatibilità bracciali mancante per {s['nome']}")
            img_path = WORKSPACE_DIR / s["immagine_locale"]
            self.assertTrue(img_path.exists(), f"File immagine mancante: {s['immagine_locale']}")
            self.assertGreater(img_path.stat().st_size, 1000, f"File immagine {s['immagine_locale']} vuoto o danneggiato")

        print(f"\n[Atelier Test 7] 35 minerali autentici con immagini e compatibilità bracciali validati al 100%")


if __name__ == "__main__":
    unittest.main()
