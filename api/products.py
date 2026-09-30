from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
from pathlib import Path

FALLBACK_PRODUCTS = [
    {
        "id": "prod_pronta_intrecciato",
        "title": "Bracciale Intrecciato in Pronta Consegna",
        "price": 30.0,
        "currency": "EUR",
        "description": "Pezzo unico già forgiato ad incudine e rifinito in atelier, disponibile per spedizione immediata.",
        "category": "Intrecciati",
        "purity": "99.9% Rame Puro",
        "in_stock": True,
        "pronta_consegna": True,
        "stock_qty": 1,
        "shipping_note": "Disponibile in bottega • Spedizione espressa tracciata 3-5 giorni lavorativi",
        "image_url": "assets/prontaconsegna/bracciale_intrecciato_pronta.jpg"
    },
    {
        "id": "prod_rame_001",
        "title": "Bracciale Intrecciato 3 Filamenti",
        "price": 30.0,
        "currency": "EUR",
        "description": "Forgiato a mano con 3 trefoli di rame massiccio ritorti a caldo. Chiusura artigianale a gancio S-Hook con battitura a martello. Proprietà armonizzanti ed elevata conducibilità energetica.",
        "category": "Intrecciati",
        "purity": "99.9% Rame Puro",
        "in_stock": True,
        "pronta_consegna": False,
        "stock_qty": 2,
        "shipping_note": "Forgiato su misura • Consegna tracciata 3-5 giorni lavorativi",
        "image_url": "assets/Intrecciati/bracciale_3_filamenti.jpg"
    },
    {
        "id": "prod_rame_002",
        "title": "Cuff Martellato Ossidato",
        "price": 45.0,
        "currency": "EUR",
        "description": "Fascia solida in rame grezzo lavorata ad incudine con trama a nido d'ape battuta a mano. Trattamento protettivo biologico con cera d'api vergine per preservare la lucentezza calda nel tempo.",
        "category": "Martellati",
        "purity": "99.9% Rame Puro",
        "in_stock": True,
        "pronta_consegna": False,
        "stock_qty": 1,
        "shipping_note": "Forgiato su misura • Consegna tracciata 3-5 giorni lavorativi",
        "image_url": "assets/Martellati ossidati/bracciale_martellato.jpg"
    },
    {
        "id": "prod_rame_003",
        "title": "Bangle Minimal Chisel",
        "price": 25.0,
        "currency": "EUR",
        "description": "Profilo circolare essenziale in puro rame elettrolitico, impreziosito da delicatissime micro-cesellature perimetrali. Un gioiello scultoreo raffinato e discreto per il benessere quotidiano.",
        "category": "Rigidi",
        "purity": "99.9% Rame Puro",
        "in_stock": True,
        "pronta_consegna": False,
        "stock_qty": 3,
        "shipping_note": "Forgiato su misura • Consegna tracciata 3-5 giorni lavorativi",
        "image_url": "assets/rigidi/bracciale_rigido_puro.jpg"
    }
]

def fetch_products():
    # 1. Prova da Supabase via PostgREST nativo
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if sb_url and sb_key:
        try:
            endpoint = f"{sb_url}/rest/v1/fattoamano_products?select=*&in_stock=eq.true&order=created_at.desc"
            req = urllib.request.Request(endpoint, headers={
                "apikey": sb_key,
                "Authorization": f"Bearer {sb_key}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    if isinstance(data, list) and len(data) > 0:
                        return data
        except Exception:
            pass

    # 2. Prova cache file su disco
    current_dir = Path(__file__).resolve().parent
    cache_paths = [
        current_dir.parent / "products_cache.json",
        current_dir / "products_cache.json"
    ]
    for p in cache_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception:
                pass

    # 3. Fallback embedded garantito
    return FALLBACK_PRODUCTS


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        products = fetch_products()
        res_bytes = json.dumps(products, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(res_bytes)
