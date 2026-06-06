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


def account_mode() -> dict:
    """Décrit ce qui est possible selon l'environnement (clés + acceptation du risque).

    Sert à l'interface pour n'autoriser le trading réel que si TOUT est réuni.
    Sur le site public partagé, aucune de ces variables n'est définie : on reste
    donc en simulation/testnet, par conception.
    """
    testnet_keys = bool(os.environ.get("BINANCE_TESTNET_API_KEY")
                        and os.environ.get("BINANCE_TESTNET_SECRET"))
    real_keys = bool(os.environ.get("BINANCE_API_KEY")
                     and os.environ.get("BINANCE_SECRET"))
    real_unlocked = os.environ.get("I_UNDERSTAND_REAL_MONEY_RISK") == "yes"
    return {
        "testnet_keys": testnet_keys,
        "real_keys": real_keys,
        "real_unlocked": real_unlocked,
        # Le réel n'est « disponible » que si les clés réelles ET l'acceptation
        # explicite du risque sont présentes côté serveur.
        "real_available": real_keys and real_unlocked,
    }


def place_market_order(
    symbol: str,
    side: str,
    amount: float,
    testnet: bool = True,
    dry_run: bool = True,
    *,
    order_value_usdt: float | None = None,
    guardrails=None,
) -> dict:
    """
    Passe un ordre au marché.

    - `dry_run=True` (défaut) : n'envoie RIEN, renvoie juste une simulation.
    - Pour réellement envoyer (sur testnet), il faut explicitement dry_run=False.
    - `testnet=False` (réseau réel) exige en plus :
        * la variable d'environnement I_UNDERSTAND_REAL_MONEY_RISK="yes",
        * le coupe-circuit (kill switch) inactif,
        * le respect des garde-fous (taille d'ordre, pertes/jour, ordres/jour) ;
          `order_value_usdt` doit alors être fourni (sinon refus par sécurité).
    """
    side = side.lower()
    if side not in ("buy", "sell"):
        raise ValueError("side doit être 'buy' ou 'sell'.")

    reel = (not dry_run) and (not testnet)
    if reel:
        # 1) Acceptation explicite du risque (garde-fou anti-accident).
        if os.environ.get("I_UNDERSTAND_REAL_MONEY_RISK") != "yes":
            raise RuntimeError(
                "Refus de passer un ordre RÉEL. Pour autoriser le trading réel, "
                "tu dois définir I_UNDERSTAND_REAL_MONEY_RISK=yes — et bien "
                "comprendre que tu peux perdre ton argent."
            )
        # 2) Garde-fous durs (coupe-circuit + limites).
        from core import trading_guard as tg

        g = guardrails or tg.Guardrails()
        stats = tg.today_stats()
        tg.validate_order(
            g,
            order_value_usdt=order_value_usdt if order_value_usdt is not None else 0.0,
            trades_today=int(stats.get("trades", 0)),
            loss_today_usdt=float(stats.get("loss", 0.0)),
            kill_switch=tg.kill_switch_active(),
        )

    if dry_run:
        logger.info("[DRY-RUN] %s %s %s (testnet=%s) — aucun ordre envoyé.",
                    side, amount, symbol, testnet)
        return {"dry_run": True, "symbol": symbol, "side": side,
                "amount": amount, "testnet": testnet, "status": "simulé"}

    exchange = get_exchange(testnet)
    if side == "buy":
        res = exchange.create_market_buy_order(symbol, amount)
    else:
        res = exchange.create_market_sell_order(symbol, amount)

    if reel:
        # Comptabilise l'ordre réel pour faire respecter les limites du jour.
        from core import trading_guard as tg

        try:
            tg.record_trade(order_value_usdt or 0.0)
        except Exception:  # ne jamais faire échouer un ordre déjà passé
            logger.warning("Ordre réel passé mais non journalisé.", exc_info=True)
    return res
