"""
Notifications / alertes.

Deux canaux :
  - Console (toujours disponible, par défaut).
  - Telegram (optionnel) : actif uniquement si les variables d'environnement
    TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID sont définies. Aucune clé n'est
    stockée dans le code.

La fonction `build_alerts` examine la dernière bougie et renvoie une liste de
messages d'alerte lisibles (RSI extrême, dernier signal, etc.).
"""

from __future__ import annotations

import os

import pandas as pd

from utils.config import Config, default_config
from utils.logger import get_logger

logger = get_logger(__name__)


def build_alerts(df: pd.DataFrame, config: Config | None = None) -> list[str]:
    """
    Construit la liste des alertes à partir de la dernière ligne du DataFrame.

    Le DataFrame est censé contenir au moins 'close' et 'rsi' ; 'signal' est
    utilisé s'il est présent.
    """
    cfg = config or default_config
    if df.empty:
        return []

    derniere = df.iloc[-1]
    alertes: list[str] = []

    rsi = derniere.get("rsi")
    if rsi is not None and not pd.isna(rsi):
        if rsi >= cfg.rsi_overbought:
            alertes.append(f"⚠️ RSI {rsi:.1f} — zone de SURACHAT (> {cfg.rsi_overbought:.0f}).")
        elif rsi <= cfg.rsi_oversold:
            alertes.append(f"💡 RSI {rsi:.1f} — zone de SURVENTE (< {cfg.rsi_oversold:.0f}).")

    if "signal" in df.columns:
        sig = int(derniere["signal"])
        libelle = {1: "ACHAT 📈", -1: "VENTE 📉"}.get(sig)
        if libelle:
            alertes.append(f"🔔 Signal de la stratégie : {libelle} "
                           f"(prix {derniere['close']:,.2f}).")

    return alertes


def send_console(message: str) -> None:
    """Affiche une notification dans la console."""
    print(f"[ALERTE] {message}")


def send_telegram(message: str) -> bool:
    """
    Envoie un message via Telegram si configuré (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID).

    Renvoie True si envoyé, False si Telegram n'est pas configuré ou en cas d'erreur.
    Ne lève pas d'exception : une notification ne doit jamais faire planter l'app.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        import urllib.parse
        import urllib.request

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
        with urllib.request.urlopen(url, data=data, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:  # réseau, token invalide...
        logger.warning("Échec de l'envoi Telegram : %s", exc)
        return False


def notify(messages: list[str], use_telegram: bool = True) -> None:
    """Diffuse une liste de messages sur les canaux disponibles."""
    for msg in messages:
        send_console(msg)
        if use_telegram:
            send_telegram(msg)
