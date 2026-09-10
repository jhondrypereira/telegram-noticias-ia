# -*- coding: utf-8 -*-
# Fuentes RSS. Puedes agregar/quitar libremente (nombre, url, etiqueta).
# Todas son de portales reconocidos y traen titular + resumen + enlace (y muchas veces imagen).

FEEDS = [
    # ----- IA / INTELIGENCIA ARTIFICIAL -----
    {"name": "TechCrunch IA",     "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tag": "#IA"},
    {"name": "VentureBeat IA",    "url": "https://venturebeat.com/category/ai/feed/",                     "tag": "#IA"},
    {"name": "MIT Tech Review",   "url": "https://www.technologyreview.com/feed/",                        "tag": "#IA"},
    {"name": "Hugging Face",      "url": "https://huggingface.co/blog/feed.xml",                          "tag": "#IA"},
    {"name": "Google News IA",    "url": "https://news.google.com/rss/search?q=inteligencia+artificial+when:1d&hl=es-419&gl=US&ceid=US:es-419", "tag": "#IA"},

    # ----- TECNOLOGÍA / AVANCES -----
    {"name": "The Verge",         "url": "https://www.theverge.com/rss/index.xml",                        "tag": "#Tecnologia"},
    {"name": "Ars Technica",      "url": "https://feeds.arstechnica.com/arstechnica/index",               "tag": "#Tecnologia"},
    {"name": "Wired",             "url": "https://www.wired.com/feed/rss",                                "tag": "#Tecnologia"},
    {"name": "Xataka",            "url": "https://feeds.weblogssl.com/xataka2",                           "tag": "#Tecnologia"},
    {"name": "Hipertextual",      "url": "https://hipertextual.com/feed",                                 "tag": "#Tecnologia"},
    {"name": "Google News Avances","url": "https://news.google.com/rss/search?q=avance+tecnologico+OR+innovacion+when:1d&hl=es-419&gl=US&ceid=US:es-419", "tag": "#Tecnologia"},

    # ----- BUENAS NOTICIAS DEL MUNDO -----
    {"name": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/",                         "tag": "#BuenasNoticias"},
    {"name": "Positive News",     "url": "https://www.positive.news/feed/",                               "tag": "#BuenasNoticias"},
]

# Si un titular contiene alguna de estas palabras, NO se publica (mantiene el canal positivo y limpio).
BLOCK = [
    "muerto", "muerte", "muere", "asesinat", "homicidio", "guerra", "violaci", "abuso",
    "terror", "atentado", "tiroteo", "masacre", "suicid", "secuestr", "narco", "femicid",
    "death", "died", "dead", "killed", "kill ", "war ", "shooting", "murder", "rape", "terror",
]

# (Opcional) Solo publica items cuyo titular/resumen mencione algo de esto.
# Deja la lista VACÍA [] para publicar todo lo que traigan las fuentes de arriba.
REQUIRE_ANY = []  # ej: ["ia", "inteligencia artificial", "tecnolog", "ai ", "robot", "chip", "app"]
