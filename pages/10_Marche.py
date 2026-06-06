"""Page : marché en un coup d'œil (top mouvements). Inspirée des terminaux on-chain."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core import indicators
from core.market_data import fetch_ohlcv
from core.strategy import RsiSmaStrategy
from utils.ui import callout, page_header, start_page

start_page("Marché", icon="🛰️")
page_header("Marché en direct",
            "Les actifs populaires d'un coup d'œil : prix, variation, RSI, tendance et "
            "dernier signal. Repère les plus forts mouvements.", icon="🛰️")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]

with st.sidebar:
    st.header("Paramètres")
    timeframe = st.selectbox("Intervalle", ["1h", "4h", "1d", "1w"], index=2)
    actifs = st.multiselect("Actifs", PAIRES, default=PAIRES)


@st.cache_data(show_spinner="Lecture du marché…", ttl=300)
def _ligne(symbol: str, timeframe: str) -> dict:
    df = fetch_ohlcv(symbol, timeframe, limit=60)
    indicators.add_rsi(df)
    indicators.add_sma(df, window=50)
    df = RsiSmaStrategy().generate_signals(df)
    closes = df["close"].tolist()
    last, prev = closes[-1], closes[-2]
    var1 = (last / prev - 1) * 100
    var7 = (last / closes[-8] - 1) * 100 if len(closes) >= 8 else float("nan")
    sig = {1: "🟢 Achat", -1: "🔴 Vente", 0: "—"}[int(df["signal"].iloc[-1])]
    return {"Actif": symbol, "Prix": round(last, 4), "Var. (1)": round(var1, 2),
            "Var. (7)": round(var7, 2), "RSI": round(float(df["rsi"].iloc[-1]), 1),
            "Tendance": indicators.detect_trend(df), "Signal": sig,
            "Évolution": closes[-20:]}


lignes = []
for sym in actifs:
    try:
        lignes.append(_ligne(sym, timeframe))
    except Exception:
        pass

if not lignes:
    callout("Aucune donnée disponible pour le moment.", tone="warn")
    st.stop()

df = pd.DataFrame(lignes).sort_values("Var. (1)", ascending=False).reset_index(drop=True)

# --- Faits marquants ---
hausse = df.iloc[0]
baisse = df.iloc[-1]
plus_rsi = df.loc[df["RSI"].idxmax()]
c1, c2, c3 = st.columns(3)
c1.metric("🚀 Plus forte hausse", hausse["Actif"], f"{hausse['Var. (1)']:+.2f} %")
c2.metric("📉 Plus forte baisse", baisse["Actif"], f"{baisse['Var. (1)']:+.2f} %")
c3.metric("🔥 RSI le plus haut", plus_rsi["Actif"], f"{plus_rsi['RSI']:.0f}")

# --- Tableau avec sparklines ---
st.subheader("Tous les actifs")
st.dataframe(
    df.set_index("Actif"),
    use_container_width=True,
    column_config={
        "Prix": st.column_config.NumberColumn(format="%.4f"),
        "Var. (1)": st.column_config.NumberColumn("Var. 1 période %", format="%+.2f"),
        "Var. (7)": st.column_config.NumberColumn("Var. 7 périodes %", format="%+.2f"),
        "Évolution": st.column_config.LineChartColumn("20 dernières", width="medium"),
    },
)

callout("Données mises en cache 5 min. « Var. (1) » = variation sur la dernière "
        "bougie de l'intervalle choisi. Aucun conseil, aucune transaction.", tone="info", icon="📌")
