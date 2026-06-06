"""
Page : Aide & FAQ — sécurité, légal, fiscalité, données personnelles.

But : informer clairement avant d'utiliser l'automatisation d'ordres, et rester
conforme (avertissements, non-conseil, cadre AMF/MiCA, fiscalité, RGPD).
Ceci est une information générale, pas un conseil juridique ou financier.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from utils.ui import callout, page_header, start_page

start_page("Aide & FAQ", icon="❓")
page_header("Aide, sécurité & informations légales",
            "Tout ce qu'il faut comprendre avant d'automatiser des ordres : risques, "
            "légalité, fiscalité, protection de tes clés et de tes données.", icon="❓")

callout("<b>Information générale, pas un conseil.</b> Ce projet est éducatif. Rien "
        "ici n'est un conseil en investissement, juridique ou fiscal. En cas de "
        "doute, consulte un professionnel agréé.", tone="warn")

# --- Risques ----------------------------------------------------------------
st.subheader("⚠️ Risques")
with st.expander("Quel est le risque de l'automatisation d'achats ?", expanded=True):
    st.markdown(
        "- Le marché crypto est **très volatil** : tu peux perdre **tout** ton capital, vite.\n"
        "- Un **bot qui achète seul** (autopilote) peut enchaîner des pertes sans que "
        "tu interviennes — y compris la nuit.\n"
        "- La **performance passée** (backtest) **ne garantit pas** les résultats futurs. "
        "Un backtest flatteur peut être du sur-apprentissage.\n"
        "- Des **bugs**, une **coupure réseau** ou une **panne d'exchange** peuvent "
        "provoquer des ordres ratés ou en double.\n\n"
        "👉 Règle d'or : **n'engage que ce que tu peux te permettre de perdre**, "
        "commence en **simulation**, puis **testnet**, et garde des **garde-fous** serrés.")

with st.expander("Quels garde-fous le bot applique-t-il ?"):
    st.markdown(
        "Avant **chaque ordre réel**, l'app vérifie :\n"
        "- un **plafond par ordre** (en USDT),\n"
        "- une **perte maximale par jour**,\n"
        "- un **nombre maximal d'ordres par jour**,\n"
        "- un **coupe-circuit** (bouton d'arrêt d'urgence) qui bloque tout.\n\n"
        "Si une limite est franchie, l'ordre est **refusé**. La simulation et le "
        "testnet ne sont pas bridés (aucun argent réel en jeu).")

# --- Argent & clés ----------------------------------------------------------
st.subheader("🔑 Ton argent et tes clés")
with st.expander("Le bot détient-il mon argent ?"):
    st.markdown(
        "**Non.** Tes fonds restent **sur ton exchange** (ex. Binance). L'app ne fait "
        "qu'envoyer des ordres via l'API. Elle ne conserve pas ton argent.")

with st.expander("Comment protéger mes clés API ?", expanded=True):
    st.markdown(
        "- Crée des clés **« trading » uniquement**, **sans droit de retrait** "
        "(withdrawal). Ainsi, même compromise, une clé ne peut pas vider ton compte.\n"
        "- Restreins-les par **adresse IP** si possible.\n"
        "- Mets-les dans des **variables d'environnement**, **jamais** dans le code ni "
        "sur GitHub (`.gitignore` protège déjà `.env`).\n"
        "- **N'entre jamais** tes clés réelles sur un site **public partagé**. C'est "
        "pourquoi le trading réel n'est déverrouillé **qu'en auto-hébergement**.\n\n"
        "_Rappel : en 2022, une fuite de 150 000 clés API chez un grand bot a montré "
        "que même les gros acteurs se font pirater. Des clés sans retrait limitent la casse._")

with st.expander("Comment activer le trading réel (en local) ?"):
    st.markdown(
        "Sur **ta** machine uniquement :\n"
        "```powershell\n"
        "$env:BINANCE_API_KEY = \"ta_cle\"          # trading seulement, sans retrait\n"
        "$env:BINANCE_SECRET  = \"ton_secret\"\n"
        "$env:I_UNDERSTAND_REAL_MONEY_RISK = \"yes\"  # garde-fou anti-accident\n"
        "streamlit run dashboard.py\n"
        "```\n"
        "Pour t'entraîner **sans risque**, préfère le **testnet** : clés gratuites sur "
        "testnet.binance.vision, variables `BINANCE_TESTNET_API_KEY` / `BINANCE_TESTNET_SECRET`.")

# --- Légal ------------------------------------------------------------------
st.subheader("⚖️ Cadre légal (France / UE)")
with st.expander("Est-ce légal d'utiliser ce bot ?", expanded=True):
    st.markdown(
        "Utiliser un outil **pour ton propre compte**, avec **ton propre argent**, est "
        "généralement **licite**. Ce que la loi encadre, c'est le fait de **fournir un "
        "service de crypto-actifs à des tiers** (échange, conservation, courtage…).\n\n"
        "En Europe, le règlement **MiCA** impose un agrément **CASP/PSAN** délivré, en "
        "France, par l'**AMF**, pour qui fournit ces services **à titre professionnel**. "
        "La période transitoire pour les acteurs français **se termine le 1ᵉʳ juillet 2026**.\n\n"
        "👉 Concrètement : pour un **usage personnel**, pas d'agrément requis. En "
        "revanche, si tu **proposes ce bot comme service** à d'autres (gestion de "
        "leurs fonds, exécution pour eux…), tu entres dans un cadre **réglementé** — "
        "renseigne-toi auprès de l'AMF avant.")

with st.expander("Est-ce un conseil en investissement ?"):
    st.markdown(
        "**Non.** Les signaux, backtests et automatisations sont des **outils "
        "techniques**, pas des recommandations personnalisées. Le conseil en "
        "investissement est une activité **réglementée** ; ce projet ne la fournit pas.")

# --- Fiscalité --------------------------------------------------------------
st.subheader("🧾 Fiscalité (France)")
with st.expander("Dois-je payer des impôts sur mes gains ?"):
    st.markdown(
        "En France, les **plus-values** de cessions de crypto par un particulier sont "
        "**imposables** (régime du **prélèvement forfaitaire unique**, dit « flat tax », "
        "**30 %** — option possible pour le barème). Tu dois aussi **déclarer tes "
        "comptes d'actifs numériques** détenus à l'étranger (formulaire **3916-bis**).\n\n"
        "- **Garde une trace** de toutes tes opérations (dates, montants, frais).\n"
        "- Les seuils et règles évoluent : vérifie sur **impots.gouv.fr** ou auprès "
        "d'un expert-comptable.\n\n"
        "_Information générale, pas un conseil fiscal._")

# --- Données personnelles ---------------------------------------------------
st.subheader("🔒 Données personnelles (RGPD)")
with st.expander("Quelles données sont stockées ?"):
    st.markdown(
        "Si tu crées un **compte** : ton identifiant, un e-mail (facultatif), et un "
        "**mot de passe haché** (PBKDF2 + sel — jamais en clair). Plus tes listes "
        "perso (watchlist, portefeuille, alertes, préférences).\n\n"
        "- Les mots de passe ne sont **jamais** stockés en clair.\n"
        "- Tu peux demander la **suppression** de ton compte et de tes données.\n"
        "- Aucune **clé API** n'est stockée par l'app : elles vivent uniquement dans "
        "tes variables d'environnement, sur ta machine.")

# --- Autopilote -------------------------------------------------------------
st.subheader("🤖 Autopilote")
with st.expander("Le bot peut-il vraiment acheter tout seul ?"):
    st.markdown(
        "Oui, **si tu le décides explicitement** : en auto-hébergement, avec tes clés "
        "réelles, après avoir accepté les risques et armé l'autopilote. Par défaut, "
        "tout est **désactivé** et en **simulation**. Tu disposes en plus d'un "
        "**coupe-circuit** pour tout stopper instantanément.\n\n"
        "Pour un autopilote **continu (24/7)**, on le lance en local : "
        "`python autopilot_runner.py` (simulation par défaut).")

st.divider()
callout("Des questions, un bug, une demande de suppression de données ? Ouvre une "
        "« issue » sur le dépôt GitHub du projet.", tone="info")

st.caption("Sources réglementaires : Autorité des marchés financiers (AMF) — "
           "dossier MiCA ; impots.gouv.fr pour la fiscalité des actifs numériques. "
           "Dernière mise à jour de cette page : juin 2026.")
