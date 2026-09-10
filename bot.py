# -*- coding: utf-8 -*-
"""
Publica noticias (IA, tecnología y buenas noticias) en un canal de Telegram, 100% automático.
- Lee RSS de portales reconocidos.
- Filtra repetidos, negativos y (opcional) por palabras clave.
- Traduce titular + resumen al ESPAÑOL, con el enlace al artículo ORIGINAL.
- Publica con imagen (sendPhoto) o solo texto si no hay imagen.
El estado (lo ya publicado) se guarda en posted.json para no repetir.
"""
import os, re, json, time, html, sys
import requests
import feedparser
from datetime import datetime, timezone

try:
    from deep_translator import GoogleTranslator
    HAS_TR = True
except Exception:
    HAS_TR = False

from feeds import FEEDS, BLOCK, REQUIRE_ANY

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

STATE_FILE   = "posted.json"
MAX_PER_RUN  = int(os.environ.get("MAX_PER_RUN", "6"))   # cuántas noticias por ejecución
KEEP_HISTORY = 3000                                       # cuántos IDs recordar (anti-repetidos)
UA = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            d = json.load(f)
            return d.get("ids", []), set(d.get("ids", []))
    except Exception:
        return [], set()


def save_state(ids):
    ids = ids[-KEEP_HISTORY:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": ids, "updated": datetime.now(timezone.utc).isoformat()}, f, ensure_ascii=False, indent=0)


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def translate(text):
    if not text or not HAS_TR:
        return text
    try:
        # GoogleTranslator limita a 5000 chars por llamada; nuestros textos son cortos
        return GoogleTranslator(source="auto", target="es").translate(text[:1200])
    except Exception:
        return text


def entry_id(e):
    return (getattr(e, "id", None) or getattr(e, "link", "") or getattr(e, "title", "")).strip()


def get_image(e):
    # 1) media:content / media:thumbnail / enclosure del propio RSS
    for key in ("media_content", "media_thumbnail"):
        arr = getattr(e, key, None)
        if arr:
            for m in arr:
                u = m.get("url")
                if u and u.startswith("http"):
                    return u
    for enc in getattr(e, "enclosures", []) or []:
        u = enc.get("href") or enc.get("url")
        if u and u.startswith("http") and "image" in (enc.get("type") or "image"):
            return u
    for l in getattr(e, "links", []) or []:
        if l.get("rel") == "enclosure" and "image" in (l.get("type") or ""):
            return l.get("href")
    # 2) buscar una <img> dentro del resumen
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', getattr(e, "summary", "") or "")
    if m and m.group(1).startswith("http"):
        return m.group(1)
    # 3) og:image del artículo (último recurso)
    try:
        r = requests.get(e.link, headers=UA, timeout=12)
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', r.text, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', r.text, re.I)
        if m:
            u = html.unescape(m.group(1))
            if u.startswith("http"):
                return u
    except Exception:
        pass
    return None


def is_blocked(title, summary):
    t = (title + " " + summary).lower()
    if any(b in t for b in BLOCK):
        return True
    if REQUIRE_ANY and not any(k in t for k in REQUIRE_ANY):
        return True
    return False


def build_caption(title_es, summary_es, source, tag, link):
    title_es = html.escape(title_es)
    summary_es = html.escape(summary_es)
    base = f"<b>{title_es}</b>"
    if summary_es:
        base += f"\n\n{summary_es}"
    footer = f"\n\n{tag} · 📰 <a href=\"{html.escape(link)}\">{html.escape(source)}</a>"
    # límite de caption de Telegram = 1024 chars
    room = 1024 - len(footer) - 4
    if len(base) > room:
        base = base[:room].rsplit(" ", 1)[0] + "…"
    return base + footer


def send_photo(photo, caption):
    r = requests.post(f"{API}/sendPhoto", data={
        "chat_id": CHANNEL_ID, "photo": photo, "caption": caption,
        "parse_mode": "HTML"}, timeout=30)
    return r.ok and r.json().get("ok")


def send_message(text):
    # texto sin imagen: dejamos que Telegram muestre la vista previa del enlace
    r = requests.post(f"{API}/sendMessage", data={
        "chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": False}, timeout=30)
    return r.ok and r.json().get("ok")


def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: faltan BOT_TOKEN o CHANNEL_ID"); sys.exit(1)

    order, seen = load_state()
    candidates = []

    for feed in FEEDS:
        try:
            d = feedparser.parse(feed["url"], request_headers=UA)
        except Exception as ex:
            print("feed error", feed["name"], ex); continue
        for e in d.entries[:12]:
            eid = entry_id(e)
            if not eid or eid in seen:
                continue
            title = strip_html(getattr(e, "title", ""))
            summary = strip_html(getattr(e, "summary", ""))[:280]
            if not title:
                continue
            if is_blocked(title, summary):
                seen.add(eid); order.append(eid)  # lo marcamos para no re-evaluarlo
                continue
            candidates.append((feed, e, eid, title, summary))

    print(f"{len(candidates)} noticias nuevas encontradas")
    posted = 0
    for feed, e, eid, title, summary in candidates:
        if posted >= MAX_PER_RUN:
            break
        title_es = translate(title)
        summary_es = translate(summary) if summary else ""
        caption = build_caption(title_es, summary_es, feed["name"], feed["tag"], e.link)
        img = get_image(e)
        ok = False
        if img:
            ok = send_photo(img, caption)
        if not ok:
            ok = send_message(caption)
        if ok:
            posted += 1
            seen.add(eid); order.append(eid)
            print("publicado:", title_es[:70])
            time.sleep(4)  # respeta los límites de Telegram
        else:
            print("fallo al publicar:", title[:70])

    save_state(order)
    print(f"listo: {posted} publicadas")


if __name__ == "__main__":
    main()
