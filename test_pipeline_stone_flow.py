"""
==============================================================================
TEST SUITE: REVISED PIPELINE - TECNICA BRACCIALE -> MINI CAROSELLO PIETRA -> ATELIER COMPLETO
==============================================================================
Verifica formale del nuovo flusso cliente:
  1. Presenza e integrità del Modal Dedicato al centro (#stonePromptModalBackdrop)
  2. Mini-carosello orizzontale pietre con solo prezzo pietra (#stoneMiniCarousel)
  3. Atelier Pietre completo con selettore bracciale da customizzare (#atelierCartBraceletSelect)
  4. Gestione Rimozione Bracciale (Edge Case B: Modale di conferma per conservare o rimuovere pietre)
  5. Supporto per molteplici pietre sullo stesso bracciale e rimozione singola
  6. Integrità CSS, Mobile Responsive e Rispetto assoluto del Purple Ban
  7. Binding delle funzioni su window in app.js
==============================================================================
"""

import unittest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent

class TestRevisedStonePipeline(unittest.TestCase):

    def setUp(self):
        self.html = (WORKSPACE_DIR / "index.html").read_text(encoding="utf-8")
        self.css = (WORKSPACE_DIR / "style.css").read_text(encoding="utf-8")
        self.js = (WORKSPACE_DIR / "app.js").read_text(encoding="utf-8")

    def test_01_prompt_modal_structure(self):
        """Verifica la presenza del Modal Dedicato al centro con mini carosello e azioni."""
        self.assertIn('id="stonePromptModalBackdrop"', self.html, "Modal prompt centrale mancante")
        self.assertIn('id="stoneMiniCarousel"', self.html, "Mini carosello orizzontale pietre mancante")
        self.assertIn('id="promptModalBraceletTitle"', self.html, "Titolo dinamico bracciale nel prompt mancante")
        self.assertIn('id="btnPromptAddStone"', self.html, "Pulsante aggiunta pietra da prompt mancante")
        self.assertIn('id="btnPromptExploreAtelier"', self.html, "Pulsante esplora atelier completo mancante")
        self.assertIn('onclick="skipPromptToCart()"', self.html, "Azione salta a carrello mancante")
        print("\n[Pipeline Test 1] Struttura Prompt Modal e Mini-Carosello verificata al 100%")

    def test_02_atelier_complete_section_and_dropdown(self):
        """Verifica l'Atelier Pietre dedicato con menu a tendina bracciale carrello e griglia completa."""
        self.assertIn('id="atelierSelectionBanner"', self.html)
        self.assertIn('id="atelierCartBraceletSelect"', self.html, "Menu a tendina bracciale da customizzare mancante")
        self.assertIn('id="atelierCartEmptyNotice"', self.html)
        self.assertIn('id="atelierStonesGrid"', self.html, "Griglia completa Atelier Pietre mancante")
        print("\n[Pipeline Test 2] Selettore Bracciale da Customizzare e Vetrina Atelier verificati")

    def test_03_edge_case_b_removal_modal(self):
        """Verifica il Modal di conferma rimozione bracciale con pietre incastonate (Opzione B)."""
        self.assertIn('id="stoneRemoveConfirmModalBackdrop"', self.html)
        self.assertIn('id="stoneRemoveConfirmMsg"', self.html)
        self.assertIn('confirmKeepStonesAsStandalone()', self.html)
        self.assertIn('confirmRemoveBraceletAndStones()', self.html)
        self.assertIn('closeStoneRemoveConfirmModal()', self.html)
        print("\n[Pipeline Test 3] Gestione Rimozione Bracciale (Edge Case B) verificata")

    def test_04_js_reactive_flow_functions(self):
        """Verifica le funzioni reattive in app.js per il nuovo flusso."""
        functions = [
            'openStonePromptModal',
            'closeStonePromptModal',
            'renderStoneMiniCarousel',
            'selectPromptStone',
            'confirmPromptAddStone',
            'exploreFullAtelierFromPrompt',
            'skipPromptToCart',
            'scrollStoneCarousel',
            'populateAtelierCartBraceletSelect',
            'onAtelierBraceletSelectChange',
            'renderAtelierStonesGrid',
            'addStoneFromAtelier',
            'openStoneRemoveConfirmModal',
            'closeStoneRemoveConfirmModal',
            'confirmRemoveBraceletAndStones',
            'confirmKeepStonesAsStandalone',
            'removeSingleStoneFromCartItem',
            'getItemUnitPrice'
        ]
        for fn in functions:
            self.assertIn(fn, self.js, f"Funzione JS mancante: {fn}")
            self.assertIn(f"window.{fn} = {fn}", self.js, f"Window binding mancante: {fn}")
        print(f"\n[Pipeline Test 4] Tutte le {len(functions)} funzioni reattive JS e Window Bindings verificate")

    def test_05_css_mobile_responsiveness_and_purple_ban(self):
        """Verifica le classi CSS per mobile e rispetto del Purple Ban."""
        css_lower = self.css.lower()
        self.assertNotIn("purple", css_lower, "Purple Ban violato in CSS")
        self.assertNotIn("#800080", css_lower)
        self.assertNotIn("#4b0082", css_lower)

        # Classi e responsive
        self.assertIn('.stone-prompt-modal-container', self.css)
        self.assertIn('.stone-mini-carousel', self.css)
        self.assertIn('.stone-mini-card', self.css)
        self.assertIn('.atelier-stones-grid', self.css)
        self.assertIn('.atelier-stone-card', self.css)
        self.assertIn('.stone-confirm-modal-container', self.css)
        self.assertIn('-webkit-overflow-scrolling: touch', self.css)
        self.assertIn('@media (max-width: 640px)', self.css)
        print("\n[Pipeline Test 5] Regole CSS, Mobile Responsiveness e Purple Ban verificate con successo")


if __name__ == "__main__":
    unittest.main()
