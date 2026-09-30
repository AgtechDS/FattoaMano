import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_DIR = Path(__file__).resolve().parent
load_dotenv(WORKSPACE_DIR / ".env", override=True)

url = 'https://api.emailjs.com/api/v1.0/email/send'

service_id = os.getenv('EMAILJS_SERVICE_ID', 'service_1m1tfyq').strip()
template_id = os.getenv('EMAILJS_TEMPLATE_ID', 'template_i4boqs9').strip()
public_key = os.getenv('EMAILJS_PUBLIC_KEY', 'Ts44-OGlmsSUV73rR').strip()
private_key = os.getenv('EMAILJS_PRIVATE_KEY', '').strip()
target_email = os.getenv('EMAILJS_TO_EMAIL', 'agtechdesigne@gmail.com').strip()

payload = {
    'service_id': service_id,
    'template_id': template_id,
    'user_id': public_key,
    'template_params': {
        'to_email': target_email,
        'email': target_email,
        'order_id': 'FAM-TEST-COLLEGA-999',
        'data_ordine': '30/09/2026, 23:15:00',
        'destinatario_nome': 'Collaudo Simulazione Fatto a Mano',
        'customer_name': 'Collaudo Simulazione Fatto a Mano',
        'destinatario_email': target_email,
        'customer_email': target_email,
        'destinatario_telefono': '+39 333 9876543',
        'customer_phone': '+39 333 9876543',
        'indirizzo': 'Via dell\'Artigianato 10',
        'cap': '50123',
        'citta': 'Firenze',
        'provincia': 'FI',
        'note_consegna': 'Ordine simulato per test recapito email notifica ad agtechdesigne@gmail.com',
        'shipping_notes': 'Simulazione acquisto con successo',
        'orders': [
            {
                'name': 'Bracciale Rame Puro 3 Filamenti Torciti 99.9%',
                'units': 1,
                'price': '30.00',
                'image_url': 'https://mkeykuouwsbjezdgwskq.supabase.co/storage/v1/object/public/fattoamano-products/bracciale_3_filamenti.jpg'
            }
        ],
        'articoli_ordine': '• Bracciale Rame Puro 3 Filamenti Torciti 99.9% (x1) - €30.00',
        'subtotal': '30.00',
        'spese_spedizione': '6.00',
        'totale_ordine': '36.00',
        'cost': {
            'shipping': '6.00',
            'tax': '0.00',
            'total': '36.00'
        },
        'cost.shipping': '6.00',
        'cost.tax': '0.00',
        'cost.total': '36.00'
    }
}

if private_key:
    payload['accessToken'] = private_key
    print(f"[Config] EMAILJS_PRIVATE_KEY rilevata ({private_key[:4]}***). Inclusa in payload come accessToken.")
else:
    print("[Config] EMAILJS_PRIVATE_KEY non presente in .env (invio solo con Public Key).")

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode('utf-8')
        print(f"\nSTATUS CODE: {resp.status}")
        print(f"RESPONSE BODY: {body}")
        print("--> INVIO EMAIL RIUSCITO CON SUCCESSO AD agtechdesigne@gmail.com <--")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f"\nHTTP ERROR: {e.code} - {err_body}")
    if e.code == 403 and "Strict mode" in err_body:
        print("\n[DIAGNOSTICA ERRORE 403]:")
        print("La Strict Mode su EmailJS è attiva. Per risolvere:")
        print("1. Opzione A (Disattivazione Strict Mode): Accedi a EmailJS Dashboard -> Account -> Security -> disattiva 'Strict Mode'.")
        print("2. Opzione B (Inserimento Private Key): Accedi a EmailJS Dashboard -> Account -> Security -> copia la 'Private Key' e incollala in Workspace/FattoAMano/.env come EMAILJS_PRIVATE_KEY=tua_chiave.")
except Exception as e:
    print(f"EXCEPTION: {e}")
