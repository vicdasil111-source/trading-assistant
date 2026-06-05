"""
Backtesting : rejouer une stratégie sur des données historiques.

Modèle simple et pédagogique : long-only, "tout ou rien".
  - Sur un signal d'ACHAT (+1) et sans position : on investit tout le cash.
  - Sur un signal de VENTE (-1) et avec une position : on revend tout.
  - Une position encore ouverte à la fin est clôturée au dernier prix.

Ce n'est pas un moteur de backtest professionnel (pas de frais, pas de
slippage, pas de positions partielles), mais il est juste, lisible et
suffisant pour comparer des stratégies. Les frais peuvent être ajoutés plus tard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class BacktestResult:
    """Résultat d'un backtest, avec les métriques clés."""

    initial_capital: float
    final_equity: float
    total_return_pct: float
    num_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    trades: list[float] = field(default_factory=list)   # P&L de chaque trade clôturé
    equity_curve: list[float] = field(default_factory=list)

    def summary(self) -> str:
        """Résumé lisible en français."""
        return (
            f"Capital initial   : {self.initial_capital:,.2f}\n"
            f"Capital final     : {self.final_equity:,.2f}\n"
            f"Rendement total   : {self.total_return_pct:+.2f} %\n"
            f"Nombre de trades  : {self.num_trades}\n"
            f"Taux de réussite  : {self.win_rate_pct:.1f} %\n"
            f"Profit factor     : {self.profit_factor:.2f}\n"
            f"Drawdown max      : {self.max_drawdown_pct:.2f} %"
        )


def _max_drawdown_pct(equity_curve: list[float]) -> float:
    """Plus forte baisse depuis un sommet, en %. Renvoie une valeur <= 0."""
    peak = float("-inf")
    max_dd = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            drawdown = (equity - peak) / peak * 100
            max_dd = min(max_dd, drawdown)
    return max_dd


def backtest(df: pd.DataFrame, initial_capital: float = 1000.0) -> BacktestResult:
    """
    Rejoue la colonne `signal` du DataFrame sur la colonne `close`.

    Le DataFrame doit contenir les colonnes 'close' et 'signal'.
    """
    if "signal" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'signal'. "
                         "Génère-la d'abord avec une stratégie.")
    if "close" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'close'.")

    cash = float(initial_capital)
    units = 0.0            # quantité d'actif détenue
    entry_price = 0.0      # prix d'entrée de la position courante
    trades: list[float] = []
    equity_curve: list[float] = []

    for price, signal in zip(df["close"], df["signal"]):
        if signal == 1 and units == 0 and price > 0:
            # On achète tout.
            units = cash / price
            entry_price = price
            cash = 0.0
        elif signal == -1 and units > 0:
            # On revend tout et on enregistre le P&L du trade.
            proceeds = units * price
            pnl = proceeds - units * entry_price
            trades.append(pnl)
            cash = proceeds
            units = 0.0
            entry_price = 0.0

        equity_curve.append(cash + units * price)

    # Clôture d'une éventuelle position encore ouverte, au dernier prix.
    if units > 0:
        last_price = float(df["close"].iloc[-1])
        proceeds = units * last_price
        pnl = proceeds - units * entry_price
        trades.append(pnl)
        cash = proceeds
        units = 0.0
        equity_curve[-1] = cash

    final_equity = equity_curve[-1] if equity_curve else float(initial_capital)
    total_return_pct = (final_equity / initial_capital - 1) * 100

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t < 0]
    num_trades = len(trades)
    win_rate_pct = (len(wins) / num_trades * 100) if num_trades else 0.0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    if gross_loss == 0:
        profit_factor = float("inf") if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    return BacktestResult(
        initial_capital=float(initial_capital),
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        num_trades=num_trades,
        win_rate_pct=win_rate_pct,
        profit_factor=profit_factor,
        max_drawdown_pct=_max_drawdown_pct(equity_curve),
        trades=trades,
        equity_curve=equity_curve,
    )
