"""
Indicateurs techniques.

Chaque fonction prend un DataFrame contenant au minimum une colonne 'close'
et lui AJOUTE une (ou plusieurs) colonne(s) d'indicateur. Les fonctions
renvoient le DataFrame pour pouvoir les enchaîner.

Aucune dépendance réseau : ce sont des calculs purs sur des nombres,
donc faciles à tester. On code les indicateurs à la main (pas de `ta-lib`)
car c'est plus simple à installer sous Windows et plus pédagogique.
"""

from __future__ import annotations

import pandas as pd


def add_sma(df: pd.DataFrame, window: int, column: str = "close") -> pd.DataFrame:
    """Moyenne mobile simple (Simple Moving Average)."""
    df[f"sma_{window}"] = df[column].rolling(window=window).mean()
    return df


def add_ema(df: pd.DataFrame, window: int, column: str = "close") -> pd.DataFrame:
    """Moyenne mobile exponentielle (donne plus de poids aux prix récents)."""
    df[f"ema_{window}"] = df[column].ewm(span=window, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, window: int = 14, column: str = "close") -> pd.DataFrame:
    """
    RSI (Relative Strength Index), entre 0 et 100.

    Interprétation classique : > 70 = suracheté, < 30 = survendu.
    Cas limites : que des hausses -> RSI = 100 ; que des baisses -> RSI = 0.
    """
    delta = df[column].diff()
    gains = delta.clip(lower=0)        # hausses (les pertes deviennent 0)
    losses = -delta.clip(upper=0)      # baisses, en valeur positive

    avg_gain = gains.rolling(window=window).mean()
    avg_loss = losses.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Si aucune perte sur la fenêtre, le RSI vaut 100 (au lieu de NaN/inf).
    rsi = rsi.where(avg_loss != 0, other=100.0)
    df["rsi"] = rsi
    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    column: str = "close",
) -> pd.DataFrame:
    """
    MACD (Moving Average Convergence Divergence).

    Ajoute 3 colonnes :
      - macd        : EMA rapide - EMA lente
      - macd_signal : EMA du MACD
      - macd_hist   : macd - macd_signal (l'histogramme)
    """
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = macd_line - signal_line
    return df


def add_bollinger(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    column: str = "close",
) -> pd.DataFrame:
    """
    Bandes de Bollinger.

    Ajoute 3 colonnes : bb_mid (moyenne mobile), bb_upper, bb_lower.
    Un prix qui touche la bande haute/basse signale une volatilité forte.
    """
    mid = df[column].rolling(window=window).mean()
    std = df[column].rolling(window=window).std(ddof=0)

    df["bb_mid"] = mid
    df["bb_upper"] = mid + num_std * std
    df["bb_lower"] = mid - num_std * std
    return df


def detect_trend(df: pd.DataFrame, short: int = 20, long: int = 50) -> str:
    """
    Détecte une tendance simple à partir de deux moyennes mobiles.

    Renvoie 'haussiere', 'baissiere' ou 'neutre'. Si pas assez de données,
    renvoie 'neutre'.
    """
    if len(df) < long:
        return "neutre"

    sma_short = df["close"].rolling(short).mean().iloc[-1]
    sma_long = df["close"].rolling(long).mean().iloc[-1]

    if pd.isna(sma_short) or pd.isna(sma_long):
        return "neutre"
    if sma_short > sma_long:
        return "haussiere"
    if sma_short < sma_long:
        return "baissiere"
    return "neutre"


def add_all(df: pd.DataFrame, config=None) -> pd.DataFrame:
    """Ajoute tous les indicateurs usuels en une fois (pratique pour le dashboard)."""
    # Import local pour éviter une dépendance circulaire à l'import.
    from utils.config import default_config

    cfg = config or default_config
    add_rsi(df, window=cfg.rsi_window)
    add_sma(df, window=cfg.sma_short)
    add_sma(df, window=cfg.sma_long)
    add_ema(df, window=cfg.sma_short)
    add_macd(df)
    add_bollinger(df, window=cfg.bollinger_window, num_std=cfg.bollinger_std)
    return df
