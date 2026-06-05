"""Tests des calculs de portefeuille et de la logique d'alertes (purs)."""

import pytest

from core import alerts, portfolio


# --- Portefeuille ---

def test_evaluate_calcule_valeur_et_pnl():
    holdings = [
        {"symbol": "BTC/USDT", "quantity": 2, "buy_price": 100},   # coût 200
        {"symbol": "ETH/USDT", "quantity": 10, "buy_price": 10},   # coût 100
    ]
    prices = {"BTC/USDT": 150, "ETH/USDT": 8}
    res = portfolio.evaluate(holdings, prices)
    assert res["total_cost"] == pytest.approx(300)
    assert res["total_value"] == pytest.approx(2 * 150 + 10 * 8)   # 300 + 80 = 380
    assert res["total_pnl"] == pytest.approx(80)
    btc = res["rows"][0]
    assert btc["pnl"] == pytest.approx(100)           # 300 - 200
    assert btc["pnl_pct"] == pytest.approx(50)


def test_evaluate_prix_manquant():
    holdings = [{"symbol": "DOGE/USDT", "quantity": 5, "buy_price": 1}]
    res = portfolio.evaluate(holdings, prices={})
    assert res["rows"][0]["value"] is None
    assert res["total_cost"] == pytest.approx(5)      # coût compté même sans prix
    assert res["total_value"] == pytest.approx(0)


def test_evaluate_portefeuille_vide():
    res = portfolio.evaluate([], {})
    assert res["total_value"] == 0 and res["total_pnl_pct"] == 0


# --- Alertes ---

def test_alertes_declenchement():
    assert alerts.is_triggered("price_above", 100, price=120, rsi=50) is True
    assert alerts.is_triggered("price_above", 100, price=90, rsi=50) is False
    assert alerts.is_triggered("price_below", 100, price=90, rsi=50) is True
    assert alerts.is_triggered("rsi_above", 70, price=0, rsi=75) is True
    assert alerts.is_triggered("rsi_below", 30, price=0, rsi=20) is True
    assert alerts.is_triggered("rsi_below", 30, price=0, rsi=40) is False


def test_alerte_type_inconnu():
    with pytest.raises(ValueError):
        alerts.is_triggered("ouragan", 1, 1, 1)


def test_alerte_describe():
    assert alerts.describe("BTC/USDT", "price_above", 70000) == "BTC/USDT — Prix ≥ 70000"
