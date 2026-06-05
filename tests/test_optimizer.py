"""Tests de l'auto-optimiseur."""

import numpy as np
import pandas as pd
import pytest

from core.optimizer import optimize_strategy
from core.strategy import EmaCrossStrategy


def _prices(n=300, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"close": 100 + np.cumsum(rng.normal(0, 1, n))})


def test_optimize_renvoie_des_parametres_de_la_grille():
    df = _prices()
    grille = {"short": [5, 10, 20], "long": [50, 100]}
    res = optimize_strategy(df, EmaCrossStrategy, grille, train_frac=0.7)
    assert res.best_params["short"] in grille["short"]
    assert res.best_params["long"] in grille["long"]


def test_optimize_evalue_sur_train_et_test():
    df = _prices()
    grille = {"short": [5, 10], "long": [50, 100]}
    res = optimize_strategy(df, EmaCrossStrategy, grille)
    # On a bien deux rendements distincts (passé vs futur simulé).
    assert isinstance(res.train_return_pct, float)
    assert isinstance(res.test_return_pct, float)
    # Le tableau contient toutes les combinaisons (2 x 2 = 4).
    assert len(res.all_results) == 4


def test_all_results_tries_par_rendement_decroissant():
    df = _prices()
    grille = {"short": [5, 10, 20], "long": [50, 100]}
    res = optimize_strategy(df, EmaCrossStrategy, grille)
    rendements = [r for _, r in res.all_results]
    assert rendements == sorted(rendements, reverse=True)


def test_grille_vide_leve_erreur():
    with pytest.raises(ValueError):
        optimize_strategy(_prices(), EmaCrossStrategy, {})


def test_pas_assez_de_donnees_leve_erreur():
    petit = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
    with pytest.raises(ValueError):
        optimize_strategy(petit, EmaCrossStrategy, {"short": [2], "long": [3]})
