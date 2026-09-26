from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import urllib.request

try:
    import stripe
except ImportError:
    stripe = None


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

        stripe_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        items = data.get("items", [])
        
        host_header = self.headers.get("Host", "fattoamano.vercel.app")
        origin = self.headers.get("Origin") or f"https://{host_header}"

        success_url = data.get("success_url") or f"{origin}/success.html"
        cancel_url = data.get("cancel_url") or f"{origin}/"

        if not stripe_key:
            res_err = {
                "error": "Chiave Stripe non configurata. Imposta STRIPE_SECRET_KEY nelle variabili d'ambiente Vercel.",
                "url": cancel_url
            }
            self.send_json(400, res_err)
            return

        # Tentativo 1: Libreria ufficiale Stripe
        if stripe:
            stripe.api_key = stripe_key
            try:
                line_items = []
                for it in items:
                    price_val = float(it.get("price", 30))
                    price_cents = int(price_val * 100)
                    title = it.get("title", "Bracciale in Puro Rame 99.9%")
                    img_url = it.get("image_url", "")
                    images = [img_url] if (img_url.startswith("http://") or img_url.startswith("https://")) else []

                    line_items.append({
                        "price_data": {
                            "currency": "eur",
                            "product_data": {
                                "name": title,
                                "description": "Bracciale artigianale in puro rame 99.9% forgiato a mano Fatto a Mano",
                                "images": images,
                            },
                            "unit_amount": price_cents,
                        },
                        "quantity": int(it.get("quantity", 1)),
                    })

                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=line_items,
                    mode="payment",
                    success_url=success_url,
                    cancel_url=cancel_url,
                )

                self.send_json(200, {
                    "id": session.id,
                    "url": session.url
                })
                return
            except Exception as e:
                # Prova fallback HTTP diretto se la libreria lancia un'eccezione
                pass

        # Tentativo 2: Chiamata REST diretta a api.stripe.com (Zero dipendenze)
        try:
            form_payload = [
                ("payment_method_types[]", "card"),
                ("mode", "payment"),
                ("success_url", success_url),
                ("cancel_url", cancel_url),
            ]
            for idx, it in enumerate(items):
                price_val = float(it.get("price", 30))
                price_cents = int(price_val * 100)
                title = it.get("title", "Bracciale in Puro Rame 99.9%")
                img_url = it.get("image_url", "")

                form_payload.append((f"line_items[{idx}][quantity]", str(int(it.get("quantity", 1)))))
                form_payload.append((f"line_items[{idx}][price_data][currency]", "eur"))
                form_payload.append((f"line_items[{idx}][price_data][unit_amount]", str(price_cents)))
                form_payload.append((f"line_items[{idx}][price_data][product_data][name]", title))
                form_payload.append((f"line_items[{idx}][price_data][product_data][description]", "Bracciale artigianale in puro rame 99.9%"))
                if img_url.startswith("http://") or img_url.startswith("https://"):
                    form_payload.append((f"line_items[{idx}][price_data][product_data][images][0]", img_url))

            encoded_data = urllib.parse.urlencode(form_payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.stripe.com/v1/checkout/sessions",
                data=encoded_data,
                headers={
                    "Authorization": f"Bearer {stripe_key}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                res_body = json.loads(res.read().decode("utf-8"))
                self.send_json(200, {
                    "id": res_body.get("id"),
                    "url": res_body.get("url")
                })
                return
        except urllib.error.HTTPError as he:
            err_msg = he.read().decode("utf-8")
            self.send_json(he.code, {"error": f"Errore Stripe: {err_msg}"})
        except Exception as e:
            self.send_json(500, {"error": f"Impossibile creare sessione Stripe: {str(e)}"})

    def send_json(self, status_code, data_dict):
        payload = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)
