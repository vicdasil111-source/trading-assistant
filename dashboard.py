"""
Dashboard Streamlit du Trading Assistant.

Lancement :
    streamlit run dashboard.py

Permet de visualiser le prix, les indicateurs et de lancer un backtest,
le tout dans le navigateur. Aucune exécution d'ordre réel.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core import indicators
from core.backtest import backtest
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils.config import default_config

st.set_page_config(page_title="Trading Assistant", page_icon="📈", layout="wide")

st.title("📈 Trading Assistant")
st.caption("Analyse crypto, backtesting et paper trading — **sans argent réel**. "
           "Ceci n'est pas un conseil financier.")

cfg = default_config

# --- Barre latérale : paramètres ---
with st.sidebar:
    st.header("Paramètres")
    symbol = st.text_input("Actif (format ccxt)", value=cfg.symbol)
    timeframe = st.selectbox(
        "Timeframe", ["1h", "4h", "1d", "1w"], index=2
    )
    limit = st.slider("Nombre de bougies", min_value=100, max_value=1000, value=cfg.limit, step=50)
    strategy_name = st.selectbox("Stratégie", list(AVAILABLE_STRATEGIES))
    capital = st.number_input("Capital fictif", min_value=10.0, value=cfg.initial_capital, step=100.0)
    lancer = st.button("Analyser", type="primary")


@st.cache_data(show_spinner="Téléchargement des données...")
def charger(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    df = fetch_ohlcv(symbol, timeframe, limit=limit)
    return indicators.add_all(df)


if lancer:
    try:
        df = charger(symbol, timeframe, limit)
    except Exception as exc:
        st.error(f"Impossible de récupérer les données : {exc}")
        st.stop()

    df = df.set_index("timestamp")
    derniere = df.iloc[-1]
    tendance = indicators.detect_trend(df.reset_index())

    # --- Indicateurs clés en haut ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Dernier prix", f"{derniere['close']:,.2f}")
    rsi = derniere.get("rsi", float("nan"))
    etat_rsi = "suracheté ⚠️" if rsi > cfg.rsi_overbought else \
               "survendu 💡" if rsi < cfg.rsi_oversold else "neutre"
    c2.metric("RSI", f"{rsi:.1f}", etat_rsi)
    c3.metric("Tendance", tendance)

    # --- Graphe prix + moyennes + Bollinger ---
    st.subheader("Prix et moyennes mobiles")
    cols_prix = [c for c in ["close", f"sma_{cfg.sma_short}", f"sma_{cfg.sma_long}",
                             "bb_upper", "bb_lower"] if c in df.columns]
    st.line_chart(df[cols_prix])

    # --- RSI ---
    st.subheader("RSI")
    st.line_chart(df[["rsi"]])

    # --- MACD ---
    if {"macd", "macd_signal"}.issubset(df.columns):
        st.subheader("MACD")
        st.line_chart(df[["macd", "macd_signal"]])

    # --- Backtest ---
    st.subheader("Backtest de la stratégie")
    strat = get_strategy(strategy_name)
    df_sig = strat.generate_signals(df.reset_index())
    res = backtest(df_sig, initial_capital=capital)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rendement", f"{res.total_return_pct:+.1f} %")
    m2.metric("Trades", res.num_trades)
    m3.metric("Taux de réussite", f"{res.win_rate_pct:.0f} %")
    m4.metric("Drawdown max", f"{res.max_drawdown_pct:.1f} %")

    st.caption("Courbe de capital (equity curve)")
    st.line_chart(pd.DataFrame({"capital": res.equity_curve}))

    st.info("📌 Performance simulée sur données passées. Ne garantit rien sur l'avenir. "
            "Aucun ordre réel n'est passé.")
else:
    st.write("👈 Choisis un actif et une stratégie dans la barre latérale, puis clique **Analyser**.")
