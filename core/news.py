"""
Actualités crypto en direct (les « journaux »).

100 % bibliothèque standard : on lit des flux **RSS** publics (pas de clé, pas de
dépendance) avec urllib, et on les parse avec xml.etree. Source principale :
Google Actualités en français (agrège de nombreux journaux), avec repli sur
Cointelegraph. Résilient : si le réseau échoue, on renvoie une liste vide et
l'interface l'indique proprement.
"""

from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET

# (nom par défaut, URL du flux). Google Actualités agrège la presse FR.
FEEDS: tuple[tuple[str, str], ...] = (
    ("Google Actualités",
     "https://news.google.com/rss/search?q=crypto+OR+bitcoin+OR+ethereum&hl=fr&gl=FR&ceid=FR:fr"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TradingAssistant/1.0)"}


def _fetch_url(url: str, timeout: int = 6) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL maîtrisée)
        return resp.read()


def parse_rss(xml_bytes: bytes, source_default: str = "") -> list[dict]:
    """Extrait les articles d'un flux RSS. Pur (testable hors-ligne)."""
    items: list[dict] = []
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None and src_el.text else source_default
        if title and link:
            items.append({"title": title, "link": link, "source": source, "date": pub})
    return items


def _enrich_assets(items: list[dict]) -> None:
    """Ajoute item['assets'] = symboles détectés dans le titre (import local pour
    éviter tout couplage à l'import)."""
    try:
        from core.assistant import detect_assets
    except Exception:
        return
    for it in items:
        it["assets"] = detect_assets(it.get("title", ""))


def latest_news(limit: int = 12) -> list[dict]:
    """Renvoie les derniers articles (en essayant les flux dans l'ordre), chacun
    enrichi des actifs mentionnés. Liste vide si tout échoue."""
    for source_default, url in FEEDS:
        try:
            data = _fetch_url(url)
            items = parse_rss(data, source_default)
            if items:
                items = items[:limit]
                _enrich_assets(items)
                return items
        except Exception:
            continue
    return []
