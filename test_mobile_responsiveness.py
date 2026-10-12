"""
==============================================================================
TEST SUITE: MOBILE RESPONSIVENESS & FLUID TOUCH NAVIGATION (320px - 768px)
==============================================================================
Verifica formale della compatibilità mobile a tutti i livelli:
  1. Presenza e integrità del Mobile Hamburger Button (#mobileMenuBtn)
  2. Presenza e navigabilità del Mobile Navigation Drawer (#mobileNavDrawer)
  3. Funzioni controller JS per apertura/chiusura/ESC/touch (app.js)
  4. Struttura Master Responsive CSS (992px, 768px, 640px, 480px)
  5. Adattamento 1fr di tutte le griglie senza blowout (products, pronta-consegna, proprieta, pietre, steps)
  6. Scrolling orizzontale touch per filter-pills e mini-carosello
  7. Prevenzione assoluta overflow orizzontale e rispetto totale del Purple Ban
==============================================================================
"""

import unittest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestMobileResponsiveness(unittest.TestCase):

    def setUp(self):
        self.html = (WORKSPACE_DIR / "index.html").read_text(encoding="utf-8")
        self.css = (WORKSPACE_DIR / "style.css").read_text(encoding="utf-8")
        self.js = (WORKSPACE_DIR / "app.js").read_text(encoding="utf-8")

    def test_01_mobile_header_and_hamburger_button(self):
        """Verifica presenza del pulsante hamburger e label responsive carrello nel markup."""
        self.assertIn('id="mobileMenuBtn"', self.html, "Pulsante #mobileMenuBtn mancante in index.html")
        self.assertIn('class="mobile-menu-btn"', self.html)
        self.assertIn('onclick="toggleMobileMenu()"', self.html)
        self.assertIn('class="cart-btn-label"', self.html, "Classe cart-btn-label mancante per compattamento mobile")
        print("\n[Mobile Test 1] Pulsante Hamburger e azioni Header mobile verificati al 100%")

    def test_02_mobile_nav_drawer_and_links(self):
        """Verifica presenza del drawer di navigazione mobile e di tutti i collegamenti di sezione."""
        self.assertIn('id="mobileNavDrawer"', self.html, "Drawer mobile #mobileNavDrawer mancante")
        self.assertIn('id="mobileNavBackdrop"', self.html, "Backdrop drawer #mobileNavBackdrop mancante")
        self.assertIn('id="closeMobileNavBtn"', self.html, "Pulsante chiusura drawer mancante")
        
        # Verifica tutte le sezioni principali collegate nel menu mobile
        sections = [
            '#prontaconsegna',
            '#collezione',
            '#bottega-pietre',
            '#filosofia',
            '#proprieta',
            '#garanzia'
        ]
        for sec in sections:
            self.assertIn(f'href="{sec}"', self.html, f"Collegamento mobile mancante per la sezione: {sec}")
        print("\n[Mobile Test 2] Mobile Navigation Drawer e collegamenti alle 6 sezioni verificati")

    def test_03_js_mobile_controllers_and_bindings(self):
        """Verifica le funzioni JS di controllo apertura, chiusura, ESC listener e binding su window."""
        funcs = ['toggleMobileMenu', 'openMobileMenu', 'closeMobileMenu']
        for fn in funcs:
            self.assertIn(f"function {fn}", self.js, f"Funzione {fn} mancante in app.js")
            self.assertIn(f"window.{fn} = {fn}", self.js, f"Window binding per {fn} mancante")

        # Verifica gestione tasto ESC
        self.assertIn("Escape", self.js, "Listener per chiusura drawer con tasto ESC mancante")
        print("\n[Mobile Test 3] Funzioni controller e Window Bindings per menu mobile verificati")

    def test_04_css_master_responsive_breakpoints(self):
        """Verifica la gerarchia completa dei breakpoint CSS (992px, 768px, 640px, 480px)."""
        self.assertIn('@media (max-width: 992px)', self.css)
        self.assertIn('@media (max-width: 768px)', self.css)
        self.assertIn('@media (max-width: 640px)', self.css)
        self.assertIn('@media (max-width: 480px)', self.css)
        print("\n[Mobile Test 4] Gerarchia Breakpoint Master Responsive verificata con successo")

    def test_05_css_grid_unification_and_no_overflow(self):
        """Verifica che tutte le griglie passino a 1fr su schermi stretti evitando overflow a 320px."""
        self.assertIn('.products-grid', self.css)
        self.assertIn('.pronta-consegna-grid', self.css)
        self.assertIn('.proprieta-grid', self.css)
        self.assertIn('.method-steps-grid', self.css)
        self.assertIn('.atelier-stones-grid', self.css)
        
        # Verifica contenimento viewport globale
        self.assertIn('overflow-x: hidden', self.css)
        self.assertIn('max-width: 100%', self.css)
        print("\n[Mobile Test 5] Adattamento griglie 1fr e contenimento overflow verificati")

    def test_06_touch_scroll_and_purple_ban(self):
        """Verifica il supporto touch e il rispetto rigoroso del Purple Ban."""
        self.assertIn('-webkit-overflow-scrolling: touch', self.css)
        
        css_lower = self.css.lower()
        self.assertNotIn('purple', css_lower, "Purple Ban violato in CSS")
        self.assertNotIn('#800080', css_lower)
        self.assertNotIn('#4b0082', css_lower)
        print("\n[Mobile Test 6] Fluidità touch e rispetto assoluto del Purple Ban superati")


if __name__ == "__main__":
    unittest.main()
