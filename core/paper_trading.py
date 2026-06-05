"""
Paper trading : un portefeuille FICTIF.

Aucun argent réel n'est jamais engagé. C'est un objet à état que tu nourris
bougie par bougie (prix + signal). Il reproduit la logique du backtest mais
"en temps réel", pour t'entraîner sans aucun risque.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Trade:
    """Un trade clôturé (entrée -> sortie)."""

    entry_price: float
    exit_price: float
    units: float

    @property
    def pnl(self) -> float:
        return (self.exit_price - self.entry_price) * self.units


@dataclass
class PaperPortfolio:
    """Portefeuille fictif long-only, "tout ou rien" (comme le backtest)."""

    initial_capital: float = 1000.0
    cash: float = field(init=False)
    units: float = field(default=0.0, init=False)
    entry_price: float = field(default=0.0, init=False)
    trades: list[Trade] = field(default_factory=list, init=False)
    last_price: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.cash = float(self.initial_capital)

    @property
    def in_position(self) -> bool:
        return self.units > 0

    def equity(self, price: float | None = None) -> float:
        """Valeur totale du portefeuille (cash + position) au prix donné."""
        price = self.last_price if price is None else price
        return self.cash + self.units * price

    def on_bar(self, price: float, signal: int) -> None:
        """
        Traite une nouvelle bougie : met à jour le prix et agit selon le signal.

        signal : +1 achat, -1 vente, 0 ne rien faire.
        """
        self.last_price = price

        if signal == 1 and not self.in_position and price > 0:
            self.units = self.cash / price
            self.entry_price = price
            self.cash = 0.0
        elif signal == -1 and self.in_position:
            self.trades.append(
                Trade(entry_price=self.entry_price, exit_price=price, units=self.units)
            )
            self.cash = self.units * price
            self.units = 0.0
            self.entry_price = 0.0

    def summary(self) -> dict:
        """Résumé chiffré du portefeuille."""
        equity = self.equity()
        wins = [t for t in self.trades if t.pnl > 0]
        num = len(self.trades)
        return {
            "capital_initial": self.initial_capital,
            "valeur_actuelle": equity,
            "rendement_pct": (equity / self.initial_capital - 1) * 100,
            "en_position": self.in_position,
            "nombre_trades": num,
            "taux_reussite_pct": (len(wins) / num * 100) if num else 0.0,
        }
