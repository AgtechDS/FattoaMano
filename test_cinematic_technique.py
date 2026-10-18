"""
==============================================================================
FATTO A MANO — CINEMATIC TECHNIQUE SHOWCASE & MODAL TEST SUITE
==============================================================================
Validates:
1. Branding Image Asset existence, integrity and format (branding_tecnica_intrecciati.jpg).
2. Strict prohibition: Zero occurrences of 'artigiano' or any synonyms in index.html, app.js, style.css.
3. Component as interactive trigger / button for modal and direct gallery jump.
4. Cinematic Site Design HUD, anamorphic vignette, ember glow, floating dust particles.
5. Technique Modal with macro stage, hotspots, 3-step process, and dedicated gallery action.
6. JavaScript controller bindings on window object.
7. Absolute respect of the Purple Ban across all newly added CSS styles.
==============================================================================
"""

import os
import sys
import re
import unittest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestCinematicTechniqueModule(unittest.TestCase):

    def setUp(self):
        self.index_html = (WORKSPACE_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (WORKSPACE_DIR / "app.js").read_text(encoding="utf-8")
        self.style_css = (WORKSPACE_DIR / "style.css").read_text(encoding="utf-8")
        self.branding_img = WORKSPACE_DIR / "assets" / "branding_tecnica_intrecciati.jpg"

    def test_01_branding_image_asset(self):
        """Verifica esistenza e integrità dell'immagine branding macro della tecnica."""
        self.assertTrue(self.branding_img.exists(), "Asset assets/branding_tecnica_intrecciati.jpg mancante!")
        file_size = self.branding_img.stat().st_size
        self.assertGreater(file_size, 100_000, f"Dimensioni immagine non cinematografiche: {file_size} bytes")
        with open(self.branding_img, "rb") as f:
            header = f.read(3)
            self.assertEqual(header, b'\xff\xd8\xff', "Il file branding non è un JPEG valido")
        print(f"\n[Cinematic Test 1] Asset branding verificato: {self.branding_img.name} ({file_size // 1024} KB)")

    def test_02_strict_synonym_sanitization(self):
        """Verifica divieto categorico di 'artigiano' e di tutti i suoi sinonimi/derivazioni."""
        forbidden_stems = [
            "artigian",  # artigiano, artigiana, artigianale, artigianato, etc.
            "boutique & artigianato",
            "gioielleria artigianale"
        ]
        
        for stem in forbidden_stems:
            self.assertNotIn(stem, self.index_html.lower(), f"Trovato '{stem}' in index.html! Solo 'fatto a mano'.")
            self.assertNotIn(stem, self.app_js.lower(), f"Trovato '{stem}' in app.js! Solo 'fatto a mano'.")
            self.assertNotIn(stem, self.style_css.lower(), f"Trovato '{stem}' in style.css! Solo 'fatto a mano'.")
        print("\n[Cinematic Test 2] Divieto sinonimi superato al 100%: zero presenze di 'artigian*'")

    def test_03_component_interactive_trigger(self):
        """Verifica che il modulo grafico funga da pulsante/trigger interattivo verso il modale e la galleria."""
        self.assertIn('id="tecnica-intreccio"', self.index_html)
        self.assertIn('id="cinematicTechniqueCard"', self.index_html)
        self.assertIn('role="button"', self.index_html)
        self.assertIn('tabindex="0"', self.index_html)
        self.assertIn('openTechniqueModal(', self.index_html)
        self.assertIn('goToDedicatedPhotoGallery(', self.index_html)
        self.assertIn('assets/branding_tecnica_intrecciati.jpg', self.index_html)
        print("\n[Cinematic Test 3] Modulo grafico e trigger pulsante interattivo verificati con successo")

    def test_04_cinematic_technique_modal(self):
        """Verifica la struttura del modale cinematografico con visione macro e navigazione alla collezione."""
        self.assertIn('id="techniqueModalBackdrop"', self.index_html)
        self.assertIn('id="techniqueModal"', self.index_html)
        self.assertIn('cinematic-stage-image', self.index_html)
        self.assertIn('cinematic-hotspot', self.index_html)
        self.assertIn('cinematic-process-grid', self.index_html)
        self.assertIn('btn-cinematic-gateway', self.index_html)
        self.assertIn("goToDedicatedPhotoGallery('Intrecciati')", self.index_html)
        print("\n[Cinematic Test 4] Modale cinematografico con macro stage, hotspot e CTA galleria verificato")

    def test_05_javascript_controllers(self):
        """Verifica le funzioni controller e l'esposizione globale su window."""
        self.assertIn('function openTechniqueModal', self.app_js)
        self.assertIn('function closeTechniqueModal', self.app_js)
        self.assertIn('function goToDedicatedPhotoGallery', self.app_js)
        self.assertIn('window.openTechniqueModal = openTechniqueModal', self.app_js)
        self.assertIn('window.closeTechniqueModal = closeTechniqueModal', self.app_js)
        self.assertIn('window.goToDedicatedPhotoGallery = goToDedicatedPhotoGallery', self.app_js)
        self.assertIn('renderProducts()', self.app_js)
        self.assertIn('scrollIntoView', self.app_js)
        print("\n[Cinematic Test 5] Controller JS e filtri dedicati verificati su window")

    def test_06_cinematic_site_design_and_purple_ban(self):
        """Verifica regole di cinematographic site design e rispetto assoluto del Purple Ban."""
        cinematic_selectors = [
            ".cinematic-technique-section",
            ".cinematic-card",
            ".cinematic-hud",
            ".cinematic-dust-field",
            ".cinematic-lens-flare",
            ".cinematic-modal-container",
            ".cinematic-stage"
        ]
        for sel in cinematic_selectors:
            self.assertIn(sel, self.style_css, f"Selettore CSS mancante: {sel}")

        # Purple Ban verification on cinematic styles
        cinematic_css_block = self.style_css[self.style_css.find("CINEMATOGRAPHIC SITE DESIGN"):]
        forbidden_purple = ["purple", "violet", "#800080", "#8a2be2", "#4b0082", "#9400d3", "#9932cc", "#ba55d3"]
        for p in forbidden_purple:
            self.assertNotIn(p, cinematic_css_block.lower(), f"Trovato colore vietato '{p}' nel blocco cinematico!")

        print("\n[Cinematic Test 6] Cinematographic Site Design e Purple Ban verificati al 100%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
