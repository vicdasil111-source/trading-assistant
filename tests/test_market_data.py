"""Tests de la récupération de données : repli sur les exemples embarqués."""

import pandas as pd
import pytest

from core import market_data


def test_repli_sur_exemple_quand_reseau_indisponible(monkeypatch):
    """Si ccxt échoue, on doit se rabattre sur les données d'exemple versionnées."""
    import ccxt

    def boom(*a, **k):
        raise RuntimeError("réseau coupé (simulé)")

    monkeypatch.setattr(ccxt, "binance", boom)

    # use_cache=False : on ignore tout cache local pour tester vraiment l'exemple.
    df = market_data.fetch_ohlcv("BTC/USDT", "1d", use_cache=False)
    assert not df.empty
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_erreur_claire_si_aucune_source(monkeypatch):
    """Sans réseau, sans cache et sans exemple : erreur explicite."""
    import ccxt

    monkeypatch.setattr(ccxt, "binance", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ko")))
    with pytest.raises(RuntimeError):
        market_data.fetch_ohlcv("DOGE/USDT", "1d", use_cache=False)


def test_sample_path_format():
    p = market_data._sample_path("BTC/USDT", "1d")
    assert p.name == "BTC-USDT_1d.csv"
    assert p.parent.name == "samples"
