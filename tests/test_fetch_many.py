"""Tests du chargement parallèle des données de marché (fetch_many).

Hors-ligne, fetch_ohlcv se rabat sur les données d'exemple embarquées
(data/samples/) pour BTC et ETH : les tests restent donc déterministes.
"""

from core.market_data import fetch_many


def test_fetch_many_renvoie_les_symboles_disponibles():
    data = fetch_many(["BTC/USDT", "ETH/USDT"], "1d", limit=30)
    assert "BTC/USDT" in data
    assert "ETH/USDT" in data
    assert not data["BTC/USDT"].empty


def test_fetch_many_ignore_les_symboles_invalides():
    data = fetch_many(["BTC/USDT", "PASUNVRAISYMBOLE/USDT"], "1d", limit=10)
    assert "BTC/USDT" in data
    assert "PASUNVRAISYMBOLE/USDT" not in data


def test_fetch_many_liste_vide():
    assert fetch_many([], "1d") == {}
