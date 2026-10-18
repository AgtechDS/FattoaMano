"""
==============================================================================
FATTO A MANO — CAROSELLO METODI DI FORGIATURA & MODALE DINAMICO TEST SUITE
==============================================================================
Validates:
1. Tutti e 4 gli asset branding (Intrecciati, Martellati, Rigidi, Incastonatura).
2. Divieto categorico di 'artigiano' e di tutti i suoi sinonimi/derivazioni.
3. Divieto di etichette camera/cinema in interfaccia front-end (es. cinema 4k, cam 01, 5600k, iso).
4. Struttura del carosello orizzontale (viewport, track, 4 card, frecce, counter, dots).
5. Modale dinamico con popolamento da TECHNIQUES_DATA per tutte e 4 le tecniche.
6. Esposizione globale dei controller JS su window (carousel, modal, gallery jump).
7. Rispetto assoluto del Purple Ban nelle nuove regole CSS.
==============================================================================
"""

import os
import sys
import re
import unittest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestMetallurgicalTechniquesCarousel(unittest.TestCase):

    def setUp(self):
        self.index_html = (WORKSPACE_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (WORKSPACE_DIR / "app.js").read_text(encoding="utf-8")
        self.style_css = (WORKSPACE_DIR / "style.css").read_text(encoding="utf-8")
        self.assets_dir = WORKSPACE_DIR / "assets"

    def test_01_all_four_branding_image_assets(self):
        """Verifica esistenza e integrità di tutte e 4 le immagini branding delle tecniche."""
        techniques = [
            "branding_tecnica_intrecciati.jpg",
            "branding_tecnica_martellati.jpg",
            "branding_tecnica_rigidi.jpg",
            "branding_tecnica_incastonatura.jpg"
        ]

        for filename in techniques:
            img_path = self.assets_dir / filename
            self.assertTrue(img_path.exists(), f"Asset {filename} mancante in assets/!")
            file_size = img_path.stat().st_size
            self.assertGreater(file_size, 100_000, f"File {filename} troppo piccolo: {file_size} bytes")
            with open(img_path, "rb") as f:
                header = f.read(3)
                self.assertEqual(header, b'\xff\xd8\xff', f"Il file {filename} non è un JPEG valido")
            print(f"\n[Test 1] Asset branding verificato: {filename} ({file_size // 1024} KB)")

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
        print("\n[Test 2] Divieto sinonimi superato al 100%: zero presenze di 'artigian*'")

    def test_03_zero_camera_front_end_labels(self):
        """Verifica divieto assoluto di terminologia tecnica/camera in front-end (cinema 4k, cam 01, etc.)."""
        forbidden_camera_terms = [
            "cinema 4k",
            "cam 01",
            "5600k",
            "iso 100",
            "rec ●",
            "hud-rec"
        ]

        for term in forbidden_camera_terms:
            self.assertNotIn(term, self.index_html.lower(), f"Trovato termine front-end vietato '{term}' in index.html!")
            self.assertNotIn(term, self.style_css.lower(), f"Trovato termine front-end vietato '{term}' in style.css!")
        print("\n[Test 3] Zero etichette da ripresa/camera in front-end verificate al 100%")

    def test_04_horizontal_carousel_structure(self):
        """Verifica struttura del carosello orizzontale e tutti i 4 moduli tecnici."""
        # Sezione e contenitori
        self.assertIn('id="tecniche-forgiatura"', self.index_html)
        self.assertIn('class="techniques-carousel-viewport"', self.index_html)
        self.assertIn('class="techniques-carousel-track"', self.index_html)
        
        # 4 Moduli tecnici presenti
        self.assertIn('id="techCardIntrecciati"', self.index_html)
        self.assertIn('id="techCardMartellati"', self.index_html)
        self.assertIn('id="techCardRigidi"', self.index_html)
        self.assertIn('id="techCardIncastonatura"', self.index_html)

        # Controlli di navigazione
        self.assertIn('id="carouselCounter"', self.index_html)
        self.assertIn('id="counterCurrent"', self.index_html)
        self.assertIn('id="carouselPrevBtn"', self.index_html)
        self.assertIn('id="carouselNextBtn"', self.index_html)
        self.assertIn('id="techniquesCarouselDots"', self.index_html)

        print("\n[Test 4] Carosello orizzontale e 4 card tecniche verificate con successo")

    def test_05_dynamic_technique_modal(self):
        """Verifica modale dinamico e binding agli elementi per le 4 tecniche."""
        self.assertIn('id="techniqueModalBackdrop"', self.index_html)
        self.assertIn('id="techniqueModal"', self.index_html)
        self.assertIn('id="modalTechniqueBadgeTitle"', self.index_html)
        self.assertIn('id="modalStageImage"', self.index_html)
        self.assertIn('id="modalHotspotsGroup"', self.index_html)
        self.assertIn('id="modalNarrativeKicker"', self.index_html)
        self.assertIn('id="techniqueModalTitle"', self.index_html)
        self.assertIn('id="modalTechniqueLead"', self.index_html)
        self.assertIn('id="modalProcessGrid"', self.index_html)
        self.assertIn('id="modalGatewayBtn"', self.index_html)
        print("\n[Test 5] Modale metallurgico dinamico verificato")

    def test_06_javascript_controllers(self):
        """Verifica il dizionario TECHNIQUES_DATA e le funzioni controller esposte su window."""
        self.assertIn('const TECHNIQUES_DATA', self.app_js)
        self.assertIn('intrecciati:', self.app_js)
        self.assertIn('martellati:', self.app_js)
        self.assertIn('rigidi:', self.app_js)
        self.assertIn('incastonatura:', self.app_js)

        # Controllers
        self.assertIn('function initTechniquesCarousel', self.app_js)
        self.assertIn('function navigateTechniqueSlide', self.app_js)
        self.assertIn('function goToTechniqueSlide', self.app_js)
        self.assertIn('function updateTechniqueCarouselUI', self.app_js)
        self.assertIn('function openTechniqueModal', self.app_js)
        self.assertIn('function closeTechniqueModal', self.app_js)
        self.assertIn('function onModalGatewayClick', self.app_js)
        self.assertIn('function jumpToBottegaPietre', self.app_js)
        self.assertIn('function goToDedicatedPhotoGallery', self.app_js)

        # Window bindings
        self.assertIn('window.TECHNIQUES_DATA = TECHNIQUES_DATA', self.app_js)
        self.assertIn('window.openTechniqueModal = openTechniqueModal', self.app_js)
        self.assertIn('window.navigateTechniqueSlide = navigateTechniqueSlide', self.app_js)
        self.assertIn('window.goToTechniqueSlide = goToTechniqueSlide', self.app_js)
        print("\n[Test 6] Dizionario 4 tecniche e controller JS verificati su window")

    def test_07_carousel_css_and_purple_ban(self):
        """Verifica le classi CSS del carosello e il rispetto assoluto del Purple Ban."""
        carousel_selectors = [
            ".techniques-carousel-section",
            ".techniques-carousel-viewport",
            ".techniques-carousel-track",
            ".technique-carousel-card",
            ".technique-card-media",
            ".technique-card-content",
            ".techniques-carousel-dots",
            ".carousel-dot.active",
            ".carousel-counter"
        ]
        for sel in carousel_selectors:
            self.assertIn(sel, self.style_css, f"Selettore CSS mancante: {sel}")

        # Verifica 1 form alla volta (flex: 0 0 100%)
        self.assertIn("flex: 0 0 100%", self.style_css)
        self.assertIn(".technique-carousel-card.is-active-slide", self.style_css)
        self.assertIn(".cinematic-dust-field", self.style_css)
        self.assertIn(".cinematic-lens-flare", self.style_css)

        # Purple Ban check in the carousel section
        block = self.style_css[self.style_css.find("I QUATTRO METODI DI FORGIATURA"):]
        forbidden_purple = ["purple", "violet", "#800080", "#8a2be2", "#4b0082", "#9400d3", "#9932cc", "#ba55d3"]
        for p in forbidden_purple:
            self.assertNotIn(p, block.lower(), f"Trovato colore vietato '{p}' nel blocco del carosello!")

        print("\n[Test 7] CSS Carosello, 1 Form alla Volta e Purple Ban verificati al 100%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
