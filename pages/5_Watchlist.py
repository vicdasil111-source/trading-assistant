"""Page : liste de suivi (watchlist) personnelle. Nécessite un compte."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core import accounts, indicators
from core.market_data import fetch_ohlcv
from core.strategy import RsiSmaStrategy
from utils import account_ui
from utils.ui import callout, page_header, start_page

start_page("Watchlist", icon="⭐")
page_header("Ma liste de suivi",
            "Garde un œil sur tes actifs préférés : prix, RSI, tendance et dernier "
            "signal, d'un coup d'œil.", icon="⭐")

user = account_ui.require_login("ta liste de suivi")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]

# --- Ajout / retrait ---
with st.sidebar:
    st.header("Gérer la liste")
    timeframe = st.selectbox("Intervalle", ["1h", "4h", "1d", "1w"], index=2)
    ajout = st.selectbox("Ajouter un actif", [""] + PAIRES)
    perso = st.text_input("…ou un symbole personnalisé").strip().upper()
    if st.button("➕ Ajouter", use_container_width=True):
        cible = perso or ajout
        if cible:
            accounts.add_watch(user, cible)
            st.rerun()

watch = accounts.get_watchlist(user)

if not watch:
    callout("Ta liste est vide. Ajoute un actif depuis la barre latérale "
            "(ex. <b>BTC/USDT</b>).", tone="info", icon="⭐")
    st.stop()


@st.cache_data(show_spinner="Mise à jour de la liste…", ttl=300)
def _apercu(symbol: str, timeframe: str) -> dict:
    df = fetch_ohlcv(symbol, timeframe, limit=200)
    indicators.add_rsi(df)
    indicators.add_sma(df, window=50)
    df = RsiSmaStrategy().generate_signals(df)
    last = df.iloc[-1]
    perf = (last["close"] / df["close"].iloc[0] - 1) * 100
    sig = {1: "Achat", -1: "Vente", 0: "—"}[int(last["signal"])]
    return {"Prix": round(float(last["close"]), 2), "RSI": round(float(last["rsi"]), 1),
            "Tendance": indicators.detect_trend(df), "Signal": sig,
            "Variation %": round(float(perf), 1)}


lignes = []
for sym in watch:
    try:
        lignes.append({"Actif": sym, **_apercu(sym, timeframe)})
    except Exception:
        lignes.append({"Actif": sym, "Prix": None, "RSI": None,
                       "Tendance": "indisponible", "Signal": "—", "Variation %": None})

st.dataframe(pd.DataFrame(lignes).set_index("Actif"), use_container_width=True)

# --- Retrait ---
col1, col2 = st.columns([3, 1])
a_retirer = col1.selectbox("Retirer un actif", watch)
if col2.button("🗑️ Retirer", use_container_width=True):
    accounts.remove_watch(user, a_retirer)
    st.rerun()

callout("Données rafraîchies au plus toutes les 5 minutes. Aucun ordre réel.",
        tone="info", icon="📌")
