"""
Récupération des données de marché (OHLCV) en crypto.

On utilise `ccxt` avec l'API PUBLIQUE de Binance : aucune clé n'est nécessaire
pour lire les prix. Les données sont mises en cache dans `data/` pour éviter
de retélécharger et pour fonctionner hors-ligne après un premier téléchargement.

OHLCV = Open, High, Low, Close, Volume (ouverture, haut, bas, clôture, volume).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from utils.config import DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

# Données d'exemple réelles embarquées (versionnées dans git), utilisées en dernier
# recours si le réseau ET le cache local échouent — utile sur un hébergement où
# l'API Binance est bloquée. Le site déployé montre alors des données réelles,
# simplement potentiellement un peu anciennes.
SAMPLES_DIR = DATA_DIR / "samples"


def _cache_path(symbol: str, timeframe: str) -> Path:
    """Chemin du fichier cache pour un couple symbole/timeframe."""
    safe = symbol.replace("/", "-")
    return DATA_DIR / f"{safe}_{timeframe}.csv"


def _sample_path(symbol: str, timeframe: str) -> Path:
    """Chemin du jeu de données d'exemple embarqué."""
    safe = symbol.replace("/", "-")
    return SAMPLES_DIR / f"{safe}_{timeframe}.csv"


def _save_cache(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _load_cache(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


def fetch_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1d",
    limit: int = 500,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Récupère les bougies OHLCV pour `symbol`.

    Stratégie de robustesse :
      1. Tente de télécharger depuis Binance (données publiques).
      2. En cas d'échec réseau, se rabat sur le cache local s'il existe.
      3. Sinon, lève une erreur claire.

    Renvoie un DataFrame avec les colonnes :
    timestamp, open, high, low, close, volume.
    """
    path = _cache_path(symbol, timeframe)

    try:
        import ccxt  # import local : pas besoin de ccxt pour les tests d'indicateurs

        exchange = ccxt.binance()
        logger.info("Téléchargement de %s (%s, %d bougies)...", symbol, timeframe, limit)
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            raise ValueError(f"Aucune donnée renvoyée pour {symbol} ({timeframe}).")

        df = pd.DataFrame(raw, columns=_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        if use_cache:
            _save_cache(df, path)
        return df

    except Exception as exc:  # réseau coupé, symbole invalide, ccxt absent...
        logger.warning("Échec du téléchargement (%s).", exc)
        if use_cache and path.exists():
            logger.info("Repli sur le cache local : %s", path)
            return _load_cache(path)
        sample = _sample_path(symbol, timeframe)
        if sample.exists():
            logger.info("Repli sur les données d'exemple embarquées : %s", sample)
            return _load_cache(sample)
        raise RuntimeError(
            f"Impossible de récupérer les données pour {symbol} ({timeframe}) "
            f"et aucun cache ni exemple disponible. Vérifie ta connexion internet "
            f"et le nom du symbole (ex. 'BTC/USDT')."
        ) from exc


def fetch_many(
    symbols,
    timeframe: str = "1d",
    limit: int = 60,
    max_workers: int = 8,
) -> dict[str, pd.DataFrame]:
    """Récupère plusieurs symboles **en parallèle** (I/O réseau → gros gain de
    vitesse). Chaque appel à `fetch_ohlcv` crée sa propre connexion ccxt, donc
    c'est sûr en threads. Les symboles en échec sont simplement ignorés.

    Renvoie un dict {symbole: DataFrame} (sans les symboles indisponibles).
    """
    symbols = list(symbols)
    if not symbols:
        return {}

    def _one(sym: str):
        try:
            return sym, fetch_ohlcv(sym, timeframe, limit=limit)
        except Exception:  # réseau, symbole invalide… : on saute
            return sym, None

    out: dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=min(max_workers, len(symbols))) as pool:
        for sym, df in pool.map(_one, symbols):
            if df is not None:
                out[sym] = df
    return out
