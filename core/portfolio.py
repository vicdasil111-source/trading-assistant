"""
Évaluation d'un portefeuille manuel (calcul pur, testable).

On sépare le calcul (ici) du stockage (core/accounts.py) et de l'affichage
(la page Streamlit). `evaluate` prend des positions et un dictionnaire de prix
courants, et renvoie la valeur, le coût et la plus/moins-value de chaque ligne
ainsi que les totaux.
"""

from __future__ import annotations


def evaluate(holdings: list[dict], prices: dict[str, float]) -> dict:
    """
    - `holdings` : liste de dicts {symbol, quantity, buy_price} (+ éventuel 'id').
    - `prices`   : {symbol: prix_courant}. Une valeur manquante => ligne sans prix.

    Renvoie {rows, total_value, total_cost, total_pnl, total_pnl_pct}.
    """
    rows = []
    total_value = 0.0
    total_cost = 0.0
    for h in holdings:
        qty = float(h["quantity"])
        buy = float(h["buy_price"])
        cost = qty * buy
        total_cost += cost
        price = prices.get(h["symbol"])
        if price is None:
            rows.append({**h, "price": None, "value": None, "pnl": None, "pnl_pct": None})
            continue
        value = qty * price
        pnl = value - cost
        total_value += value
        rows.append({
            **h, "price": price, "value": value, "pnl": pnl,
            "pnl_pct": (value / cost - 1) * 100 if cost else 0.0,
        })

    total_pnl = total_value - total_cost
    return {
        "rows": rows,
        "total_value": total_value,
        "total_cost": total_cost,
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_value / total_cost - 1) * 100 if total_cost else 0.0,
    }
