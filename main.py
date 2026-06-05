"""
Point d'entrée en ligne de commande (CLI) du Trading Assistant.

Exemples :
    python main.py analyse  --symbol BTC/USDT --timeframe 1d --notify
    python main.py backtest --symbol ETH/USDT --strategy rsi_sma --capital 1000 --fee 0.1
    python main.py compare  --symbol BTC/USDT --fee 0.1

Rappel : aucune exécution d'ordre réel. Tout est analyse et simulation.
"""

from __future__ import annotations

import argparse
import sys

from core import indicators
from core.backtest import backtest
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils import notifications
from utils.config import default_config


def cmd_analyse(args: argparse.Namespace) -> None:
    """Analyse rapide : derniers indicateurs + dernier signal (+ alertes)."""
    df = fetch_ohlcv(args.symbol, args.timeframe, limit=args.limit)
    indicators.add_all(df)

    strat = get_strategy(args.strategy)
    df = strat.generate_signals(df)

    derniere = df.iloc[-1]
    tendance = indicators.detect_trend(df)
    signaux = {1: "ACHAT", -1: "VENTE", 0: "NEUTRE"}

    print(f"\n=== Analyse {args.symbol} ({args.timeframe}) ===")
    print(f"Prix de clôture  : {derniere['close']:,.2f}")
    print(f"RSI              : {derniere.get('rsi', float('nan')):.1f}")
    print(f"Tendance         : {tendance}")
    print(f"Stratégie        : {strat.name}")
    print(f"Dernier signal   : {signaux.get(int(derniere['signal']), '?')}")

    alertes = notifications.build_alerts(df)
    if alertes:
        print("\n--- Alertes ---")
        notifications.notify(alertes, use_telegram=args.notify)

    print("\n(Rappel : ceci n'est pas un conseil financier. Aucune exécution réelle.)")


def cmd_backtest(args: argparse.Namespace) -> None:
    """Backtest d'une stratégie sur l'historique."""
    df = fetch_ohlcv(args.symbol, args.timeframe, limit=args.limit)
    strat = get_strategy(args.strategy)
    df = strat.generate_signals(df)

    res = backtest(df, initial_capital=args.capital, fee_pct=args.fee)
    print(f"\n=== Backtest {args.symbol} ({args.timeframe}) — stratégie '{strat.name}' ===")
    print(res.summary())
    print("\n(Performance passée simulée. Ne garantit rien sur l'avenir.)")


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare TOUTES les stratégies sur le même actif."""
    df_base = fetch_ohlcv(args.symbol, args.timeframe, limit=args.limit)
    indicators.add_all(df_base)

    print(f"\n=== Comparaison des stratégies — {args.symbol} ({args.timeframe}) ===")
    entete = f"{'Stratégie':<14}{'Rendement':>12}{'Trades':>8}{'Réussite':>10}{'Sharpe':>8}"
    print(entete)
    print("-" * len(entete))

    lignes = []
    for name in AVAILABLE_STRATEGIES:
        df_sig = get_strategy(name).generate_signals(df_base)
        res = backtest(df_sig, initial_capital=args.capital, fee_pct=args.fee)
        lignes.append((name, res))
        print(f"{name:<14}{res.total_return_pct:>+11.2f}%{res.num_trades:>8}"
              f"{res.win_rate_pct:>9.0f}%{res.sharpe_ratio:>8.2f}")

    # Benchmark Buy & Hold (identique pour toutes les stratégies).
    bh = lignes[0][1].buy_hold_return_pct if lignes else 0.0
    print("-" * len(entete))
    print(f"{'Buy & Hold':<14}{bh:>+11.2f}%")

    meilleure = max(lignes, key=lambda x: x[1].total_return_pct)
    print(f"\n🏆 Meilleure (sur le passé) : '{meilleure[0]}' "
          f"({meilleure[1].total_return_pct:+.2f} %)")
    print("\n(Attention : sur-optimiser sur le passé ne garantit rien sur l'avenir.)")


def build_parser() -> argparse.ArgumentParser:
    cfg = default_config
    parser = argparse.ArgumentParser(
        description="Trading Assistant — analyse crypto, backtesting et paper trading (sans argent réel)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def ajouter_args_communs(p: argparse.ArgumentParser, avec_strategie: bool = True) -> None:
        p.add_argument("--symbol", default=cfg.symbol, help="Ex. BTC/USDT")
        p.add_argument("--timeframe", default=cfg.timeframe, help="1m, 1h, 1d, ...")
        p.add_argument("--limit", type=int, default=cfg.limit, help="Nombre de bougies")
        if avec_strategie:
            p.add_argument("--strategy", default="rsi_sma",
                           choices=list(AVAILABLE_STRATEGIES), help="Stratégie à utiliser")

    p_analyse = sub.add_parser("analyse", help="Analyse rapide d'un actif")
    ajouter_args_communs(p_analyse)
    p_analyse.add_argument("--notify", action="store_true",
                           help="Envoyer aussi les alertes sur Telegram (si configuré)")
    p_analyse.set_defaults(func=cmd_analyse)

    p_backtest = sub.add_parser("backtest", help="Tester une stratégie sur l'historique")
    ajouter_args_communs(p_backtest)
    p_backtest.add_argument("--capital", type=float, default=cfg.initial_capital)
    p_backtest.add_argument("--fee", type=float, default=0.1,
                            help="Frais en %% par transaction (défaut 0.1)")
    p_backtest.set_defaults(func=cmd_backtest)

    p_compare = sub.add_parser("compare", help="Comparer toutes les stratégies")
    ajouter_args_communs(p_compare, avec_strategie=False)
    p_compare.add_argument("--capital", type=float, default=cfg.initial_capital)
    p_compare.add_argument("--fee", type=float, default=0.1,
                           help="Frais en %% par transaction (défaut 0.1)")
    p_compare.set_defaults(func=cmd_compare)

    return parser


def main() -> None:
    # La console Windows utilise par défaut cp1252, qui ne sait pas afficher
    # les emojis (🏆, ✅...). On force l'UTF-8 pour éviter un plantage.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # flux non reconfigurable
        pass

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
