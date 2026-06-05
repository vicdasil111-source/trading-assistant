"""
Gestion du risque.

Deux outils essentiels que tout trader devrait utiliser :
  - le ratio risque/récompense (faut-il prendre ce trade ?) ;
  - la taille de position (combien acheter pour ne risquer qu'un % du capital ?).
"""

from __future__ import annotations


def risk_reward_ratio(entry: float, stop: float, target: float) -> float:
    """
    Ratio récompense / risque d'un trade.

    - entry  : prix d'entrée
    - stop   : prix du stop-loss (où l'on coupe la perte)
    - target : prix cible (take-profit)

    Exemple : entrée 100, stop 90, cible 130 -> récompense 30 / risque 10 = 3.0.
    Un ratio >= 2 est souvent recherché. Lève une erreur si le risque est nul.
    """
    risque = abs(entry - stop)
    if risque == 0:
        raise ValueError("Le risque est nul (entry == stop) : ratio indéfini.")
    recompense = abs(target - entry)
    return recompense / risque


def position_size(
    capital: float,
    risk_pct: float,
    entry: float,
    stop: float,
) -> float:
    """
    Taille de position pour ne risquer qu'un pourcentage donné du capital.

    - capital  : capital total disponible
    - risk_pct : pourcentage du capital à risquer (ex. 1.0 pour 1 %)
    - entry    : prix d'entrée
    - stop     : prix du stop-loss

    Renvoie le nombre d'unités à acheter. Exemple : 1 000 € de capital, risque
    1 %, entrée 100, stop 90 -> on risque 10 € ; perte par unité = 10 ->
    on achète 1 unité.
    """
    perte_par_unite = abs(entry - stop)
    if perte_par_unite == 0:
        raise ValueError("La perte par unité est nulle (entry == stop).")
    montant_risque = capital * (risk_pct / 100)
    return montant_risque / perte_par_unite
