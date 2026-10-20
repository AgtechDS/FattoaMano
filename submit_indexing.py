#!/usr/bin/env python3
"""
==============================================================================
FATTO A MANO — MOTORE DI INVIO INDICIZZAZIONE (GOOGLE & INDEXNOW/BING)
==============================================================================
Invia i ping di indicizzazione istantanea per:
  1. Google Search Engine (Sitemap Ping)
  2. Microsoft Bing (Sitemap Ping)
  3. Protocollo IndexNow (Bing, Yandex, Seznam, Naver & AI Crawlers)
==============================================================================
"""

import json
import ssl
import sys
import urllib.request
import urllib.error

DOMAIN = "https://agtechdesigne.shop"
SITEMAP_URL = f"{DOMAIN}/sitemap.xml"
INDEXNOW_KEY = "a8f9c1e2d4b56789a1b2c3d4e5f67890"

URLS_TO_INDEX = [
    f"{DOMAIN}/",
    f"{DOMAIN}/index.html",
    f"{DOMAIN}/atelier-pietre.html"
]

def ping_google_sitemap():
    print("\n[1/3] Invio Ping Sitemap a Google Search...")
    url = f"https://www.google.com/ping?sitemap={SITEMAP_URL}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            print(f"  -> Google Ping completato: HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  -> Google Ping risposta: HTTP {e.code} ({e.reason})")
        return e.code in (200, 204, 404) # 404 can occur as Google deprecated public ping endpoint in favor of Search Console API
    except Exception as e:
        print(f"  -> Avviso Google Ping: {e}")
        return False

def ping_bing_sitemap():
    print("\n[2/3] Invio Ping Sitemap a Microsoft Bing...")
    url = f"https://www.bing.com/ping?sitemap={SITEMAP_URL}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            print(f"  -> Bing Ping completato: HTTP {resp.status}")
            return True
    except Exception as e:
        print(f"  -> Avviso Bing Ping: {e}")
        return False

def submit_indexnow():
    print("\n[3/3] Invio Richiesta Indicizzazione Istantanea via IndexNow (Bing & AI Engines)...")
    payload = {
        "host": "agtechdesigne.shop",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{DOMAIN}/{INDEXNOW_KEY}.txt",
        "urlList": URLS_TO_INDEX
    }
    data = json.dumps(payload).encode("utf-8")
    endpoints = [
        "https://api.indexnow.org/indexnow",
        "https://www.bing.com/indexnow"
    ]
    ctx = ssl.create_default_context()
    for ep in endpoints:
        try:
            req = urllib.request.Request(
                ep,
                data=data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            )
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                print(f"  -> {ep}: HTTP {resp.status} (Accettato)")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            print(f"  -> {ep}: HTTP {he.code} ({err_body.strip() or he.reason})")
        except Exception as e:
            print(f"  -> {ep}: Avviso ({e})")

def main():
    print("=" * 65)
    print("  FATTO A MANO — SISTEMA DI INDICIZZAZIONE MOTORI DI RICERCA")
    print("=" * 65)
    print(f"Dominio: {DOMAIN}")
    print(f"Sitemap: {SITEMAP_URL}")
    print(f"Pagine da indicizzare ({len(URLS_TO_INDEX)}):")
    for u in URLS_TO_INDEX:
        print(f"  • {u}")
    print("-" * 65)

    ping_google_sitemap()
    ping_bing_sitemap()
    submit_indexnow()

    print("\n" + "=" * 65)
    print("  PROCEDURA DI INDICIZZAZIONE COMPLETATA")
    print("=" * 65)

if __name__ == "__main__":
    main()
