"""Page : pilote automatique (paper trading autonome, 100 % fictif)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core.autopilot import DEFAULT_STATE_PATH, Autopilot
from core.strategy import AVAILABLE_STRATEGIES
from utils.ui import callout, page_header, setup_page

setup_page("Pilote auto", icon="🤖")
page_header(
    "Pilote automatique",
    "Un portefeuille fictif qui décide tout seul à chaque bougie. Son état est "
    "sauvegardé entre les sessions. Aucun argent réel.",
    icon="🤖",
)

with st.sidebar:
    st.header("Configuration")
    existe = DEFAULT_STATE_PATH.exists()
    if existe:
        st.success("Un pilote est déjà en cours. Clique « Avancer ».")
    symbol = st.text_input("Actif", value="BTC/USDT", disabled=existe)
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2, disabled=existe)
    strategy = st.selectbox("Stratégie", list(AVAILABLE_STRATEGIES), disabled=existe)
    capital = st.number_input("Capital fictif", min_value=10.0, value=1000.0, step=100.0, disabled=existe)

col_a, col_b = st.columns(2)
avancer = col_a.button("▶️ Avancer (traiter les nouvelles bougies)", type="primary")
reinit = col_b.button("🔄 Réinitialiser le pilote")

bot = Autopilot.load(symbol=symbol, timeframe=timeframe, strategy=strategy, initial_capital=capital)

if reinit:
    bot.reset()
    st.toast("Pilote réinitialisé.")

if avancer:
    try:
        with st.spinner("Le pilote analyse le marché..."):
            rapport = bot.step()
        st.toast(f"{rapport['bougies_traitees']} bougie(s) traitée(s).")
    except Exception as exc:
        st.error(f"Erreur pendant le pas : {exc}")

# --- État courant ---
status = bot.status()
st.subheader("État du portefeuille")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valeur actuelle", f"{status['valeur_actuelle']:,.2f}")
c2.metric("Rendement", f"{status['rendement_pct']:+.1f} %")
c3.metric("En position ?", "Oui 📈" if status["en_position"] else "Non 💵")
c4.metric("Trades", status["nombre_trades"])
st.caption(f"Actif : {status['symbol']} · Stratégie : {status['strategy']} · "
           f"{status['bougies_vues']} bougies vues")

# --- Historique ---
if bot.state.history:
    hist = pd.DataFrame(bot.state.history)
    st.subheader("Évolution du capital (fictif)")
    st.line_chart(hist.set_index("time")["equity"])
    with st.expander("Voir le journal détaillé"):
        st.dataframe(hist[::-1], use_container_width=True)
else:
    callout("Clique sur <b>Avancer</b> pour démarrer : le pilote ingérera "
            "l'historique puis suivra le marché.", tone="info", icon="▶️")

callout("Tout est simulé : le pilote ne passe aucun ordre réel. Pour une vraie "
        "autonomie temps réel, on lance ce pas en boucle "
        "(CLI : <code>python autopilot_runner.py</code>).", tone="info", icon="📌")
