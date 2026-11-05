#!/usr/bin/env python3
"""Monitora t.me/s/prodigeekOfferte e avvisa via bot Telegram
quando compare un post che contiene "aubox" o "chuwi".

Setup:
  pip install requests beautifulsoup4
  1. Crea il bot con @BotFather e copia il token.
  2. Scrivi /start al tuo bot, poi apri
     https://api.telegram.org/bot<TOKEN>/getUpdates e copia il chat id.
  3. Imposta le variabili d'ambiente TG_TOKEN e TG_CHAT_ID.
  4. Lancialo ogni 5 minuti (cron, oppure su Termux:
     while true; do python prodigeek_watch.py; sleep 300; done)
"""
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CHANNEL_URL = "https://t.me/s/prodigeekOfferte"
KEYWORDS = ["aubox", "chuwi"]   # basta che ne compaia una
MIN_RAM_GB = 16
MIN_SSD_GB = 512
MAX_PRICE = 250.0

TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]
SEEN_FILE = Path(__file__).with_name("seen_posts.json")


def parse_price(text):
    m = re.search(r"Prezzo:\s*([\d.,]+)\s*€", text)
    if not m:
        return None
    raw = m.group(1)
    if "," in raw:                      # formato 1.236,32
        raw = raw.replace(".", "").replace(",", ".")
    return float(raw)


def parse_ram(text):
    m = re.search(r"(\d+)\s*GB\s*RAM", text, re.I)
    return int(m.group(1)) if m else None


def parse_ssd(text):
    m = re.search(r"(\d+)\s*(GB|TB)\s*SSD", text, re.I)
    if not m:
        return None
    size = int(m.group(1))
    return size * 1000 if m.group(2).upper() == "TB" else size


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=20,
    ).raise_for_status()


def main():
    seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

    html = requests.get(
        CHANNEL_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
    ).text
    soup = BeautifulSoup(html, "html.parser")

    for msg in soup.select("div.tgme_widget_message"):
        post_id = msg.get("data-post")
        text_el = msg.select_one(".tgme_widget_message_text")
        if not post_id or not text_el or post_id in seen:
            continue
        seen.add(post_id)

        text = text_el.get_text("\n")
        low = text.lower()
        if not any(k in low for k in KEYWORDS):
            continue

        send(f"{text[:600]}\n\nhttps://t.me/{post_id}")

    SEEN_FILE.write_text(json.dumps(sorted(seen)))


if __name__ == "__main__":
    main()
