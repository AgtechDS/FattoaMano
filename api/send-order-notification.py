from http.server import BaseHTTPRequestHandler
import json
import os
import time
import ssl
import urllib.request
import urllib.error

def send_telegram_order_alert(order_id: str, shipping_info: dict, items: list, total: float) -> bool:
    """Invia notifica push istantanea via Telegram al titolare dell'Atelier."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    owner_id = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
    if not token or not owner_id:
        return False
    try:
        items_txt = "\n".join([f"• {it.get('title') or it.get('name', 'Bracciale Rame')} (x{it.get('quantity', 1)}) - €{float(it.get('price', 0))*int(it.get('quantity', 1)):.2f}" for it in items]) or "1x Bracciale Fatto a Mano"
        msg = (
            f"📦 <b>[NUOVO ORDINE FATTO A MANO] #{order_id}</b>\n\n"
            f"💰 <b>Totale:</b> €{total:.2f}\n"
            f"👤 <b>Cliente:</b> {shipping_info.get('fullName', 'N/D')}\n"
            f"📧 <b>Email:</b> {shipping_info.get('email', 'N/D')}\n"
            f"📞 <b>Cellulare:</b> {shipping_info.get('phone', 'N/D')}\n"
            f"📏 <b>Misura Polso:</b> <code>{shipping_info.get('wristCm', 'Standard')}</code>\n"
            f"🚚 <b>Spedizione:</b> {shipping_info.get('address', '')}, {shipping_info.get('cap', '')} {shipping_info.get('city', '')} ({shipping_info.get('province', '')})\n"
            f"📝 <b>Note:</b> {shipping_info.get('notes', 'Nessuna nota')}\n\n"
            f"💍 <b>Opere Ordinate:</b>\n{items_txt}\n\n"
            f"✨ <i>Notifica istantanea Bot Telegram AGOS</i>"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": owner_id, "text": msg, "parse_mode": "HTML"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"[Telegram Alert Dispatch Notice]: {e}")
        return False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body_raw)
        except Exception:
            data = {}

        order_id = data.get("order_id") or f"FAM-{int(time.time() * 1000) % 1000000:06d}"
        shipping_info = data.get("shipping_info", {})
        items = data.get("items", [])
        total = float(data.get("total", 0.0))
        subtotal = float(data.get("subtotal", total - 6.0 if total > 6.0 else total))
        shipping_fee = float(data.get("shipping_fee", 6.0))

        # Configurazione EmailJS
        emailjs_service = os.environ.get("EMAILJS_SERVICE_ID", "service_1m1tfyq").strip()
        emailjs_template = os.environ.get("EMAILJS_TEMPLATE_ID", "template_i4boqs9").strip()
        emailjs_public = os.environ.get("EMAILJS_PUBLIC_KEY", "Ts44-OGlmsSUV73rR").strip()
        emailjs_private = os.environ.get("EMAILJS_PRIVATE_KEY", "Kryxmh9ayPFRn10UMXLO7").strip()
        target_email = os.environ.get("EMAILJS_TO_EMAIL", "agtechdesigne@gmail.com").strip()

        emailjs_sent = False
        status_msg = f"Ordine #{order_id} elaborato su Vercel Serverless"

        if emailjs_service and emailjs_template and emailjs_public:
            # Formattazione lista articoli per template EmailJS
            orders_list = []
            for it in items:
                p = float(it.get("price", 30.0))
                q = int(it.get("quantity", 1))
                orders_list.append({
                    "name": str(it.get("title") or it.get("name") or "Bracciale in Puro Rame 99.9%"),
                    "units": q,
                    "price": f"{p * q:.2f}"
                })
            items_text = "\n".join([f"• {o['name']} (x{o['units']}) - €{o['price']}" for o in orders_list]) or "• 1x Bracciale in Puro Rame 99.9%"

            base_params = {
                "order_id": order_id,
                "data_ordine": time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()),
                "destinatario_nome": shipping_info.get("fullName", ""),
                "customer_name": shipping_info.get("fullName", ""),
                "destinatario_email": shipping_info.get("email", ""),
                "customer_email": shipping_info.get("email", ""),
                "destinatario_telefono": shipping_info.get("phone", ""),
                "customer_phone": shipping_info.get("phone", ""),
                "misura_polso": shipping_info.get("wristCm", "Calibratura Standard"),
                "wrist_cm": shipping_info.get("wristCm", "Calibratura Standard"),
                "indirizzo": shipping_info.get("address", ""),
                "cap": shipping_info.get("cap", ""),
                "citta": shipping_info.get("city", ""),
                "provincia": shipping_info.get("province", ""),
                "note_consegna": shipping_info.get("notes", "Nessuna istruzione particolare"),
                "shipping_notes": shipping_info.get("notes", "Nessuna istruzione particolare"),
                "subtotal": f"{subtotal:.2f}",
                "spese_spedizione": f"{shipping_fee:.2f}",
                "totale_ordine": f"{total:.2f}",
                "orders": orders_list,
                "articoli_ordine": items_text,
                "cost": {
                    "shipping": f"{shipping_fee:.2f}",
                    "tax": "0.00",
                    "total": f"{total:.2f}"
                }
            }

            customer_email = (shipping_info.get("email") or "").strip()
            recipients = []
            if customer_email and "@" in customer_email:
                recipients.append(customer_email)
            if target_email and target_email not in recipients:
                recipients.append(target_email)

            for rec in recipients:
                try:
                    p_params = dict(base_params)
                    p_params["email"] = rec
                    p_params["to_email"] = rec

                    payload_js = {
                        "service_id": emailjs_service,
                        "template_id": emailjs_template,
                        "user_id": emailjs_public,
                        "template_params": p_params
                    }
                    if emailjs_private:
                        payload_js["accessToken"] = emailjs_private

                    req = urllib.request.Request(
                        "https://api.emailjs.com/api/v1.0/email/send",
                        data=json.dumps(payload_js).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        }
                    )
                    ctx = ssl.create_default_context()
                    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                        if r.status in (200, 201):
                            emailjs_sent = True
                            status_msg += f" • Notifica Email inviata a {rec}"
                except Exception as e:
                    status_msg += f" • Avviso invio {rec}: {str(e)}"

        # Notifica istantanea Telegram al titolare
        telegram_sent = send_telegram_order_alert(order_id, shipping_info, items, total)
        if telegram_sent:
            status_msg += " • Inviato alert istantaneo su Telegram"

        resp = {
            "success": True,
            "order_id": order_id,
            "emailjs_sent": emailjs_sent,
            "telegram_sent": telegram_sent,
            "target_email": target_email,
            "message": status_msg
        }

        payload = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)
