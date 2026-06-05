"""Tests des indicateurs techniques (calculs purs, sans réseau)."""

import numpy as np
import pandas as pd
import pytest

from core import indicators


def _df(prices):
    """Petit DataFrame avec juste une colonne 'close'."""
    return pd.DataFrame({"close": prices})


def test_sma_valeurs_connues():
    df = _df([1, 2, 3, 4, 5])
    indicators.add_sma(df, window=3)
    # Les 2 premières valeurs sont NaN (fenêtre incomplète).
    assert np.isnan(df["sma_3"].iloc[0])
    assert df["sma_3"].iloc[2] == pytest.approx(2.0)   # (1+2+3)/3
    assert df["sma_3"].iloc[4] == pytest.approx(4.0)   # (3+4+5)/3


def test_ema_premiere_valeur_egale_au_prix():
    df = _df([10, 20, 30])
    indicators.add_ema(df, window=2)
    # Avec adjust=False, la première EMA est égale au premier prix.
    assert df["ema_2"].iloc[0] == pytest.approx(10.0)
    # L'EMA réagit et reste entre les valeurs récentes.
    assert 10 < df["ema_2"].iloc[-1] <= 30


def test_rsi_que_des_hausses_vaut_100():
    df = _df(list(range(1, 20)))  # strictement croissant
    indicators.add_rsi(df, window=14)
    assert df["rsi"].iloc[-1] == pytest.approx(100.0)


def test_rsi_que_des_baisses_vaut_0():
    df = _df(list(range(20, 1, -1)))  # strictement décroissant
    indicators.add_rsi(df, window=14)
    assert df["rsi"].iloc[-1] == pytest.approx(0.0)


def test_rsi_borne_entre_0_et_100():
    rng = np.random.default_rng(42)
    prices = 100 + np.cumsum(rng.normal(0, 1, 200))
    df = _df(prices)
    indicators.add_rsi(df, window=14)
    rsi = df["rsi"].dropna()
    assert (rsi >= 0).all() and (rsi <= 100).all()


def test_macd_colonnes_et_coherence():
    df = _df(list(range(1, 60)))
    indicators.add_macd(df)
    for col in ("macd", "macd_signal", "macd_hist"):
        assert col in df.columns
    # hist = macd - signal, par définition.
    np.testing.assert_allclose(
        df["macd_hist"].values, (df["macd"] - df["macd_signal"]).values
    )


def test_bollinger_ordre_des_bandes():
    rng = np.random.default_rng(0)
    df = _df(100 + rng.normal(0, 5, 100))
    indicators.add_bollinger(df, window=20, num_std=2)
    valides = df.dropna(subset=["bb_lower", "bb_mid", "bb_upper"])
    assert (valides["bb_lower"] <= valides["bb_mid"]).all()
    assert (valides["bb_mid"] <= valides["bb_upper"]).all()


def test_detect_trend_haussiere():
    # Prix qui montent franchement -> tendance haussière.
    df = _df(list(range(1, 101)))
    assert indicators.detect_trend(df, short=20, long=50) == "haussiere"


def test_detect_trend_baissiere():
    df = _df(list(range(100, 0, -1)))
    assert indicators.detect_trend(df, short=20, long=50) == "baissiere"


def test_detect_trend_pas_assez_de_donnees():
    df = _df([1, 2, 3])
    assert indicators.detect_trend(df, short=20, long=50) == "neutre"


def _ohlcv(n=60, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame({
        "open": close, "high": close + 1.5, "low": close - 1.5,
        "close": close, "volume": rng.uniform(100, 1000, n),
    })


def test_atr_positif_et_borne():
    df = _ohlcv()
    indicators.add_atr(df, window=14)
    atr = df["atr"].dropna()
    assert (atr >= 0).all()
    assert not atr.empty


def test_stochastic_borne_0_100():
    df = _ohlcv()
    indicators.add_stochastic(df)
    k = df["stoch_k"].dropna()
    assert (k >= 0).all() and (k <= 100).all()


def test_stochastic_proche_100_si_cloture_au_plus_haut():
    # Clôture = plus haut de chaque bougie, prix croissant -> %K proche de 100.
    n = 30
    close = pd.Series(range(1, n + 1), dtype=float)
    df = pd.DataFrame({"high": close, "low": close - 0.5, "close": close})
    indicators.add_stochastic(df, k_window=14)
    assert df["stoch_k"].iloc[-1] == pytest.approx(100.0, abs=1.0)


def test_obv_monte_quand_le_prix_monte():
    df = pd.DataFrame({"close": [10, 11, 12, 13], "volume": [100, 100, 100, 100]})
    indicators.add_obv(df)
    # Trois hausses consécutives de +100 de volume chacune -> OBV = 0,100,200,300.
    assert list(df["obv"]) == [0, 100, 200, 300]
