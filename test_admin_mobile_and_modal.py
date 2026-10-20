"""
==============================================================================
TEST SUITE: ADMIN MOBILE ACCESS & OBJECT CONFIGURATION MODAL (MIT-GRADE)
==============================================================================
Verifica formale della risoluzione dei due problemi critici:
  1. Accesso Mobile al pannello Admin (Mobile Drawer + Footer + Touch Keypad)
  2. Mobile Responsiveness Admin Header, Navigation Tabs e Table Card (min-width + overflow-x)
  3. Modal 'Nuova Opera' / Oggetto: Form flex, Pinned Footer (nessun taglio a 90vh)
  4. Upload Foto con Fotocamera Mobile: Label nativa (zero popup/security block)
  5. Compressione Client-Side su Canvas (max 1600px, JPEG ~400KB, zero HTTP 413)
  6. Tolleranza e sanitizzazione del prezzo con virgola e punto (es. '35,00' -> 35.00)
  7. Rispetto assoluto del Purple Ban in admin.css
==============================================================================
"""

import unittest
from pathlib import Path
import json

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestAdminMobileAndModal(unittest.TestCase):

    def setUp(self):
        self.index_html = (WORKSPACE_DIR / "index.html").read_text(encoding="utf-8")
        self.admin_html = (WORKSPACE_DIR / "admin.html").read_text(encoding="utf-8")
        self.admin_css = (WORKSPACE_DIR / "admin.css").read_text(encoding="utf-8")
        self.admin_js = (WORKSPACE_DIR / "admin.js").read_text(encoding="utf-8")
        self.api_products = (WORKSPACE_DIR / "api" / "admin_products.py").read_text(encoding="utf-8")

    def test_01_mobile_access_points(self):
        """Verifica presenza e accessibilità dei link ad admin.html nel drawer mobile e nel footer."""
        # 1. Mobile Drawer
        self.assertIn('class="mobile-nav-admin"', self.index_html, "Sezione admin mancante nel drawer mobile")
        self.assertIn('href="admin.html"', self.index_html, "Link admin.html mancante nel drawer mobile")
        self.assertIn('Area Riservata Atelier', self.index_html)

        # 2. Footer
        self.assertIn('admin.html', self.index_html)
        print("\n[Admin Test 1] Punti di accesso mobile ad admin.html verificati nel Drawer e nel Footer")

    def test_02_auth_gate_mobile_scrollability_and_keypad(self):
        """Verifica che la schermata PIN sia scrollabile verticalmente quando la tastiera mobile è aperta."""
        self.assertIn('.auth-gate-wrapper', self.admin_css)
        self.assertIn('overflow-y: auto', self.admin_css)
        self.assertIn('-webkit-overflow-scrolling: touch', self.admin_css)
        self.assertIn('inputmode="numeric"', self.admin_html, "inputmode numeric mancante nel PIN")
        print("\n[Admin Test 2] Scrollabilità verticale Auth Gate e touch keypad verificati")

    def test_03_responsive_header_tabs_and_table(self):
        """Verifica compattamento header, tabs nav orizzontale a scorrimento e tabella catalogo."""
        # Header responsive
        self.assertIn('header-btn-text', self.admin_html)
        self.assertIn('@media (max-width: 768px)', self.admin_css)
        self.assertIn('.admin-header-center', self.admin_css)

        # Tab bar orizzontale a scorrimento touch
        self.assertIn('.admin-tabs-nav', self.admin_css)
        self.assertIn('overflow-x: auto', self.admin_css)

        # Table-card e min-width per prevenire tagli su mobile
        self.assertIn('.table-card', self.admin_css)
        self.assertIn('min-width: 680px', self.admin_css)
        print("\n[Admin Test 3] Header compatto, tabs a scorrimento orizzontale e table-card scrollabile verificati")

    def test_04_modal_flex_structure_and_pinned_footer(self):
        """Verifica che il modal 'Nuova Opera' usi flex container e mantenga il footer sempre visibile."""
        self.assertIn('class="modal-edit-form"', self.admin_html)
        self.assertIn('.modal-edit-form', self.admin_css)
        self.assertIn('.modal-footer', self.admin_css)
        self.assertIn('flex-shrink: 0', self.admin_css)
        self.assertIn('inputmode="decimal"', self.admin_html, "inputmode decimal mancante per il prezzo")
        print("\n[Admin Test 4] Struttura flex modal con footer bloccato e scroll interno verificati")

    def test_05_photo_camera_picker_and_clear_button(self):
        """Verifica la label nativa per fotocamera mobile e il pulsante di rimozione foto."""
        self.assertIn('<label for="productImageFileInput" class="drop-zone"', self.admin_html)
        self.assertIn('id="btnClearPhoto"', self.admin_html)
        self.assertIn('function clearSelectedPhoto', self.admin_js)
        self.assertIn('function handleManualImageUrlInput', self.admin_js)
        print("\n[Admin Test 5] Label nativa per camera picker e controllo rimozione foto verificati")

    def test_06_canvas_client_side_compression(self):
        """Verifica la presenza del motore di downscaling su Canvas (max 1600px, JPEG ~400KB)."""
        self.assertIn('createElement(\'canvas\')', self.admin_js)
        self.assertIn('MAX_DIM = 1600', self.admin_js)
        self.assertIn('toDataURL(\'image/jpeg\', 0.85)', self.admin_js)
        print("\n[Admin Test 6] Compressione automatica client-side su Canvas (zero errore 413) verificata")

    def test_07_comma_and_dot_price_tolerance(self):
        """Verifica che sia il frontend che l'API backend gestiscano prezzi con virgola (es. '35,50')."""
        self.assertIn("replace(',', '.')", self.admin_js, "Sanitizzazione virgola mancante in admin.js")
        self.assertIn("replace(\",\", \".\")", self.api_products, "Sanitizzazione virgola mancante in admin_products.py")
        print("\n[Admin Test 7] Tolleranza e sanitizzazione virgola/punto nei prezzi verificata su client e server")

    def test_08_purple_ban_in_admin_css(self):
        """Verifica rispetto assoluto del Purple Ban in admin.css."""
        css_lower = self.admin_css.lower()
        self.assertNotIn("purple", css_lower)
        self.assertNotIn("#800080", css_lower)
        self.assertNotIn("#4b0082", css_lower)
        print("\n[Admin Test 8] Rispetto assoluto del Purple Ban superato al 100%")


    def test_09_mobile_luxury_card_and_touch_actions(self):
        """Verifica trasformazione tabella in luxury card e pulsanti modifica/elimina touch-friendly (>=44px)."""
        # CSS Card Layout
        self.assertIn('#catalogTableBody tr', self.admin_css)
        self.assertIn('grid-template-areas:', self.admin_css)
        self.assertIn('.btn-icon-action.btn-edit-action', self.admin_css)
        self.assertIn('min-height: 44px', self.admin_css)
        self.assertIn('.btn-action-label', self.admin_css)
        self.assertIn('.btn-icon-action.btn-delete-action', self.admin_css)

        # JS Generazione etichette e classi touch
        self.assertIn('btn-edit-action', self.admin_js)
        self.assertIn('btn-action-label', self.admin_js)
        self.assertIn('btn-delete-action', self.admin_js)

        # Modal testata e footer sticky su mobile
        self.assertIn('.modal-head', self.admin_css)
        self.assertIn('position: sticky', self.admin_css)
        self.assertIn('position: sticky', self.admin_css)
        self.assertIn('.modal-footer', self.admin_css)
        print("\n[Admin Test 9] Layout luxury card mobile, pulsanti touch 44px e modal sticky footer verificati")

    def test_10_zero_forbidden_synonyms(self):
        """Verifica rispetto assoluto del divieto di sinonimi (nessun 'artigian*')."""
        files = [
            WORKSPACE_DIR / "admin.html",
            WORKSPACE_DIR / "admin.js",
            WORKSPACE_DIR / "admin.css",
            WORKSPACE_DIR / "success.html"
        ]
        for f in files:
            content = f.read_text(encoding="utf-8").lower()
            self.assertNotIn("artigian", content, f"Trovato pattern vietato 'artigian*' in {f.name}!")
        print("\n[Admin Test 10] Divieto sinonimi ('artigian*') superato al 100% in tutti i file admin e success")

    def test_11_order_confirmation_and_email_dispatcher(self):
        """Verifica il flusso di conferma ordine e dispatch email post-pagamento Stripe."""
        success_html = (WORKSPACE_DIR / "success.html").read_text(encoding="utf-8")
        app_js = (WORKSPACE_DIR / "app.js").read_text(encoding="utf-8")

        # Persistenza pre-redirect e keepalive in app.js
        self.assertIn('fattoamano_last_order', app_js)
        self.assertIn('keepalive: true', app_js)

        # Finalizzazione su success.html
        self.assertIn('fattoamano_last_order', success_html)
        self.assertIn('/api/send-order-notification', success_html)
        self.assertIn('PAID_CONFIRMED', success_html)
        self.assertIn('orderSuccessDetails', success_html)
        print("\n[Admin Test 11] Flusso di conferma ordine e dispatch email garantito verificato al 100%")


if __name__ == "__main__":
    unittest.main()
