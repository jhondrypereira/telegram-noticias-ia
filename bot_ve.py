# -*- coding: utf-8 -*-
"""
Canal de NOTICIAS DE VENEZUELA, 100% automático.
- Lee RSS de medios venezolanos.
- Arma un RESUMEN más largo (primeros párrafos del artículo), SIN enlace a la fuente.
- Publica con imagen (o solo texto). Ya viene en español (no traduce).
Estado en posted_ve.json (no repite).
"""
import os, re, json, time, html, sys, random
import requests
import feedparser
from datetime import datetime, timezone
from feeds_ve import FEEDS, BLOCK, REQUIRE_ANY

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

STATE_FILE   = "posted_ve.json"
MAX_PER_RUN  = int(os.environ.get("MAX_PER_RUN", "5"))
KEEP_HISTORY = 3000
SUMMARY_MAX  = 700         # largo del resumen (caracteres)
UA = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            ids = json.load(f).get("ids", [])
            return ids, set(ids)
    except Exception:
        return [], set()


def save_state(ids):
    ids = ids[-KEEP_HISTORY:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": ids, "updated": datetime.now(timezone.utc).isoformat()}, f, ensure_ascii=False, indent=0)


def strip_html(text):
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def entry_id(e):
    return (getattr(e, "id", None) or getattr(e, "link", "") or getattr(e, "title", "")).strip()


def article_paragraphs(url):
    """Baja el artículo y saca los párrafos de texto (para el resumen)."""
    try:
        r = requests.get(url, headers=UA, timeout=12)
        htmltext = r.text
    except Exception:
        return []
    # descartar bloques de script/estilo
    htmltext = re.sub(r"(?is)<(script|style|nav|footer|aside)[^>]*>.*?</\1>", " ", htmltext)
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", htmltext)
    out = []
    for p in paras:
        t = strip_html(p)
        # descarta párrafos cortos o típicos de pie/legales
        low = t.lower()
        if len(t) < 60:
            continue
        if any(x in low for x in ("cookie", "suscríb", "lea también", "lea tambien", "copyright",
                                  "todos los derechos", "foto:", "leer más", "©", "compart")):
            continue
        out.append(t)
        if len(" ".join(out)) > 1200:
            break
    return out


def make_summary(e):
    # 1) el CONTENIDO del propio RSS (limpio y ya en español)
    cont = e.content[0].value if getattr(e, "content", None) else ""
    summ = getattr(e, "summary", "") or getattr(e, "description", "")
    src = cont if len(strip_html(cont)) >= len(strip_html(summ)) else summ
    text = strip_html(src)
    # 2) respaldo: raspar los párrafos del artículo
    if len(text) < 120:
        paras = article_paragraphs(e.link)
        if paras:
            text = " ".join(paras).strip()
    if not text:
        return ""
    # limpiar coletillas típicas de WordPress y datos de contacto
    text = re.sub(r'(?is)\bLa entrada\b.*', '', text)
    text = re.sub(r'(?is)\bThe post\b.*?appeared first on.*', '', text)
    text = re.sub(r'(?is)\b(lea tambi[eé]n|leer m[aá]s|tambi[eé]n le puede interesar|con informaci[oó]n de)\b.*', '', text)
    text = re.sub(r'(?i)\bcorreo:\s*', '', text)
    text = re.sub(r'\S+@\S+\.\S+', '', text)      # emails sueltos
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ""
    # recorta a un resumen limpio, cerrando en punto
    if len(text) > SUMMARY_MAX:
        cut = text[:SUMMARY_MAX]
        dot = cut.rfind(". ")
        text = (cut[:dot+1] if dot > SUMMARY_MAX*0.5 else cut.rsplit(" ", 1)[0] + "…")
    return text


def get_image(e):
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
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', getattr(e, "summary", "") or "")
    if m and m.group(1).startswith("http"):
        return m.group(1)
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


def build_text(title, summary, tag):
    title = html.escape(title.strip())
    body = f"<b>{title}</b>"
    if summary:
        body += f"\n\n{html.escape(summary)}"
    body += f"\n\n{tag}"
    return body


def send_photo(photo, caption):
    # caption de sendPhoto = 1024 chars máx
    if len(caption) > 1024:
        caption = caption[:1000].rsplit(" ", 1)[0] + "…"
    r = requests.post(f"{API}/sendPhoto", data={"chat_id": CHANNEL_ID, "photo": photo,
                      "caption": caption, "parse_mode": "HTML"}, timeout=30)
    return r.ok and r.json().get("ok")


def send_message(text):
    r = requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL_ID, "text": text[:4096],
                      "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=30)
    return r.ok and r.json().get("ok")


def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: faltan BOT_TOKEN o CHANNEL_ID"); sys.exit(1)
    order, seen = load_state()
    cands = []
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
            if not title:
                continue
            if is_blocked(title, strip_html(getattr(e, "summary", ""))):
                seen.add(eid); order.append(eid); continue
            cands.append((feed, e, eid, title))

    # variedad: intercala fuentes
    by_feed = {}
    for c in cands:
        by_feed.setdefault(c[0]["name"], []).append(c)
    for arr in by_feed.values():
        random.shuffle(arr)
    mixed, groups = [], list(by_feed.values())
    while groups:
        for arr in groups:
            mixed.append(arr.pop(0))
        groups = [a for a in groups if a]
    cands = mixed

    print(f"{len(cands)} noticias nuevas")
    posted = 0
    for feed, e, eid, title in cands:
        if posted >= MAX_PER_RUN:
            break
        summary = make_summary(e)
        text = build_text(title, summary, feed["tag"])
        img = get_image(e)
        ok = send_photo(img, text) if img else False
        if not ok:
            ok = send_message(text)
        if ok:
            posted += 1; seen.add(eid); order.append(eid)
            print("publicado:", title[:70]); time.sleep(4)
        else:
            print("fallo:", title[:70])
    save_state(order)
    print(f"listo: {posted} publicadas")


if __name__ == "__main__":
    main()
