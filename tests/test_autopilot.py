"""Tests du pilote automatique (avec données simulées, sans réseau)."""

import numpy as np
import pandas as pd
import pytest

from core import autopilot as ap_module
from core.autopilot import Autopilot


@pytest.fixture
def fake_market(monkeypatch):
    """Remplace fetch_ohlcv par des données synthétiques (aucun réseau)."""
    rng = np.random.default_rng(3)
    n = 150
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="D"),
        "open": close, "high": close + 1, "low": close - 1,
        "close": close, "volume": 1000.0,
    })
    monkeypatch.setattr(ap_module, "fetch_ohlcv", lambda *a, **k: df.copy())
    return df


def test_premier_pas_ingere_l_historique(tmp_path, fake_market):
    bot = Autopilot.load(state_path=tmp_path / "state.json", initial_capital=1000)
    rapport = bot.step()
    assert rapport["bougies_traitees"] > 0
    assert len(bot.state.history) > 0
    # L'état est bien sauvegardé sur le disque.
    assert (tmp_path / "state.json").exists()


def test_deuxieme_pas_sans_nouvelles_bougies(tmp_path, fake_market):
    bot = Autopilot.load(state_path=tmp_path / "state.json", initial_capital=1000)
    bot.step()
    n_hist = len(bot.state.history)
    rapport2 = bot.step()  # mêmes données -> aucune nouvelle bougie
    assert rapport2["bougies_traitees"] == 0
    assert len(bot.state.history) == n_hist


def test_etat_persiste_entre_deux_chargements(tmp_path, fake_market):
    chemin = tmp_path / "state.json"
    bot = Autopilot.load(state_path=chemin, initial_capital=1000)
    bot.step()
    valeur = bot.status()["valeur_actuelle"]

    # On recharge depuis le disque : l'état doit être identique.
    bot2 = Autopilot.load(state_path=chemin)
    assert bot2.status()["valeur_actuelle"] == pytest.approx(valeur)
    assert len(bot2.state.history) == len(bot.state.history)


def test_reset_efface_l_historique(tmp_path, fake_market):
    bot = Autopilot.load(state_path=tmp_path / "state.json", initial_capital=1000)
    bot.step()
    assert len(bot.state.history) > 0
    bot.reset()
    assert bot.state.history == []
    assert bot.state.cash == 1000
