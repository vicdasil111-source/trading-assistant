"""Tests de la gestion du risque et du portefeuille fictif (paper trading)."""

import pytest

from core.paper_trading import PaperPortfolio
from core.risk import position_size, risk_reward_ratio


# --- Gestion du risque ---

def test_risk_reward_ratio():
    # Entrée 100, stop 90 (risque 10), cible 130 (récompense 30) -> ratio 3.
    assert risk_reward_ratio(entry=100, stop=90, target=130) == pytest.approx(3.0)


def test_risk_reward_ratio_stop_egal_entree():
    with pytest.raises(ValueError):
        risk_reward_ratio(entry=100, stop=100, target=130)


def test_position_size():
    # 1000 de capital, 1 % de risque = 10 risqués ; perte/unité = 10 -> 1 unité.
    assert position_size(capital=1000, risk_pct=1, entry=100, stop=90) == pytest.approx(1.0)


def test_position_size_stop_egal_entree():
    with pytest.raises(ValueError):
        position_size(capital=1000, risk_pct=1, entry=100, stop=100)


# --- Paper trading ---

def test_paper_trade_gagnant():
    pf = PaperPortfolio(initial_capital=100)
    pf.on_bar(price=10, signal=1)   # achat à 10
    pf.on_bar(price=20, signal=-1)  # vente à 20
    s = pf.summary()
    assert s["valeur_actuelle"] == pytest.approx(200.0)
    assert s["rendement_pct"] == pytest.approx(100.0)
    assert s["nombre_trades"] == 1
    assert s["taux_reussite_pct"] == pytest.approx(100.0)
    assert s["en_position"] is False


def test_paper_reste_en_position_sans_signal_de_vente():
    pf = PaperPortfolio(initial_capital=100)
    pf.on_bar(price=10, signal=1)
    pf.on_bar(price=15, signal=0)
    assert pf.in_position is True
    # Équité = 10 unités * 15 = 150 (non réalisé).
    assert pf.equity() == pytest.approx(150.0)


def test_paper_ignore_double_achat():
    pf = PaperPortfolio(initial_capital=100)
    pf.on_bar(price=10, signal=1)
    units_apres_premier_achat = pf.units
    pf.on_bar(price=12, signal=1)  # déjà en position -> ignoré
    assert pf.units == pytest.approx(units_apres_premier_achat)
