"""Tests du parseur Fear & Greed (hors-ligne, déterministe)."""

from core import sentiment

SAMPLE = (b'{"name":"Fear and Greed Index","data":['
          b'{"value":"40","value_classification":"Fear","timestamp":"1"}],'
          b'"metadata":{"error":null}}')


def test_parse_fng_valeur_et_label():
    r = sentiment.parse_fng(SAMPLE)
    assert r["value"] == 40
    assert r["label"] == "Fear"
    assert r["label_fr"] == "Peur"


def test_parse_fng_traduction_extreme():
    r = sentiment.parse_fng({"data": [{"value": "88", "value_classification": "Extreme Greed"}]})
    assert r["value"] == 88
    assert r["label_fr"] == "Avidité extrême"


def test_parse_fng_donnees_vides():
    r = sentiment.parse_fng({"data": []})
    assert r["value"] == 0
