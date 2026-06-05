"""
Stratégies de trading.

Une stratégie transforme des données (+ indicateurs) en une colonne `signal` :
  +1 = achat, -1 = vente, 0 = ne rien faire.

C'est la pièce centrale : le backtest ET le paper trading consomment cette
même colonne `signal`. Pour créer ta propre stratégie, hérite de `Strategy`
et implémente `generate_signals`.
"""

from __future__ import annotations

import pandas as pd

from core import indicators
from utils.config import Config, default_config


class Strategy:
    """Classe de base. Une stratégie doit implémenter `generate_signals`."""

    name: str = "base"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:  # pragma: no cover
        raise NotImplementedError("Implémente generate_signals dans ta sous-classe.")


class RsiSmaStrategy(Strategy):
    """
    Stratégie d'exemple : RSI + moyenne mobile.

    - ACHAT (+1)  : le RSI passe en zone de survente (< seuil bas)
                    ET le prix est au-dessus de sa moyenne mobile longue
                    (on n'achète que dans une tendance plutôt saine).
    - VENTE (-1)  : le RSI passe en zone de surachat (> seuil haut).
    - Sinon : 0.
    """

    name = "rsi_sma"

    def __init__(
        self,
        config: Config | None = None,
        rsi_window: int | None = None,
        rsi_oversold: float | None = None,
        rsi_overbought: float | None = None,
        sma_long: int | None = None,
    ):
        # Les paramètres explicites priment ; sinon on prend ceux de la config.
        # (Permet à l'optimiseur d'essayer plein de réglages.)
        cfg = config or default_config
        self.rsi_window = rsi_window if rsi_window is not None else cfg.rsi_window
        self.rsi_oversold = rsi_oversold if rsi_oversold is not None else cfg.rsi_oversold
        self.rsi_overbought = rsi_overbought if rsi_overbought is not None else cfg.rsi_overbought
        self.sma_long = sma_long if sma_long is not None else cfg.sma_long

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Calcule les indicateurs nécessaires s'ils ne sont pas déjà là.
        if "rsi" not in df.columns:
            indicators.add_rsi(df, window=self.rsi_window)
        sma_col = f"sma_{self.sma_long}"
        if sma_col not in df.columns:
            indicators.add_sma(df, window=self.sma_long)

        df["signal"] = 0
        achat = (df["rsi"] < self.rsi_oversold) & (df["close"] > df[sma_col])
        vente = df["rsi"] > self.rsi_overbought
        df.loc[achat, "signal"] = 1
        df.loc[vente, "signal"] = -1
        return df


class EmaCrossStrategy(Strategy):
    """
    Stratégie de croisement de moyennes (golden cross / death cross).

    - ACHAT (+1) : l'EMA courte croise l'EMA longue VERS LE HAUT.
    - VENTE (-1) : l'EMA courte croise l'EMA longue VERS LE BAS.
    """

    name = "ema_cross"

    def __init__(self, short: int = 20, long: int = 50):
        self.short = short
        self.long = long

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        indicators.add_ema(df, window=self.short)
        indicators.add_ema(df, window=self.long)
        short_col, long_col = f"ema_{self.short}", f"ema_{self.long}"

        # Position relative des deux moyennes, hier et aujourd'hui.
        au_dessus = df[short_col] > df[long_col]
        croise_haut = au_dessus & ~au_dessus.shift(1, fill_value=False)
        croise_bas = ~au_dessus & au_dessus.shift(1, fill_value=False)

        df["signal"] = 0
        df.loc[croise_haut, "signal"] = 1
        df.loc[croise_bas, "signal"] = -1
        return df


class MacdCrossStrategy(Strategy):
    """
    Stratégie MACD : on suit le croisement entre la ligne MACD et sa ligne de signal.

    - ACHAT (+1) : la ligne MACD croise sa ligne de signal VERS LE HAUT
                   (momentum qui devient positif).
    - VENTE (-1) : elle croise VERS LE BAS.
    """

    name = "macd_cross"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "macd" not in df.columns or "macd_signal" not in df.columns:
            indicators.add_macd(df)

        au_dessus = df["macd"] > df["macd_signal"]
        croise_haut = au_dessus & ~au_dessus.shift(1, fill_value=False)
        croise_bas = ~au_dessus & au_dessus.shift(1, fill_value=False)

        df["signal"] = 0
        df.loc[croise_haut, "signal"] = 1
        df.loc[croise_bas, "signal"] = -1
        return df


class BollingerStrategy(Strategy):
    """
    Stratégie de retour à la moyenne avec les bandes de Bollinger.

    - ACHAT (+1) : le prix passe SOUS la bande basse (potentiellement survendu).
    - VENTE (-1) : le prix repasse AU-DESSUS de la bande médiane (moyenne).
    """

    name = "bollinger"

    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "bb_lower" not in df.columns:
            indicators.add_bollinger(df, window=self.window, num_std=self.num_std)

        df["signal"] = 0
        df.loc[df["close"] < df["bb_lower"], "signal"] = 1
        df.loc[df["close"] > df["bb_mid"], "signal"] = -1
        return df


class BreakoutStrategy(Strategy):
    """
    Stratégie de cassure (breakout).

    - ACHAT (+1) : le prix dépasse le plus haut des `window` dernières bougies.
    - VENTE (-1) : le prix casse sous le plus bas des `window` dernières bougies.

    On compare au plus haut/bas PRÉCÉDENT (décalé d'une bougie) pour ne pas
    « tricher » avec l'information du jour même.
    """

    name = "breakout"

    def __init__(self, window: int = 20):
        self.window = window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        plus_haut = df["close"].rolling(self.window).max().shift(1)
        plus_bas = df["close"].rolling(self.window).min().shift(1)
        df["signal"] = 0
        df.loc[df["close"] > plus_haut, "signal"] = 1
        df.loc[df["close"] < plus_bas, "signal"] = -1
        return df


# Registre des stratégies disponibles, pour les sélectionner par leur nom.
AVAILABLE_STRATEGIES = {
    RsiSmaStrategy.name: RsiSmaStrategy,
    EmaCrossStrategy.name: EmaCrossStrategy,
    MacdCrossStrategy.name: MacdCrossStrategy,
    BollingerStrategy.name: BollingerStrategy,
    BreakoutStrategy.name: BreakoutStrategy,
}


def get_strategy(name: str) -> Strategy:
    """Instancie une stratégie par son nom (ex. 'rsi_sma')."""
    if name not in AVAILABLE_STRATEGIES:
        dispo = ", ".join(AVAILABLE_STRATEGIES)
        raise ValueError(f"Stratégie inconnue '{name}'. Disponibles : {dispo}")
    return AVAILABLE_STRATEGIES[name]()
