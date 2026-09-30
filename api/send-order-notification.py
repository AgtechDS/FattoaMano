from http.server import BaseHTTPRequestHandler
import json
import os
import time
import urllib.request
import urllib.error

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
            try:
                payload_js = {
                    "service_id": emailjs_service,
                    "template_id": emailjs_template,
                    "user_id": emailjs_public,
                    "template_params": {
                        "to_email": target_email,
                        "email": shipping_info.get("email", target_email),
                        "order_id": order_id,
                        "data_ordine": time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()),
                        "destinatario_nome": shipping_info.get("fullName", ""),
                        "destinatario_email": shipping_info.get("email", ""),
                        "destinatario_telefono": shipping_info.get("phone", ""),
                        "misura_polso": shipping_info.get("wristCm", "Calibratura Standard"),
                        "wrist_cm": shipping_info.get("wristCm", "Calibratura Standard"),
                        "indirizzo": shipping_info.get("address", ""),
                        "cap": shipping_info.get("cap", ""),
                        "citta": shipping_info.get("city", ""),
                        "provincia": shipping_info.get("province", ""),
                        "note_consegna": shipping_info.get("notes", "Nessuna istruzione particolare"),
                        "subtotal": f"{subtotal:.2f}",
                        "spese_spedizione": f"{shipping_fee:.2f}",
                        "totale_ordine": f"{total:.2f}"
                    }
                }
                if emailjs_private:
                    payload_js["accessToken"] = emailjs_private

                req = urllib.request.Request(
                    "https://api.emailjs.com/api/v1.0/email/send",
                    data=json.dumps(payload_js).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    if r.status in (200, 201):
                        emailjs_sent = True
                        status_msg += " • Notifica Email inviata con successo via EmailJS"
            except Exception as e:
                status_msg += f" • Avviso invio: {str(e)}"

        resp = {
            "success": True,
            "order_id": order_id,
            "emailjs_sent": emailjs_sent,
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
