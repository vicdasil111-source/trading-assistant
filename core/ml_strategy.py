"""
Stratégie par Machine Learning.

Un modèle (régression logistique ou arbre de décision) apprend, à partir
d'indicateurs (RSI, MACD, rendement...), à prédire si la PROCHAINE bougie sera
haussière ou baissière. La prédiction devient un signal d'achat/vente.

⚠️ Honnêteté : prédire les marchés est très difficile. Ce module est un
support d'apprentissage. On évite soigneusement de "tricher" (pas de fuite
d'information du futur), et on évalue le modèle sur des données qu'il n'a
jamais vues. Une précision proche de 50 % signifie « pas mieux qu'un tirage
à pile ou face » — c'est souvent le cas, et c'est une leçon en soi.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core import indicators
from core.strategy import Strategy

# Colonnes utilisées comme caractéristiques (features) du modèle.
FEATURES = ["rsi", "macd", "macd_hist", "ret1", "ret3", "sma_ratio"]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes de features. N'utilise QUE des informations passées/présentes."""
    df = df.copy()
    indicators.add_rsi(df, window=14)
    indicators.add_macd(df)
    indicators.add_sma(df, window=20)
    df["ret1"] = df["close"].pct_change(1)          # rendement sur 1 bougie
    df["ret3"] = df["close"].pct_change(3)          # rendement sur 3 bougies
    df["sma_ratio"] = df["close"] / df["sma_20"]    # position vs moyenne
    return df


def _make_model(kind: str):
    """Crée un modèle scikit-learn (import local : sklearn n'est requis que pour le ML)."""
    if kind == "tree":
        from sklearn.tree import DecisionTreeClassifier
        return DecisionTreeClassifier(max_depth=4, random_state=0)
    if kind == "logistic":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    raise ValueError(f"Modèle inconnu '{kind}'. Choix : 'logistic' ou 'tree'.")


@dataclass
class MLEvaluation:
    train_accuracy: float            # précision sur l'entraînement
    test_accuracy: float             # précision hors échantillon (la vraie mesure)
    test_return_pct: float           # rendement d'un backtest sur le test
    buy_hold_test_pct: float
    n_train: int
    n_test: int

    def summary(self) -> str:
        verdict = ("à peine mieux que le hasard" if self.test_accuracy < 0.55
                   else "intéressant, à confirmer")
        return (
            f"Précision entraînement : {self.train_accuracy:.1%}\n"
            f"Précision test (hors échantillon) : {self.test_accuracy:.1%}  ({verdict})\n"
            f"Rendement backtest (test) : {self.test_return_pct:+.2f} %\n"
            f"Buy & Hold (test) : {self.buy_hold_test_pct:+.2f} %\n"
            f"Échantillons : {self.n_train} entraînement / {self.n_test} test"
        )


class MLStrategy(Strategy):
    """
    Stratégie ML : prédit la direction de la prochaine bougie.

    signal = +1 si le modèle prévoit une hausse, -1 sinon.
    """

    name = "ml"

    def __init__(self, kind: str = "logistic", train_frac: float = 0.7):
        self.kind = kind
        self.train_frac = train_frac
        self.model = None
        self.n_train = 0

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = _build_features(df)
        # Cible : la prochaine bougie monte-t-elle ? (utilise le futur -> entraînement seulement)
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

        data = df.dropna(subset=FEATURES + ["target"])
        if len(data) < 30:
            raise ValueError("Pas assez de données pour entraîner le modèle (min 30 lignes utilisables).")

        split = int(len(data) * self.train_frac)
        train = data.iloc[:split]
        self.n_train = len(train)

        self.model = _make_model(self.kind)
        self.model.fit(train[FEATURES], train["target"])

        # Prédiction sur toutes les lignes exploitables.
        preds = self.model.predict(data[FEATURES])
        df["signal"] = 0
        df.loc[data.index, "signal"] = np.where(preds == 1, 1, -1)
        return df


def evaluate_ml(
    df: pd.DataFrame,
    kind: str = "logistic",
    train_frac: float = 0.7,
    initial_capital: float = 1000.0,
    fee_pct: float = 0.1,
) -> MLEvaluation:
    """Entraîne le modèle et l'évalue honnêtement sur la partie test (jamais vue)."""
    from sklearn.metrics import accuracy_score

    from core.backtest import backtest

    feat = _build_features(df)
    feat["target"] = (feat["close"].shift(-1) > feat["close"]).astype(int)
    data = feat.dropna(subset=FEATURES + ["target"])
    if len(data) < 30:
        raise ValueError("Pas assez de données pour évaluer le modèle (min 30 lignes).")

    split = int(len(data) * train_frac)
    train, test = data.iloc[:split], data.iloc[split:]

    model = _make_model(kind)
    model.fit(train[FEATURES], train["target"])

    train_acc = accuracy_score(train["target"], model.predict(train[FEATURES]))
    test_acc = accuracy_score(test["target"], model.predict(test[FEATURES]))

    # Backtest sur la partie test, à partir des prédictions du modèle.
    test_bt = test.copy()
    test_bt["signal"] = np.where(model.predict(test[FEATURES]) == 1, 1, -1)
    res = backtest(test_bt, initial_capital, fee_pct)

    return MLEvaluation(
        train_accuracy=train_acc,
        test_accuracy=test_acc,
        test_return_pct=res.total_return_pct,
        buy_hold_test_pct=res.buy_hold_return_pct,
        n_train=len(train),
        n_test=len(test),
    )
