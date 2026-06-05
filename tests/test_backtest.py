"""Tests du moteur de backtest, avec des scénarios calculés à la main."""

import pandas as pd
import pytest

from core.backtest import backtest


def _df(prices, signals):
    return pd.DataFrame({"close": prices, "signal": signals})


def test_trade_gagnant():
    # Achat à 10, vente à 20 : on double l'argent.
    df = _df([10, 10, 20, 20, 5], [1, 0, -1, 0, 0])
    res = backtest(df, initial_capital=100)
    assert res.final_equity == pytest.approx(200.0)
    assert res.total_return_pct == pytest.approx(100.0)
    assert res.num_trades == 1
    assert res.win_rate_pct == pytest.approx(100.0)


def test_trade_perdant():
    # Achat à 10, vente à 5 : on perd la moitié.
    df = _df([10, 5], [1, -1])
    res = backtest(df, initial_capital=100)
    assert res.final_equity == pytest.approx(50.0)
    assert res.total_return_pct == pytest.approx(-50.0)
    assert res.num_trades == 1
    assert res.win_rate_pct == pytest.approx(0.0)
    assert res.profit_factor == pytest.approx(0.0)


def test_position_ouverte_cloturee_a_la_fin():
    # Achat à 10, jamais de vente -> clôturé au dernier prix (20).
    df = _df([10, 20], [1, 0])
    res = backtest(df, initial_capital=100)
    assert res.num_trades == 1
    assert res.final_equity == pytest.approx(200.0)


def test_aucun_signal_capital_inchange():
    df = _df([10, 20, 30], [0, 0, 0])
    res = backtest(df, initial_capital=100)
    assert res.num_trades == 0
    assert res.final_equity == pytest.approx(100.0)
    assert res.total_return_pct == pytest.approx(0.0)


def test_drawdown_maximal():
    # On garde la position pendant que le prix monte à 200 puis chute à 50.
    df = _df([10, 20, 5, 8], [1, 0, 0, 0])
    res = backtest(df, initial_capital=100)
    # Sommet d'équité = 200, creux = 50 -> drawdown = -75 %.
    assert res.max_drawdown_pct == pytest.approx(-75.0, abs=0.1)


def test_erreur_si_pas_de_colonne_signal():
    df = pd.DataFrame({"close": [1, 2, 3]})
    with pytest.raises(ValueError):
        backtest(df)


def test_equity_curve_meme_longueur_que_donnees():
    df = _df([10, 11, 12, 13], [1, 0, -1, 0])
    res = backtest(df, initial_capital=100)
    assert len(res.equity_curve) == len(df)
