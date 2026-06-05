"""Page : comparateur de performances multi-actifs (base 100). Pas de compte requis."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.market_data import fetch_ohlcv
from utils.ui import callout, current_colors, page_header, start_page

start_page("Comparateur", icon="📊")
page_header("Comparateur d'actifs",
            "Compare l'évolution de plusieurs actifs sur la même base 100 : qui a le "
            "mieux performé sur la période ?", icon="📊")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]

with st.sidebar:
    st.header("Paramètres")
    choix = st.multiselect("Actifs à comparer", PAIRES,
                           default=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe = st.selectbox("Intervalle", ["1h", "4h", "1d", "1w"], index=2)
    limit = st.slider("Nombre de bougies", 100, 1000, 365, step=50)
    lancer = st.button("Comparer", type="primary", use_container_width=True)

C = current_colors()
# Palette de lignes (l'indigo de marque + couleurs distinctes, lisibles sur les 2 thèmes).
LIGNES = [C["primary"], C["gain"], C["warn"], C["loss"], "#3bb3c9", "#c06fe0"]


@st.cache_data(show_spinner="Téléchargement…", ttl=300)
def _serie(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    return fetch_ohlcv(symbol, timeframe, limit=limit)


if lancer and choix:
    fig = go.Figure()
    perfs = []
    for i, sym in enumerate(choix):
        try:
            df = _serie(sym, timeframe, limit)
        except Exception:
            callout(f"Données indisponibles pour {sym}.", tone="warn")
            continue
        base = df["close"] / float(df["close"].iloc[0]) * 100
        fig.add_trace(go.Scatter(x=df["timestamp"], y=base, name=sym,
                                 line=dict(width=2, color=LIGNES[i % len(LIGNES)])))
        perfs.append({"Actif": sym, "Performance %": round(float(base.iloc[-1] - 100), 1)})

    fig.add_hline(y=100, line=dict(color=C["muted"], width=1, dash="dot"))
    fig.update_layout(template=C["plotly"], height=460,
                      margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=C["ink"], family="Inter, sans-serif"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0))
    fig.update_xaxes(gridcolor=C["grid"])
    fig.update_yaxes(gridcolor=C["grid"], title="Base 100")
    st.plotly_chart(fig, use_container_width=True)

    if perfs:
        tableau = pd.DataFrame(perfs).sort_values("Performance %", ascending=False)
        meilleur = tableau.iloc[0]
        st.dataframe(tableau.set_index("Actif"), use_container_width=True)
        callout(f"🏆 Sur la période, <b>{meilleur['Actif']}</b> est en tête "
                f"({meilleur['Performance %']:+.1f} %).", tone="gain")
elif lancer:
    callout("Sélectionne au moins un actif.", tone="warn")
else:
    callout("Choisis des actifs dans la barre latérale, puis clique <b>Comparer</b>.",
            tone="info", icon="👈")
