"""
Page : trading automatisé en SIMULATION / TESTNET (argent fictif).

⚠️ Aucune exécution d'ordre avec de l'argent réel. Par défaut, tout est en
« dry-run » (rien n'est envoyé). Le testnet Binance permet d'apprendre la
mécanique d'exécution sans aucun risque.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import execution, indicators
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils.ui import callout, page_header, start_page

start_page("Trading testnet", icon="🤝")
page_header("Trading automatisé (simulation / testnet)",
            "Apprends la mécanique d'un ordre — achat, vente, automatisation sur "
            "signal — sans aucun risque. Argent 100 % fictif.", icon="🤝")

callout("<b>Pas d'argent réel.</b> Par défaut, chaque action est en <b>dry-run</b> "
        "(rien n'est envoyé). Le trading réel autonome n'est pas proposé : un bot qui "
        "achète seul avec de vrais fonds est trop risqué. Ici, on s'entraîne.",
        tone="warn")

keys_ok = bool(os.environ.get("BINANCE_TESTNET_API_KEY") and
               os.environ.get("BINANCE_TESTNET_SECRET"))
if keys_ok:
    callout("Clés testnet détectées : tu peux décocher « dry-run » pour envoyer de "
            "vrais ordres <b>sur le testnet</b> (argent fictif).", tone="info")
else:
    callout("Aucune clé testnet configurée → tout reste en simulation (dry-run). "
            "Pour brancher le testnet : variables <code>BINANCE_TESTNET_API_KEY</code> "
            "et <code>BINANCE_TESTNET_SECRET</code> (clés gratuites sur "
            "testnet.binance.vision).", tone="info")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]

# --- Ordre manuel ---
st.subheader("Passer un ordre")
c1, c2, c3 = st.columns(3)
symbol = c1.selectbox("Actif", PAIRES)
side = c2.selectbox("Sens", ["buy", "sell"], format_func=lambda s: "Acheter" if s == "buy" else "Vendre")
amount = c3.number_input("Quantité", min_value=0.0, value=0.01, step=0.01, format="%.4f")
dry = st.checkbox("Mode simulation (dry-run)", value=True, disabled=not keys_ok)

if st.button("Envoyer l'ordre", type="primary"):
    try:
        res = execution.place_market_order(symbol, side, amount, testnet=True, dry_run=dry or not keys_ok)
        if res.get("dry_run"):
            callout(f"Simulation : ordre <b>{side}</b> de {amount} {symbol} — "
                    f"aucun ordre réellement envoyé.", tone="gain")
        else:
            callout(f"Ordre envoyé sur le testnet : {res}", tone="gain")
    except Exception as exc:
        callout(f"Impossible d'envoyer l'ordre : {exc}", tone="danger")

# --- Auto-trade sur signal ---
st.subheader("Automatisation sur signal")
st.caption("Le bot calcule le dernier signal d'une stratégie et te dit ce qu'il ferait.")
a1, a2 = st.columns(2)
sym2 = a1.selectbox("Actif à suivre", PAIRES, key="auto_sym")
strat = a2.selectbox("Stratégie", list(AVAILABLE_STRATEGIES), key="auto_strat")

if st.button("Calculer le signal et simuler"):
    try:
        df = fetch_ohlcv(sym2, "1d", limit=200)
        indicators.add_all(df)
        df = get_strategy(strat).generate_signals(df)
        sig = int(df["signal"].iloc[-1])
    except Exception as exc:
        callout(f"Données indisponibles : {exc}", tone="warn")
        st.stop()

    libelle = {1: "ACHÈTERAIT 📈", -1: "VENDRAIT 📉", 0: "n'agirait pas (neutre)"}[sig]
    callout(f"Avec la stratégie <b>{strat}</b> sur {sym2}, le bot <b>{libelle}</b> "
            f"maintenant.", tone="info")
    if sig != 0:
        ordre = execution.place_market_order(sym2, "buy" if sig == 1 else "sell",
                                             0.01, testnet=True, dry_run=True)
        callout(f"Simulation de l'ordre correspondant : {ordre['side']} "
                f"{ordre['amount']} {sym2} (dry-run, rien d'envoyé).", tone="gain")

callout("Pour une vraie autonomie en simulation continue, vois la page "
        "<b>Pilote auto</b> (portefeuille fictif qui décide seul).", tone="info", icon="🤖")
