import os
import json
import urllib.request

DEST_DIR = r"e:\Agtechdesigne\AGTECHDESIGNE_v001\Workspace\FattoAMano\assets\pietre"
os.makedirs(DEST_DIR, exist_ok=True)

SELECTED_STONES = [
    {
        "id": "pietra_acquamarina",
        "nome": "Acquamarina S",
        "tipo": "Burattato levigato (2 - 2,5 cm)",
        "prezzo_fornitore": 3.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Calma profonda, chiarezza interiore, distensione emotiva e apertura della comunicazione autentica.",
        "elemento": "Acqua",
        "chakra": "Gola (5° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17acq003_2_1724082990_94.jpg",
        "file_locale": "acquamarina_s.jpg"
    },
    {
        "id": "pietra_ametista",
        "nome": "Ametista Naturale S",
        "tipo": "Burattato levigato (2 - 3 cm)",
        "prezzo_fornitore": 2.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Serenità spirituale, riequilibrio dei ritmi del sonno, lucidità mentale e purificazione energetica.",
        "elemento": "Aria / Etere",
        "chakra": "Terzo Occhio & Corona (6°-7° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17ame001_2_1724147678_31.jpg",
        "file_locale": "ametista_s.jpg"
    },
    {
        "id": "pietra_agata_blu",
        "nome": "Agata Blu M-L",
        "tipo": "Burattato pebble (3 - 4 cm)",
        "prezzo_fornitore": 4.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Pace della mente, scioglimento delle tensioni comunicative e armonia nelle relazioni quotidiane.",
        "elemento": "Acqua",
        "chakra": "Gola (5° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17aga008_2_1724082029_90.jpg",
        "file_locale": "agata_blu.jpg"
    },
    {
        "id": "pietra_corniola",
        "nome": "Agata Corniola S",
        "tipo": "Burattato vivente (1,5 - 3 cm)",
        "prezzo_fornitore": 2.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Vitalità ardente, forza creativa, coraggio nelle decisioni e stimolo della circolazione sanguigna.",
        "elemento": "Fuoco",
        "chakra": "Sacrale & Radice (1°-2° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17cor004_3_1658497901_634_1724147218_23.jpg",
        "file_locale": "corniola_s.jpg"
    },
    {
        "id": "pietra_amazzonite",
        "nome": "Amazzonite S-M",
        "tipo": "Burattato vellutato (2 - 2,5 cm)",
        "prezzo_fornitore": 3.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Scudo naturale contro le frequenze elettromagnetiche, armonia interiore, libertà e determinazione.",
        "elemento": "Terra / Acqua",
        "chakra": "Cuore & Gola (4°-5° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/whatsapp-image-2024-12-19-at-15.10.49_1734617505_86.jpg",
        "file_locale": "amazzonite_sm.jpg"
    },
    {
        "id": "pietra_agata_verde",
        "nome": "Agata Verde L",
        "tipo": "Burattato pebble (3 cm)",
        "prezzo_fornitore": 4.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Riequilibrio energetico del cuore, stabilità emotiva, abbondanza e profondo contatto con la natura.",
        "elemento": "Terra",
        "chakra": "Cuore (4° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17aga007_2_1724082116_74.jpg",
        "file_locale": "agata_verde.jpg"
    },
    {
        "id": "pietra_agata_muschiata",
        "nome": "Agata Muschiata M",
        "tipo": "Burattato naturale (2,5 - 3 cm)",
        "prezzo_fornitore": 3.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Rigenerazione e rinascita, connessione botanica, benessere corporeo e liberazione dallo stress.",
        "elemento": "Terra",
        "chakra": "Cuore (4° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17AGM1M1_1.jpg",
        "file_locale": "agata_muschiata.jpg"
    },
    {
        "id": "pietra_adularia",
        "nome": "Pietra di Luna (Adularia Grezza)",
        "tipo": "Grezzo naturale (1 - 2 cm)",
        "prezzo_fornitore": 3.30,
        "prezzo_vendita": 10.00,
        "proprieta": "Risonanza con le fasi lunari, risveglio dell'intuito profondo, equilibrio ormonale e dolcezza d'animo.",
        "elemento": "Acqua",
        "chakra": "Corona (7° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/01plu001_2_1689674306_112_1732994241_7.jpg",
        "file_locale": "adularia_grezza.jpg"
    },
    {
        "id": "pietra_avventurina",
        "nome": "Avventurina Verde Grezza",
        "tipo": "Grezzo compatto (3 - 4 cm)",
        "prezzo_fornitore": 3.00,
        "prezzo_vendita": 10.00,
        "proprieta": "Pietra della buona sorte, amplificatore di ottimismo, vitalità espansiva e purificazione vitale.",
        "elemento": "Terra",
        "chakra": "Cuore (4° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/01avv001_2_1732998636_91.jpg",
        "file_locale": "avventurina_grezza.jpg"
    },
    {
        "id": "pietra_ambra_baltica",
        "nome": "Ambra Baltica Naturale S",
        "tipo": "Resina fossile autentica (2 - 2,5 cm)",
        "prezzo_fornitore": 5.00,
        "prezzo_vendita": 16.00,
        "proprieta": "Dono solare millenario: riscalda il corpo, allevia infiammazioni fisiche e dissipa negatività emotiva.",
        "elemento": "Fuoco / Sole",
        "chakra": "Plesso Solare (3° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17amb001_2_1724147431_21.jpg",
        "file_locale": "ambra_baltica_s.jpg"
    },
    {
        "id": "pietra_ametista_chevron",
        "nome": "Ametista Chevron XL",
        "tipo": "Pietra sciamanica a bande (7 - 9 cm)",
        "prezzo_fornitore": 8.00,
        "prezzo_vendita": 18.00,
        "proprieta": "Vibrazione trasmutativa potente: purificazione dell'aura, visione interiore e radicamento spirituale.",
        "elemento": "Aria / Etere",
        "chakra": "Terzo Occhio (6° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/17ame006_1_1747837195_66.jpg",
        "file_locale": "ametista_chevron_xl.jpg"
    },
    {
        "id": "pietra_blue_lace",
        "nome": "Agata Pizzo Blu (Blue Lace)",
        "tipo": "Pietra con foro per pendente (2,5 cm)",
        "prezzo_fornitore": 10.00,
        "prezzo_vendita": 20.00,
        "proprieta": "Armonizzatore sublime: distende l'ansia, dona serenità angelica e apre canali di calma interiore.",
        "elemento": "Aria / Acqua",
        "chakra": "Gola (5° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/25cdofor_1_1781528950_30.jpg",
        "file_locale": "blue_lace_forata.jpg"
    },
    {
        "id": "pietra_ambra_grezza_ml",
        "nome": "Ambra Baltica Grezza M-L",
        "tipo": "Pepita grezza massiccia (6 - 8 cm)",
        "prezzo_fornitore": 20.00,
        "prezzo_vendita": 38.00,
        "proprieta": "Rara resina fossile di grandi dimensioni: scudo bioelettrico, calore rigenerativo e carica bioenergetica.",
        "elemento": "Sole / Fuoco",
        "chakra": "Plesso Solare (3° Chakra)",
        "immagine_remota": "https://store.didoni.com/media/prodotti/01amb001_2_1729244434_99.jpg",
        "file_locale": "ambra_grezza_ml.jpg"
    },
    {
        "id": "pietra_cintamani",
        "nome": "Agni Manitite (Cintamani Stone S)",
        "tipo": "Tektite perla di fuoco rara",
        "prezzo_fornitore": 27.00,
        "prezzo_vendita": 48.00,
        "proprieta": "Gemma sacra leggendaria: amplificatore della volontà superiore, risveglio kundalini e forte magnetismo.",
        "elemento": "Fuoco Cosmico",
        "chakra": "Plesso Solare & Radice",
        "immagine_remota": "https://store.didoni.com/media/prodotti/01agni001_2_1729244386_49.jpg",
        "file_locale": "cintamani_s.jpg"
    },
    {
        "id": "pietra_serafinite",
        "nome": "Grezzo di Serafinite (Pietra degli Angeli)",
        "tipo": "Minerale raro di Siberia (4 x 4 x 3 cm - 68.9 g)",
        "prezzo_fornitore": 35.00,
        "prezzo_vendita": 55.00,
        "proprieta": "La celebre 'Pietra degli Angeli' del lago Baikal con piumature d'argento vivo. Connette con le guide spirituali, purifica l'aura, dissipa conflitti interiori e apre il cuore a frequenze elevate.",
        "elemento": "Etere / Cuore",
        "chakra": "Cuore Spirituale & Corona",
        "immagine_remota": "https://store.didoni.com/media/prodotti/01SER006_1.jpg",
        "file_locale": "serafinite_grezza.jpg"
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for stone in SELECTED_STONES:
    local_path = os.path.join(DEST_DIR, stone["file_locale"])
    stone["immagine_locale"] = f"assets/pietre/{stone['file_locale']}"
    if not os.path.exists(local_path):
        try:
            print(f"Downloading {stone['nome']} -> {stone['file_locale']}...")
            req = urllib.request.Request(stone["immagine_remota"], headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(local_path, "wb") as out:
                    out.write(resp.read())
            print(f"  OK: {local_path} ({os.path.getsize(local_path)} bytes)")
        except Exception as e:
            print(f"  FAILED: {stone['immagine_remota']} -> {e}")
    else:
        print(f"Already exists: {stone['file_locale']}")

# Save json catalog directly in Workspace/FattoAMano
catalog_path = r"e:\Agtechdesigne\AGTECHDESIGNE_v001\Workspace\FattoAMano\pietre_catalog.json"
with open(catalog_path, "w", encoding="utf-8") as f:
    json.dump(SELECTED_STONES, f, indent=2, ensure_ascii=False)

print(f"\nSaved pietre_catalog.json ({len(SELECTED_STONES)} pietre)")
