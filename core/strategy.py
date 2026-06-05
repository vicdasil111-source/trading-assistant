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

    def __init__(self, config: Config | None = None):
        self.cfg = config or default_config

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Calcule les indicateurs nécessaires s'ils ne sont pas déjà là.
        if "rsi" not in df.columns:
            indicators.add_rsi(df, window=self.cfg.rsi_window)
        sma_col = f"sma_{self.cfg.sma_long}"
        if sma_col not in df.columns:
            indicators.add_sma(df, window=self.cfg.sma_long)

        df["signal"] = 0
        achat = (df["rsi"] < self.cfg.rsi_oversold) & (df["close"] > df[sma_col])
        vente = df["rsi"] > self.cfg.rsi_overbought
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


# Registre des stratégies disponibles, pour les sélectionner par leur nom.
AVAILABLE_STRATEGIES = {
    RsiSmaStrategy.name: RsiSmaStrategy,
    EmaCrossStrategy.name: EmaCrossStrategy,
}


def get_strategy(name: str) -> Strategy:
    """Instancie une stratégie par son nom (ex. 'rsi_sma')."""
    if name not in AVAILABLE_STRATEGIES:
        dispo = ", ".join(AVAILABLE_STRATEGIES)
        raise ValueError(f"Stratégie inconnue '{name}'. Disponibles : {dispo}")
    return AVAILABLE_STRATEGIES[name]()
