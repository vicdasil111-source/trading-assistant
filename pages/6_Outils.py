"""Page : outils de trading (gestion du risque). Pas de compte requis."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core.risk import position_size, risk_reward_ratio
from utils.ui import callout, page_header, start_page

start_page("Outils", icon="🧮")
page_header("Outils de gestion du risque",
            "Avant tout trade : combien acheter pour ne risquer qu'un petit pourcentage "
            "de ton capital, et le trade en vaut-il la peine ?", icon="🧮")

st.subheader("Calculateur de taille de position")
c1, c2 = st.columns(2)
with c1:
    capital = st.number_input("Capital total", min_value=1.0, value=1000.0, step=100.0)
    risque_pct = st.number_input("Risque par trade (%)", min_value=0.1, value=1.0, step=0.5)
with c2:
    entree = st.number_input("Prix d'entrée", min_value=0.0, value=100.0, step=1.0)
    stop = st.number_input("Stop-loss", min_value=0.0, value=90.0, step=1.0)
cible = st.number_input("Objectif (take-profit)", min_value=0.0, value=130.0, step=1.0)

try:
    unites = position_size(capital, risque_pct, entree, stop)
    montant_risque = capital * risque_pct / 100
    valeur_position = unites * entree
    rr = risk_reward_ratio(entree, stop, cible)
    gain_pot = abs(cible - entree) * unites
    perte_pot = abs(entree - stop) * unites

    m = st.columns(4)
    m[0].metric("Unités à acheter", f"{unites:,.4f}")
    m[1].metric("Valeur de la position", f"{valeur_position:,.2f}")
    m[2].metric("Montant risqué", f"{montant_risque:,.2f}")
    m[3].metric("Ratio risque/récompense", f"{rr:.2f}")

    g = st.columns(2)
    g[0].metric("Gain potentiel", f"+{gain_pot:,.2f}")
    g[1].metric("Perte potentielle", f"-{perte_pot:,.2f}")

    if rr >= 2:
        callout(f"Bon ratio ({rr:.1f}) : tu vises au moins le double de ce que tu "
                f"risques. C'est un repère sain.", tone="gain")
    elif rr < 1:
        callout(f"Ratio faible ({rr:.1f}) : tu risques plus que ce que tu peux gagner. "
                f"À éviter en général.", tone="warn")
    else:
        callout(f"Ratio correct ({rr:.1f}). Beaucoup de traders visent ≥ 2.", tone="info")
except ValueError as exc:
    callout(str(exc), tone="warn")

with st.expander("📖 Comment ça marche ?"):
    st.markdown(
        "- **Taille de position** : on calcule combien d'unités acheter pour que, si "
        "le stop-loss est touché, tu ne perdes que le pourcentage choisi de ton capital.\n"
        "- **Risque/récompense** : (objectif − entrée) ÷ (entrée − stop). Un ratio de 2 "
        "signifie que tu vises un gain deux fois plus grand que ta perte possible.\n"
        "- Règle d'or : risquer peu par trade (souvent 1 %) permet d'encaisser une série "
        "de pertes sans couler le compte."
    )
