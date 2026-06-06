"""Tests du parseur RSS des actualités (hors-ligne, déterministe)."""

from core import news

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Flux test</title>
  <item>
    <title>Le Bitcoin franchit un cap</title>
    <link>https://exemple.test/btc</link>
    <pubDate>Mon, 06 Jun 2026 09:00:00 GMT</pubDate>
    <source url="https://journal.test">Le Journal</source>
  </item>
  <item>
    <title>Ethereum met a jour son reseau</title>
    <link>https://exemple.test/eth</link>
  </item>
  <item>
    <title></title>
    <link></link>
  </item>
</channel></rss>"""


def test_parse_rss_extrait_les_articles():
    items = news.parse_rss(SAMPLE_RSS, source_default="Defaut")
    # le 3e item (titre/lien vides) est ignoré
    assert len(items) == 2
    assert items[0]["title"] == "Le Bitcoin franchit un cap"
    assert items[0]["link"].startswith("https://")


def test_parse_rss_source_explicite_et_defaut():
    items = news.parse_rss(SAMPLE_RSS, source_default="Defaut")
    assert items[0]["source"] == "Le Journal"      # balise <source>
    assert items[1]["source"] == "Defaut"          # repli sur le défaut


def test_parse_rss_vide():
    assert news.parse_rss(b"<rss><channel></channel></rss>") == []
