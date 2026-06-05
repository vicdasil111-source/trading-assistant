"""
Dashboard Streamlit du Trading Assistant.

Lancement :
    streamlit run dashboard.py

Visualise le prix (chandelles), les indicateurs, lance un backtest et compare
les stratégies, le tout dans le navigateur. Aucune exécution d'ordre réel.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import indicators
from core.backtest import backtest
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils import notifications
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
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2)
    limit = st.slider("Nombre de bougies", min_value=100, max_value=1000, value=cfg.limit, step=50)
    strategy_name = st.selectbox("Stratégie", list(AVAILABLE_STRATEGIES))
    capital = st.number_input("Capital fictif", min_value=10.0, value=cfg.initial_capital, step=100.0)
    fee = st.number_input("Frais par transaction (%)", min_value=0.0, value=0.1, step=0.05)
    lancer = st.button("Analyser", type="primary")


@st.cache_data(show_spinner="Téléchargement des données...")
def charger(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    df = fetch_ohlcv(symbol, timeframe, limit=limit)
    return indicators.add_all(df)


def graphe_chandelles(df: pd.DataFrame) -> go.Figure:
    """Graphe en chandelles + moyennes mobiles + bandes de Bollinger."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["timestamp"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Prix",
    ))
    for col, couleur in [(f"sma_{cfg.sma_short}", "orange"),
                         (f"sma_{cfg.sma_long}", "blue")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df[col], name=col,
                                     line=dict(width=1, color=couleur)))
    if {"bb_upper", "bb_lower"}.issubset(df.columns):
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_upper"], name="Bollinger haut",
                                 line=dict(width=1, color="gray", dash="dot")))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lower"], name="Bollinger bas",
                                 line=dict(width=1, color="gray", dash="dot"),
                                 fill="tonexty", fillcolor="rgba(128,128,128,0.1)"))
    fig.update_layout(xaxis_rangeslider_visible=False, height=500,
                      margin=dict(l=0, r=0, t=10, b=0))
    return fig


if lancer:
    try:
        df = charger(symbol, timeframe, limit)
    except Exception as exc:
        st.error(f"Impossible de récupérer les données : {exc}")
        st.stop()

    derniere = df.iloc[-1]
    tendance = indicators.detect_trend(df)

    # --- Indicateurs clés ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Dernier prix", f"{derniere['close']:,.2f}")
    rsi = derniere.get("rsi", float("nan"))
    etat_rsi = "suracheté ⚠️" if rsi > cfg.rsi_overbought else \
               "survendu 💡" if rsi < cfg.rsi_oversold else "neutre"
    c2.metric("RSI", f"{rsi:.1f}", etat_rsi)
    c3.metric("Tendance", tendance)

    # --- Alertes ---
    df_sig = get_strategy(strategy_name).generate_signals(df)
    alertes = notifications.build_alerts(df_sig)
    for a in alertes:
        st.warning(a)

    # --- Graphe en chandelles ---
    st.subheader("Prix (chandelles), moyennes et Bollinger")
    st.plotly_chart(graphe_chandelles(df), use_container_width=True)

    # --- RSI & MACD ---
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("RSI")
        st.line_chart(df.set_index("timestamp")[["rsi"]])
    with g2:
        if {"macd", "macd_signal"}.issubset(df.columns):
            st.subheader("MACD")
            st.line_chart(df.set_index("timestamp")[["macd", "macd_signal"]])

    # --- Backtest de la stratégie choisie ---
    st.subheader(f"Backtest — stratégie « {strategy_name} »")
    res = backtest(df_sig, initial_capital=capital, fee_pct=fee)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Rendement", f"{res.total_return_pct:+.1f} %",
              f"{res.total_return_pct - res.buy_hold_return_pct:+.1f} % vs B&H")
    m2.metric("Buy & Hold", f"{res.buy_hold_return_pct:+.1f} %")
    m3.metric("Trades", res.num_trades)
    m4.metric("Sharpe", f"{res.sharpe_ratio:.2f}")
    m5.metric("Drawdown max", f"{res.max_drawdown_pct:.1f} %")

    st.caption("Courbe de capital (equity curve)")
    courbe = pd.DataFrame({"timestamp": df["timestamp"].values,
                           "capital": res.equity_curve}).set_index("timestamp")
    st.line_chart(courbe)

    # --- Comparaison de toutes les stratégies ---
    st.subheader("Comparaison des stratégies")
    rows = []
    for name in AVAILABLE_STRATEGIES:
        r = backtest(get_strategy(name).generate_signals(df), initial_capital=capital, fee_pct=fee)
        rows.append({
            "Stratégie": name,
            "Rendement %": round(r.total_return_pct, 2),
            "Trades": r.num_trades,
            "Réussite %": round(r.win_rate_pct, 1),
            "Sharpe": round(r.sharpe_ratio, 2),
            "Drawdown %": round(r.max_drawdown_pct, 1),
        })
    tableau = pd.DataFrame(rows).set_index("Stratégie")
    st.dataframe(tableau, use_container_width=True)
    st.caption(f"Référence Buy & Hold : {res.buy_hold_return_pct:+.2f} %")

    st.info("📌 Performance simulée sur données passées (frais inclus). Ne garantit rien "
            "sur l'avenir. Aucun ordre réel n'est passé.")
else:
    st.write("👈 Choisis un actif et une stratégie dans la barre latérale, puis clique **Analyser**.")
