"""
Point d'entrée en ligne de commande (CLI) du Trading Assistant.

Exemples :
    python main.py analyse --symbol BTC/USDT --timeframe 1d
    python main.py backtest --symbol ETH/USDT --strategy rsi_sma --capital 1000
    python main.py backtest --strategy ema_cross

Rappel : aucune exécution d'ordre réel. Tout est analyse et simulation.
"""

from __future__ import annotations

import argparse

from core import indicators
from core.backtest import backtest
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils.config import default_config


def cmd_analyse(args: argparse.Namespace) -> None:
    """Analyse rapide : derniers indicateurs + dernier signal."""
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
    print("\n(Rappel : ceci n'est pas un conseil financier. Aucune exécution réelle.)")


def cmd_backtest(args: argparse.Namespace) -> None:
    """Backtest d'une stratégie sur l'historique."""
    df = fetch_ohlcv(args.symbol, args.timeframe, limit=args.limit)
    strat = get_strategy(args.strategy)
    df = strat.generate_signals(df)

    res = backtest(df, initial_capital=args.capital)
    print(f"\n=== Backtest {args.symbol} ({args.timeframe}) — stratégie '{strat.name}' ===")
    print(res.summary())
    print("\n(Performance passée simulée. Ne garantit rien sur l'avenir.)")


def build_parser() -> argparse.ArgumentParser:
    cfg = default_config
    parser = argparse.ArgumentParser(
        description="Trading Assistant — analyse crypto, backtesting et paper trading (sans argent réel)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def ajouter_args_communs(p: argparse.ArgumentParser) -> None:
        p.add_argument("--symbol", default=cfg.symbol, help="Ex. BTC/USDT")
        p.add_argument("--timeframe", default=cfg.timeframe, help="1m, 1h, 1d, ...")
        p.add_argument("--limit", type=int, default=cfg.limit, help="Nombre de bougies")
        p.add_argument(
            "--strategy",
            default="rsi_sma",
            choices=list(AVAILABLE_STRATEGIES),
            help="Stratégie à utiliser",
        )

    p_analyse = sub.add_parser("analyse", help="Analyse rapide d'un actif")
    ajouter_args_communs(p_analyse)
    p_analyse.set_defaults(func=cmd_analyse)

    p_backtest = sub.add_parser("backtest", help="Tester une stratégie sur l'historique")
    ajouter_args_communs(p_backtest)
    p_backtest.add_argument("--capital", type=float, default=cfg.initial_capital)
    p_backtest.set_defaults(func=cmd_backtest)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
