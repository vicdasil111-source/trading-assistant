"""
Configuration centrale du Trading Assistant.

Tous les paramètres modifiables sont ici, dans un seul endroit.
AUCUNE clé API privée n'est nécessaire : on n'utilise que des données publiques.
"""

from dataclasses import dataclass, field
from pathlib import Path

# Dossier racine du projet (le parent de "utils/")
ROOT_DIR = Path(__file__).resolve().parent.parent

# Dossier de cache des données téléchargées (ignoré par git)
DATA_DIR = ROOT_DIR / "data"


@dataclass
class Config:
    """Paramètres par défaut. Modifie-les ici ou en passant des arguments au CLI."""

    # --- Marché ---
    symbol: str = "BTC/USDT"      # actif analysé (format ccxt)
    timeframe: str = "1d"          # bougie : 1m, 5m, 1h, 4h, 1d, 1w...
    limit: int = 500               # nombre de bougies récupérées

    # --- Capital (FICTIF — paper trading / backtest uniquement) ---
    initial_capital: float = 1000.0

    # --- Paramètres d'indicateurs ---
    rsi_window: int = 14
    rsi_oversold: float = 30.0     # en-dessous = potentiellement survendu (achat)
    rsi_overbought: float = 70.0   # au-dessus = potentiellement suracheté (vente)
    sma_short: int = 20
    sma_long: int = 50
    bollinger_window: int = 20
    bollinger_std: float = 2.0

    # --- Gestion du risque ---
    risk_per_trade_pct: float = 1.0  # % du capital risqué par trade

    # --- Cache ---
    use_cache: bool = True
    data_dir: Path = field(default_factory=lambda: DATA_DIR)


# Instance par défaut, pratique à importer : `from utils.config import default_config`
default_config = Config()
