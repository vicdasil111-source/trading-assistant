"""Tests du module d'exécution testnet (garde-fous, sans réseau)."""

import pytest

from core import execution


def test_dry_run_n_envoie_rien():
    ordre = execution.place_market_order("BTC/USDT", "buy", 0.01)  # dry_run=True par défaut
    assert ordre["dry_run"] is True
    assert ordre["status"] == "simulé"
    assert ordre["side"] == "buy"


def test_side_invalide_leve_erreur():
    with pytest.raises(ValueError):
        execution.place_market_order("BTC/USDT", "hold", 0.01)


def test_ordre_reel_refuse_sans_acceptation_du_risque(monkeypatch):
    # Sans I_UNDERSTAND_REAL_MONEY_RISK=yes, l'ordre réel est refusé.
    monkeypatch.delenv("I_UNDERSTAND_REAL_MONEY_RISK", raising=False)
    with pytest.raises(RuntimeError):
        execution.place_market_order("BTC/USDT", "buy", 0.01, testnet=False, dry_run=False)


def test_cles_manquantes_levent_une_erreur_claire(monkeypatch):
    monkeypatch.delenv("BINANCE_TESTNET_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_TESTNET_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        execution.get_exchange(testnet=True)
