"""
Lance le pilote automatique en BOUCLE (paper trading autonome, 100 % fictif).

Exemples :
    python autopilot_runner.py --symbol BTC/USDT --timeframe 1h --strategy rsi_sma
    python autopilot_runner.py --once          # un seul pas puis on s'arrête
    python autopilot_runner.py --interval 3600 # un pas toutes les heures

Arrête avec Ctrl+C. Aucun ordre réel n'est jamais passé.
"""

from __future__ import annotations

import argparse
import sys
import time

from core.autopilot import Autopilot
from core.strategy import AVAILABLE_STRATEGIES


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Pilote automatique en simulation (boucle).")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--strategy", default="rsi_sma", choices=list(AVAILABLE_STRATEGIES))
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--interval", type=int, default=3600,
                        help="Secondes entre deux pas (défaut 3600 = 1 h)")
    parser.add_argument("--once", action="store_true", help="Faire un seul pas puis quitter")
    args = parser.parse_args()

    bot = Autopilot.load(symbol=args.symbol, timeframe=args.timeframe,
                         strategy=args.strategy, initial_capital=args.capital)

    print(f"🤖 Pilote auto démarré — {args.symbol} ({args.timeframe}), stratégie '{args.strategy}'.")
    print("   100 % simulation. Ctrl+C pour arrêter.\n")

    try:
        while True:
            rapport = bot.step()
            s = bot.status()
            print(f"[{time.strftime('%H:%M:%S')}] +{rapport['bougies_traitees']} bougie(s) | "
                  f"valeur {s['valeur_actuelle']:,.2f} ({s['rendement_pct']:+.1f} %) | "
                  f"{'en position' if s['en_position'] else 'hors marché'}")
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n⏹️  Pilote arrêté. État sauvegardé.")


if __name__ == "__main__":
    main()
