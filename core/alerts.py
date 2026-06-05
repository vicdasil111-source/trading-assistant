"""
Alertes de prix / RSI (logique pure, testable).

Une alerte se déclenche quand une condition est vérifiée sur les données
courantes. Quatre types : prix au-dessus / en dessous d'un seuil, RSI au-dessus /
en dessous d'un seuil.
"""

from __future__ import annotations

KINDS = {
    "price_above": "Prix ≥",
    "price_below": "Prix ≤",
    "rsi_above": "RSI ≥",
    "rsi_below": "RSI ≤",
}


def is_triggered(kind: str, threshold: float, price: float, rsi: float) -> bool:
    """Renvoie True si l'alerte doit se déclencher pour ces valeurs courantes."""
    if kind == "price_above":
        return price >= threshold
    if kind == "price_below":
        return price <= threshold
    if kind == "rsi_above":
        return rsi >= threshold
    if kind == "rsi_below":
        return rsi <= threshold
    raise ValueError(f"Type d'alerte inconnu : {kind!r}")


def describe(symbol: str, kind: str, threshold: float) -> str:
    """Libellé lisible d'une alerte, ex. 'BTC/USDT — Prix ≥ 70000'."""
    if kind not in KINDS:
        raise ValueError(f"Type d'alerte inconnu : {kind!r}")
    return f"{symbol} — {KINDS[kind]} {threshold:g}"
