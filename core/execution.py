"""
Exécution d'ordres sur le TESTNET Binance (argent FICTIF).

⚠️ GARDE-FOUS — à lire :
  - Par défaut, tout est en `dry_run` (aucun ordre n'est réellement envoyé,
    on se contente d'afficher ce qui serait fait).
  - `testnet=True` par défaut : on ne parle qu'au réseau de TEST de Binance,
    où l'argent est fictif. Le réseau réel n'est JAMAIS utilisé par défaut.
  - Aucune clé n'est stockée dans le code : on lit des variables d'environnement.
  - Ce module n'est PAS branché au pilote automatique : aucune exécution n'est
    déclenchée toute seule. C'est un outil manuel d'apprentissage.

Clés testnet (gratuites) : https://testnet.binance.vision/
    $env:BINANCE_TESTNET_API_KEY = "..."
    $env:BINANCE_TESTNET_SECRET  = "..."
"""

from __future__ import annotations

import os

from utils.logger import get_logger

logger = get_logger(__name__)


def _get_keys(testnet: bool) -> tuple[str, str]:
    if testnet:
        key = os.environ.get("BINANCE_TESTNET_API_KEY")
        secret = os.environ.get("BINANCE_TESTNET_SECRET")
        nom = "BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_SECRET"
    else:
        key = os.environ.get("BINANCE_API_KEY")
        secret = os.environ.get("BINANCE_SECRET")
        nom = "BINANCE_API_KEY / BINANCE_SECRET"
    if not key or not secret:
        raise RuntimeError(
            f"Clés manquantes : définis les variables d'environnement {nom}. "
            f"Pour le testnet (recommandé), crée-les sur https://testnet.binance.vision/"
        )
    return key, secret


def get_exchange(testnet: bool = True):
    """Crée une connexion ccxt. testnet=True -> réseau de test (argent fictif)."""
    import ccxt

    key, secret = _get_keys(testnet)
    exchange = ccxt.binance({"apiKey": key, "secret": secret, "enableRateLimit": True})
    if testnet:
        exchange.set_sandbox_mode(True)  # bascule sur le réseau de test
    return exchange


def fetch_balance(testnet: bool = True) -> dict:
    """Renvoie le solde (fictif sur testnet)."""
    exchange = get_exchange(testnet)
    return exchange.fetch_balance()


def place_market_order(
    symbol: str,
    side: str,
    amount: float,
    testnet: bool = True,
    dry_run: bool = True,
) -> dict:
    """
    Passe un ordre au marché.

    - `dry_run=True` (défaut) : n'envoie RIEN, renvoie juste une simulation.
    - Pour réellement envoyer (sur testnet), il faut explicitement dry_run=False.
    - `testnet=False` (réseau réel) exige en plus la variable d'environnement
      I_UNDERSTAND_REAL_MONEY_RISK="yes" : un garde-fou contre les accidents.
    """
    side = side.lower()
    if side not in ("buy", "sell"):
        raise ValueError("side doit être 'buy' ou 'sell'.")

    if dry_run:
        logger.info("[DRY-RUN] %s %s %s (testnet=%s) — aucun ordre envoyé.",
                    side, amount, symbol, testnet)
        return {"dry_run": True, "symbol": symbol, "side": side,
                "amount": amount, "testnet": testnet, "status": "simulé"}

    if not testnet and os.environ.get("I_UNDERSTAND_REAL_MONEY_RISK") != "yes":
        raise RuntimeError(
            "Refus de passer un ordre RÉEL. Le trading réel autonome n'est pas "
            "supporté. Pour un ordre réel manuel, tu dois définir "
            "I_UNDERSTAND_REAL_MONEY_RISK=yes — et bien comprendre le risque."
        )

    exchange = get_exchange(testnet)
    if side == "buy":
        return exchange.create_market_buy_order(symbol, amount)
    return exchange.create_market_sell_order(symbol, amount)
