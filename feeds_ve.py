# -*- coding: utf-8 -*-
# Fuentes RSS de noticias de VENEZUELA (medios reconocidos + Google News).
FEEDS = [
    {"name": "Efecto Cocuyo",  "url": "https://efectococuyo.com/feed/",     "tag": "#Venezuela"},
    {"name": "Tal Cual",       "url": "https://talcualdigital.com/feed/",   "tag": "#Venezuela"},
    {"name": "Runrun.es",      "url": "https://runrun.es/feed/",            "tag": "#Venezuela"},
    {"name": "El Nacional",    "url": "https://www.elnacional.com/feed/",   "tag": "#Venezuela"},
    {"name": "El Pitazo",      "url": "https://elpitazo.net/feed/",         "tag": "#Venezuela"},
    {"name": "Descifrado",     "url": "https://www.descifrado.com/feed/",   "tag": "#Venezuela"},
]

# No se publica si el titular contiene esto (ajústalo a tu gusto).
BLOCK = []

# Solo publica si menciona algo de esto (vacío = todo lo de las fuentes de arriba).
REQUIRE_ANY = []
