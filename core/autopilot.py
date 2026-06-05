"""
Pilote automatique — paper trading autonome.

Un portefeuille FICTIF qui "vit" entre les exécutions : son état est sauvegardé
sur le disque (JSON). À chaque appel de `step()`, il :
  1. télécharge les dernières bougies,
  2. calcule les signaux avec la stratégie choisie,
  3. applique les NOUVELLES bougies (celles pas encore traitées) au portefeuille,
  4. enregistre l'évolution et sauvegarde.

⚠️ 100 % simulation. Aucun ordre réel, aucun argent réel. C'est volontaire :
l'autonomie ne touche jamais de vrais fonds.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from core import indicators
from core.market_data import fetch_ohlcv
from core.paper_trading import PaperPortfolio
from core.strategy import get_strategy
from utils.config import DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_STATE_PATH = DATA_DIR / "autopilot_state.json"


@dataclass
class AutopilotState:
    symbol: str = "BTC/USDT"
    timeframe: str = "1d"
    strategy: str = "rsi_sma"
    initial_capital: float = 1000.0
    cash: float = 1000.0
    units: float = 0.0
    entry_price: float = 0.0
    last_timestamp: str | None = None            # dernière bougie traitée (ISO)
    trades: int = 0
    history: list = field(default_factory=list)  # [{time, price, signal, equity}]


class Autopilot:
    """Pilote le portefeuille fictif et persiste son état."""

    def __init__(self, state: AutopilotState, state_path: Path = DEFAULT_STATE_PATH):
        self.state = state
        self.state_path = state_path

    # --- Chargement / sauvegarde ---

    @classmethod
    def load(
        cls,
        state_path: Path = DEFAULT_STATE_PATH,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        strategy: str = "rsi_sma",
        initial_capital: float = 1000.0,
    ) -> "Autopilot":
        """Charge l'état existant, ou en crée un neuf s'il n'existe pas."""
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            return cls(AutopilotState(**data), state_path)
        state = AutopilotState(
            symbol=symbol, timeframe=timeframe, strategy=strategy,
            initial_capital=initial_capital, cash=initial_capital,
        )
        return cls(state, state_path)

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Repart de zéro (garde symbole/stratégie/capital)."""
        s = self.state
        self.state = AutopilotState(
            symbol=s.symbol, timeframe=s.timeframe, strategy=s.strategy,
            initial_capital=s.initial_capital, cash=s.initial_capital,
        )
        self.save()

    # --- Reconstruction du portefeuille depuis l'état ---

    def _portfolio(self) -> PaperPortfolio:
        pf = PaperPortfolio(initial_capital=self.state.initial_capital)
        pf.cash = self.state.cash
        pf.units = self.state.units
        pf.entry_price = self.state.entry_price
        return pf

    # --- Un pas d'autonomie ---

    def step(self, limit: int = 500) -> dict:
        """
        Télécharge les données et traite les bougies non encore vues.

        Renvoie un petit rapport. Au tout premier appel, tout l'historique
        disponible est ingéré pour que le portefeuille reflète la stratégie à ce jour.
        """
        df = fetch_ohlcv(self.state.symbol, self.state.timeframe, limit=limit)
        df = get_strategy(self.state.strategy).generate_signals(indicators.add_all(df))

        # Ne garder que les bougies postérieures à la dernière traitée.
        if self.state.last_timestamp is not None:
            nouveau = df[df["timestamp"].astype(str) > self.state.last_timestamp]
        else:
            nouveau = df

        pf = self._portfolio()
        traitees = 0
        for _, ligne in nouveau.iterrows():
            prix = float(ligne["close"])
            signal = int(ligne["signal"])
            pf.on_bar(prix, signal)
            self.state.history.append({
                "time": str(ligne["timestamp"]),
                "price": prix,
                "signal": signal,
                "equity": pf.equity(prix),
            })
            self.state.last_timestamp = str(ligne["timestamp"])
            traitees += 1

        # Recopier l'état du portefeuille dans l'état persistant.
        self.state.cash = pf.cash
        self.state.units = pf.units
        self.state.entry_price = pf.entry_price
        self.state.trades = len(pf.trades)
        self.save()

        logger.info("Autopilot : %d nouvelle(s) bougie(s) traitée(s).", traitees)
        return {
            "bougies_traitees": traitees,
            "equity": pf.equity(),
            "en_position": pf.in_position,
            "rendement_pct": (pf.equity() / self.state.initial_capital - 1) * 100,
        }

    def status(self) -> dict:
        pf = self._portfolio()
        equity = pf.equity(self.state.history[-1]["price"]) if self.state.history else pf.cash
        return {
            "symbol": self.state.symbol,
            "strategy": self.state.strategy,
            "capital_initial": self.state.initial_capital,
            "valeur_actuelle": equity,
            "rendement_pct": (equity / self.state.initial_capital - 1) * 100,
            "en_position": pf.in_position,
            "nombre_trades": self.state.trades,
            "bougies_vues": len(self.state.history),
        }
