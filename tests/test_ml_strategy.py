"""Tests de la stratégie Machine Learning."""

import numpy as np
import pandas as pd
import pytest

from core.ml_strategy import MLStrategy, evaluate_ml


def _prices(n=300, seed=2):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"close": 100 + np.cumsum(rng.normal(0, 1, n))})


def test_ml_signaux_valides():
    out = MLStrategy(kind="logistic").generate_signals(_prices())
    assert "signal" in out.columns
    assert set(out["signal"].unique()).issubset({-1, 0, 1})


def test_ml_arbre_fonctionne_aussi():
    out = MLStrategy(kind="tree").generate_signals(_prices())
    assert set(out["signal"].unique()).issubset({-1, 0, 1})


def test_evaluate_ml_precisions_dans_zero_un():
    ev = evaluate_ml(_prices(), kind="logistic")
    assert 0.0 <= ev.train_accuracy <= 1.0
    assert 0.0 <= ev.test_accuracy <= 1.0
    assert ev.n_train > 0 and ev.n_test > 0


def test_modele_inconnu_leve_erreur():
    with pytest.raises(ValueError):
        MLStrategy(kind="inexistant").generate_signals(_prices())


def test_pas_assez_de_donnees_leve_erreur():
    with pytest.raises(ValueError):
        evaluate_ml(pd.DataFrame({"close": [1, 2, 3, 4, 5]}))
