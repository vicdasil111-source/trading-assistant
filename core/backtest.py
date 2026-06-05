"""
Backtesting : rejouer une stratégie sur des données historiques.

Modèle simple et pédagogique : long-only, "tout ou rien".
  - Sur un signal d'ACHAT (+1) et sans position : on investit tout le cash.
  - Sur un signal de VENTE (-1) et avec une position : on revend tout.
  - Une position encore ouverte à la fin est clôturée au dernier prix.

Réalisme ajouté :
  - Frais de transaction (`fee_pct`) appliqués à chaque achat et vente.
  - Comparaison avec une stratégie "Buy & Hold" (acheter au début, garder).
  - Ratio de Sharpe (rendement ajusté du risque).

Ce n'est pas un moteur professionnel (pas de slippage, pas de positions
partielles), mais il est juste, lisible et suffisant pour comparer des stratégies.
"""

from __future__ import annotations

import math
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
    buy_hold_return_pct: float = 0.0   # rendement si on avait juste gardé l'actif
    sharpe_ratio: float = 0.0          # rendement ajusté du risque (par bougie)
    total_fees: float = 0.0            # total des frais payés
    trades: list[float] = field(default_factory=list)   # P&L de chaque trade clôturé
    equity_curve: list[float] = field(default_factory=list)

    @property
    def beats_buy_hold(self) -> bool:
        """La stratégie a-t-elle fait mieux que "acheter et garder" ?"""
        return self.total_return_pct > self.buy_hold_return_pct

    def summary(self) -> str:
        """Résumé lisible en français."""
        verdict = "✅ mieux que Buy & Hold" if self.beats_buy_hold else "❌ moins bien que Buy & Hold"
        return (
            f"Capital initial   : {self.initial_capital:,.2f}\n"
            f"Capital final     : {self.final_equity:,.2f}\n"
            f"Rendement total   : {self.total_return_pct:+.2f} %\n"
            f"Buy & Hold        : {self.buy_hold_return_pct:+.2f} %  ({verdict})\n"
            f"Nombre de trades  : {self.num_trades}\n"
            f"Taux de réussite  : {self.win_rate_pct:.1f} %\n"
            f"Profit factor     : {self.profit_factor:.2f}\n"
            f"Ratio de Sharpe   : {self.sharpe_ratio:.2f}\n"
            f"Drawdown max      : {self.max_drawdown_pct:.2f} %\n"
            f"Frais payés       : {self.total_fees:,.2f}"
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


def _sharpe_ratio(equity_curve: list[float]) -> float:
    """
    Ratio de Sharpe simplifié (sans taux sans risque, par bougie).

    = moyenne des rendements / écart-type des rendements.
    Plus c'est élevé, meilleur est le rendement par unité de risque.
    Renvoie 0 si l'écart-type est nul ou s'il y a trop peu de points.
    """
    if len(equity_curve) < 2:
        return 0.0
    returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, len(equity_curve))
        if equity_curve[i - 1] != 0
    ]
    if len(returns) < 2:
        return 0.0
    moyenne = sum(returns) / len(returns)
    variance = sum((r - moyenne) ** 2 for r in returns) / (len(returns) - 1)
    ecart_type = math.sqrt(variance)
    if ecart_type == 0:
        return 0.0
    return moyenne / ecart_type


def backtest(
    df: pd.DataFrame,
    initial_capital: float = 1000.0,
    fee_pct: float = 0.0,
) -> BacktestResult:
    """
    Rejoue la colonne `signal` du DataFrame sur la colonne `close`.

    - `fee_pct` : frais en pourcentage appliqués à chaque achat et chaque vente
      (ex. 0.1 pour 0,1 %, ce qui est typique sur Binance).

    Le DataFrame doit contenir les colonnes 'close' et 'signal'.
    """
    if "signal" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'signal'. "
                         "Génère-la d'abord avec une stratégie.")
    if "close" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'close'.")

    fee_rate = fee_pct / 100.0
    cash = float(initial_capital)
    units = 0.0            # quantité d'actif détenue
    entry_price = 0.0      # prix d'entrée de la position courante
    trades: list[float] = []
    equity_curve: list[float] = []
    total_fees = 0.0

    for price, signal in zip(df["close"], df["signal"]):
        if signal == 1 and units == 0 and price > 0:
            # On achète tout (frais déduits du cash investi).
            fee = cash * fee_rate
            total_fees += fee
            units = (cash - fee) / price
            entry_price = price
            cash = 0.0
        elif signal == -1 and units > 0:
            # On revend tout (frais déduits du produit de la vente).
            gross = units * price
            fee = gross * fee_rate
            total_fees += fee
            proceeds = gross - fee
            pnl = proceeds - units * entry_price
            trades.append(pnl)
            cash = proceeds
            units = 0.0
            entry_price = 0.0

        equity_curve.append(cash + units * price)

    # Clôture d'une éventuelle position encore ouverte, au dernier prix.
    if units > 0:
        last_price = float(df["close"].iloc[-1])
        gross = units * last_price
        fee = gross * fee_rate
        total_fees += fee
        proceeds = gross - fee
        pnl = proceeds - units * entry_price
        trades.append(pnl)
        cash = proceeds
        units = 0.0
        equity_curve[-1] = cash

    final_equity = equity_curve[-1] if equity_curve else float(initial_capital)
    total_return_pct = (final_equity / initial_capital - 1) * 100

    # Benchmark Buy & Hold : acheter à la première bougie, garder jusqu'au bout.
    premier = float(df["close"].iloc[0])
    dernier = float(df["close"].iloc[-1])
    buy_hold_return_pct = (dernier / premier - 1) * 100 if premier > 0 else 0.0

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
        buy_hold_return_pct=buy_hold_return_pct,
        sharpe_ratio=_sharpe_ratio(equity_curve),
        total_fees=total_fees,
        trades=trades,
        equity_curve=equity_curve,
    )
