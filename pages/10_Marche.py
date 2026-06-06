"""Page : marché en un coup d'œil (top mouvements). Inspirée des terminaux on-chain."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core import indicators
from core.market_data import fetch_ohlcv
from core.strategy import RsiSmaStrategy
from utils.ui import callout, market_grid, page_header, section, start_page

C = start_page("Marché", icon="🛰️")
page_header("Marché en direct",
            "Les actifs populaires d'un coup d'œil : prix, variation, RSI, tendance et "
            "dernier signal. Clique une tuile pour l'analyser en détail.", icon="🛰️")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]

TRIS = ["Plus fortes hausses", "Plus fortes baisses", "RSI le plus haut", "Nom (A→Z)"]

with st.sidebar:
    st.header("Paramètres")
    timeframe = st.selectbox("Intervalle", ["1h", "4h", "1d", "1w"], index=2)
    actifs = st.multiselect("Actifs", PAIRES, default=PAIRES)
    tri = st.selectbox("Trier par", TRIS)


@st.cache_data(show_spinner="Lecture du marché…", ttl=300)
def ligne(symbol: str, timeframe: str) -> dict:
    """Indicateurs + sparkline pour un actif (mis en cache 5 min)."""
    df = fetch_ohlcv(symbol, timeframe, limit=60)
    indicators.add_rsi(df)
    indicators.add_sma(df, window=50)
    df = RsiSmaStrategy().generate_signals(df)
    closes = [float(x) for x in df["close"].tolist()]
    last, prev = closes[-1], closes[-2]
    var1 = (last / prev - 1) * 100
    var7 = (last / closes[-8] - 1) * 100 if len(closes) >= 8 else float("nan")
    return {
        "symbol": symbol, "price": last, "chg": var1, "var7": var7,
        "rsi": float(df["rsi"].iloc[-1]), "trend": indicators.detect_trend(df),
        "signal": int(df["signal"].iloc[-1]), "spark": closes[-24:],
    }


items = []
for sym in actifs:
    try:
        items.append(ligne(sym, timeframe))
    except Exception:
        pass

if not items:
    callout("Aucune donnée disponible pour le moment.", tone="warn")
    st.stop()

# --- Faits marquants (toujours calculés sur la variation, indépendamment du tri) ---
par_var = sorted(items, key=lambda x: x["chg"], reverse=True)
hausse, baisse = par_var[0], par_var[-1]
plus_rsi = max(items, key=lambda x: (x["rsi"] if x["rsi"] == x["rsi"] else -1))
m1, m2, m3 = st.columns(3)
m1.metric("🚀 Plus forte hausse", hausse["symbol"].split("/")[0], f"{hausse['chg']:+.2f} %")
m2.metric("📉 Plus forte baisse", baisse["symbol"].split("/")[0], f"{baisse['chg']:+.2f} %")
m3.metric("🔥 RSI le plus haut", plus_rsi["symbol"].split("/")[0], f"{plus_rsi['rsi']:.0f}")

# --- Tri choisi ---
if tri == "Plus fortes hausses":
    items.sort(key=lambda x: x["chg"], reverse=True)
elif tri == "Plus fortes baisses":
    items.sort(key=lambda x: x["chg"])
elif tri == "RSI le plus haut":
    items.sort(key=lambda x: (x["rsi"] if x["rsi"] == x["rsi"] else -1), reverse=True)
else:
    items.sort(key=lambda x: x["symbol"])

# --- Grille de tuiles cliquables ---
section("Tous les actifs", f"{len(items)} actifs · {timeframe} · clique pour analyser", live=True)
market_grid(items, C, link=True)

# --- Tableau détaillé (pour qui veut la densité) ---
with st.expander("📋 Tableau détaillé (copie, tri par colonne, sparklines)"):
    df = pd.DataFrame([{
        "Actif": it["symbol"], "Prix": round(it["price"], 4),
        "Var. (1)": round(it["chg"], 2),
        "Var. (7)": round(it["var7"], 2) if it["var7"] == it["var7"] else None,
        "RSI": round(it["rsi"], 1), "Tendance": it["trend"],
        "Signal": {1: "🟢 Achat", -1: "🔴 Vente", 0: "—"}[it["signal"]],
        "Évolution": it["spark"],
    } for it in items]).set_index("Actif")
    st.dataframe(
        df, use_container_width=True,
        column_config={
            "Prix": st.column_config.NumberColumn(format="%.4f"),
            "Var. (1)": st.column_config.NumberColumn("Var. 1 période %", format="%+.2f"),
            "Var. (7)": st.column_config.NumberColumn("Var. 7 périodes %", format="%+.2f"),
            "Évolution": st.column_config.LineChartColumn("20 dernières", width="medium"),
        },
    )

callout("Données mises en cache 5 min. « Var. (1) » = variation sur la dernière "
        "bougie de l'intervalle choisi. Aucun conseil, aucune transaction.",
        tone="info", icon="📌")
