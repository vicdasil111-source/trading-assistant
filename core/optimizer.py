"""
Auto-optimisation de stratégie.

Le bot teste automatiquement de nombreuses combinaisons de paramètres et garde
la meilleure. POINT CLÉ pédagogique : on coupe les données en deux dans le temps :

  - une partie "entraînement" (in-sample, le passé) sur laquelle on cherche les
    meilleurs paramètres ;
  - une partie "test" (out-of-sample, le futur simulé) que l'optimiseur n'a
    JAMAIS vue, pour mesurer si les paramètres tiennent vraiment.

Si la performance s'effondre entre l'entraînement et le test, c'est du
SUR-APPRENTISSAGE : les paramètres ont mémorisé le passé sans rien comprendre.
C'est le piège n°1 de l'optimisation, et cet outil sert justement à le voir.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import pandas as pd

from core.backtest import backtest


@dataclass
class OptimizationResult:
    best_params: dict
    train_return_pct: float          # rendement sur l'entraînement (passé)
    test_return_pct: float           # rendement sur le test (futur simulé)
    buy_hold_test_pct: float         # référence Buy & Hold sur le test
    all_results: list = field(default_factory=list)  # (params, train_return) triés

    @property
    def overfitting_gap(self) -> float:
        """Écart entraînement - test. Grand écart positif = sur-apprentissage probable."""
        return self.train_return_pct - self.test_return_pct

    def summary(self) -> str:
        verdict = ("⚠️ écart important entraînement/test : sur-apprentissage probable"
                   if self.overfitting_gap > 20 else
                   "semble se généraliser correctement")
        return (
            f"Meilleurs paramètres : {self.best_params}\n"
            f"Rendement entraînement (passé)   : {self.train_return_pct:+.2f} %\n"
            f"Rendement test (futur simulé)    : {self.test_return_pct:+.2f} %\n"
            f"Buy & Hold sur le test           : {self.buy_hold_test_pct:+.2f} %\n"
            f"Écart (overfitting)              : {self.overfitting_gap:+.2f} %  ({verdict})"
        )


def optimize_strategy(
    df: pd.DataFrame,
    strategy_class,
    param_grid: dict,
    initial_capital: float = 1000.0,
    fee_pct: float = 0.1,
    train_frac: float = 0.7,
    metric: str = "total_return_pct",
) -> OptimizationResult:
    """
    Cherche les meilleurs paramètres de `strategy_class` par recherche exhaustive.

    - `param_grid` : dict {nom_param: [valeurs à essayer]}. Ex pour EmaCrossStrategy :
        {"short": [10, 20], "long": [50, 100]}.
    - `train_frac` : proportion des données (au début) servant à l'optimisation.
    - `metric` : attribut de BacktestResult à maximiser (ex. 'total_return_pct'
      ou 'sharpe_ratio').

    La meilleure combinaison est choisie sur l'entraînement, puis évaluée
    honnêtement sur le test.
    """
    if not param_grid:
        raise ValueError("param_grid ne doit pas être vide.")
    if len(df) < 20:
        raise ValueError("Pas assez de données pour optimiser (minimum 20 bougies).")

    split = int(len(df) * train_frac)
    train = df.iloc[:split].reset_index(drop=True)
    test = df.iloc[split:].reset_index(drop=True)

    noms = list(param_grid.keys())
    resultats = []
    best_params = None
    best_score = float("-inf")

    for combinaison in itertools.product(*param_grid.values()):
        params = dict(zip(noms, combinaison))
        strat = strategy_class(**params)
        res = backtest(strat.generate_signals(train), initial_capital, fee_pct)
        score = getattr(res, metric)
        resultats.append((params, res.total_return_pct))
        if score > best_score:
            best_score = score
            best_params = params

    # Évaluation hors échantillon (le test n'a jamais influencé le choix).
    strat = strategy_class(**best_params)
    res_train = backtest(strat.generate_signals(train), initial_capital, fee_pct)
    res_test = backtest(strat.generate_signals(test), initial_capital, fee_pct)

    resultats.sort(key=lambda x: x[1], reverse=True)
    return OptimizationResult(
        best_params=best_params,
        train_return_pct=res_train.total_return_pct,
        test_return_pct=res_test.total_return_pct,
        buy_hold_test_pct=res_test.buy_hold_return_pct,
        all_results=resultats,
    )
