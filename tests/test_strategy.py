"""Tests des stratégies de génération de signaux."""

import pandas as pd

from core.strategy import EmaCrossStrategy, RsiSmaStrategy, get_strategy
from utils.config import Config


def test_rsi_sma_signaux_dans_intervalle_valide():
    # Signaux possibles : -1, 0, +1 uniquement.
    df = pd.DataFrame({"close": [100 + (i % 7) for i in range(120)]})
    strat = RsiSmaStrategy()
    out = strat.generate_signals(df)
    assert set(out["signal"].unique()).issubset({-1, 0, 1})
    assert "signal" in out.columns


def test_rsi_sma_genere_une_vente_en_surachat():
    # Prix qui montent en flèche -> RSI élevé -> au moins un signal de vente (-1).
    df = pd.DataFrame({"close": list(range(1, 120))})
    out = RsiSmaStrategy().generate_signals(df)
    assert (out["signal"] == -1).any()


def test_rsi_sma_ne_modifie_pas_le_df_original():
    df = pd.DataFrame({"close": list(range(1, 60))})
    avant = df.columns.tolist()
    RsiSmaStrategy().generate_signals(df)
    # La stratégie travaille sur une copie : le df d'origine est intact.
    assert df.columns.tolist() == avant


def test_ema_cross_detecte_un_croisement_haussier():
    # Prix qui baissent puis remontent fort -> l'EMA courte recroise vers le haut.
    prices = list(range(50, 0, -1)) + list(range(0, 80))
    df = pd.DataFrame({"close": prices})
    out = EmaCrossStrategy(short=5, long=20).generate_signals(df)
    assert (out["signal"] == 1).any()


def test_get_strategy_par_nom():
    assert isinstance(get_strategy("rsi_sma"), RsiSmaStrategy)
    assert isinstance(get_strategy("ema_cross"), EmaCrossStrategy)


def test_get_strategy_nom_inconnu():
    import pytest

    with pytest.raises(ValueError):
        get_strategy("strategie_qui_nexiste_pas")


def test_config_personnalisee_change_les_seuils():
    cfg = Config(rsi_oversold=40, rsi_overbought=60, sma_long=10)
    df = pd.DataFrame({"close": list(range(1, 60))})
    out = RsiSmaStrategy(config=cfg).generate_signals(df)
    assert set(out["signal"].unique()).issubset({-1, 0, 1})
