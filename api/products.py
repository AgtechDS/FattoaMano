from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
from pathlib import Path

FALLBACK_PRODUCTS = [
    {
        "id": "prod_1",
        "title": "Bracciale Torsione Rame Puro 99.9%",
        "price": 30.0,
        "description": "Forgiato a mano con tre filamenti intrecciati in puro rame 99.9%. Finitura lucidata a specchio e proprietà antibatteriche naturali.",
        "category": "twisted",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/copper_bracelet_twisted_1790426425823.jpg"
    },
    {
        "id": "prod_2",
        "title": "Cuff Rame Battuto a Martello",
        "price": 45.0,
        "description": "Rigido e scultoreo, battuto a mano secondo l'antica tradizione orafa toscana. Una superficie sfaccettata che cattura la luce ad ogni movimento.",
        "category": "cuff",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/copper_cuff_hammered_1790426443233.jpg"
    },
    {
        "id": "prod_3",
        "title": "Bangle Rame Satinato Lineare",
        "price": 38.0,
        "description": "Design minimale ed ergonomico a profilo tondo continuo. Rame massiccio satinato per un'eleganza sobria e una perfetta conduttività energetica.",
        "category": "bangle",
        "purity": "99.9%",
        "in_stock": True,
        "image_url": "assets/copper_bangle_minimal_1790426465276.jpg"
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
