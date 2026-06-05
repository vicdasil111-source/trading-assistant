"""
Site Trading Assistant — page d'accueil « Analyse ».

Lancement :
    streamlit run dashboard.py

Panneau d'analyse complet : indicateurs réglables, affichage modulable, graphe
en chandelles avec volume et signaux, backtest avec benchmark, exports CSV.
Aucune exécution d'ordre réel.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import streamlit as st

from core import indicators
from core.backtest import backtest
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, RsiSmaStrategy, get_strategy
from utils import notifications
from utils.config import Config, default_config
from utils.ui import callout, page_header, start_page

C = start_page("Analyse", icon="📈")
page_header(
    "Analyse du marché",
    "Indicateurs, signaux et backtest sur données réelles — sans argent réel. "
    "Ceci n'est pas un conseil financier.",
    icon="📈",
)
callout("Dans la barre latérale : <b>Optimisation</b> (le bot règle ses stratégies "
        "seul), <b>Pilote auto</b> (portefeuille fictif autonome), <b>Machine "
        "Learning</b> (prédiction).", tone="info", icon="🧭")

cfg = default_config
PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]

# -----------------------------------------------------------------------------
# Panneau de contrôle (sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Paramètres")
    choix = st.selectbox("Actif", PAIRES + ["Autre…"])
    symbol = st.text_input("Symbole personnalisé", value="BTC/USDT") if choix == "Autre…" else choix
    timeframe = st.selectbox("Intervalle", ["15m", "30m", "1h", "4h", "1d", "1w"], index=4)
    limit = st.slider("Nombre de bougies", 100, 1000, cfg.limit, step=50)
    strategy_name = st.selectbox("Stratégie", list(AVAILABLE_STRATEGIES))
    capital = st.number_input("Capital fictif", min_value=10.0, value=cfg.initial_capital, step=100.0)
    fee = st.number_input("Frais par transaction (%)", min_value=0.0, value=0.1, step=0.05)

    with st.expander("⚙️ Réglages des indicateurs"):
        rsi_w = st.slider("RSI — période", 5, 30, cfg.rsi_window)
        sma_s = st.slider("Moyenne courte", 5, 60, cfg.sma_short)
        sma_l = st.slider("Moyenne longue", 20, 200, cfg.sma_long)
        bb_w = st.slider("Bollinger — période", 10, 40, cfg.bollinger_window)
        bb_std = st.slider("Bollinger — écarts-types", 1.0, 3.0, cfg.bollinger_std, step=0.5)

    with st.expander("👁️ Affichage du graphe"):
        show_sma = st.checkbox("Moyennes mobiles", value=True)
        show_bb = st.checkbox("Bandes de Bollinger", value=True)
        show_signals = st.checkbox("Signaux achat / vente", value=True)
        show_volume = st.checkbox("Volume", value=True)
        show_rsi = st.checkbox("Sous-graphe RSI", value=True)
        show_macd = st.checkbox("Sous-graphe MACD", value=True)
        show_stoch = st.checkbox("Sous-graphe Stochastique", value=False)

    lancer = st.button("Analyser", type="primary", use_container_width=True)

ucfg = Config(symbol=symbol, timeframe=timeframe, limit=limit, initial_capital=capital,
              rsi_window=rsi_w, sma_short=sma_s, sma_long=sma_l,
              bollinger_window=bb_w, bollinger_std=bb_std)


# -----------------------------------------------------------------------------
# Données & graphes
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Téléchargement des données…")
def charger_brut(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    return fetch_ohlcv(symbol, timeframe, limit=limit)


def _plotly_layout(fig: go.Figure, height: int) -> None:
    fig.update_layout(
        template=C["plotly"], height=height, xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["ink"], family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=C["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False)


def graphe_prix(df: pd.DataFrame) -> go.Figure:
    rows = 1 + int(show_volume)
    heights = [0.78, 0.22] if show_volume else [1.0]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.04, row_heights=heights)

    fig.add_trace(go.Candlestick(
        x=df["timestamp"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="Prix", increasing_line_color=C["gain"], increasing_fillcolor=C["gain"],
        decreasing_line_color=C["loss"], decreasing_fillcolor=C["loss"]), row=1, col=1)

    if show_sma:
        for col, color in [(f"sma_{sma_s}", C["warn"]), (f"sma_{sma_l}", C["primary"])]:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df["timestamp"], y=df[col], name=col,
                                         line=dict(width=1.4, color=color)), row=1, col=1)
    if show_bb and {"bb_upper", "bb_lower"}.issubset(df.columns):
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_upper"], name="Bollinger",
                                 line=dict(width=1, color=C["muted"], dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lower"], name="Bollinger bas",
                                 line=dict(width=1, color=C["muted"], dash="dot"),
                                 fill="tonexty", fillcolor=C["bb_fill"], showlegend=False), row=1, col=1)
    if show_signals and "signal" in df.columns:
        sig, prec = df["signal"], df["signal"].shift(1)
        ach = df[(sig == 1) & (prec != 1)]
        ven = df[(sig == -1) & (prec != -1)]
        if not ach.empty:
            fig.add_trace(go.Scatter(x=ach["timestamp"], y=ach["low"] * 0.985, name="Achat",
                mode="markers", marker=dict(symbol="triangle-up", size=11, color=C["gain"],
                line=dict(width=1, color=C["bg"])), hovertemplate="Achat<br>%{x}<extra></extra>"), row=1, col=1)
        if not ven.empty:
            fig.add_trace(go.Scatter(x=ven["timestamp"], y=ven["high"] * 1.015, name="Vente",
                mode="markers", marker=dict(symbol="triangle-down", size=11, color=C["loss"],
                line=dict(width=1, color=C["bg"])), hovertemplate="Vente<br>%{x}<extra></extra>"), row=1, col=1)
    if show_volume:
        couleurs = [C["gain"] if c >= o else C["loss"] for o, c in zip(df["open"], df["close"])]
        fig.add_trace(go.Bar(x=df["timestamp"], y=df["volume"], name="Volume",
                             marker_color=couleurs, marker_line_width=0, opacity=0.5,
                             showlegend=False), row=2, col=1)
    _plotly_layout(fig, 560 if show_volume else 480)
    return fig


def graphe_rsi(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor=C["warn"], opacity=0.10, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor=C["primary"], opacity=0.10, line_width=0)
    for lvl in (30, 70):
        fig.add_hline(y=lvl, line=dict(color=C["muted"], width=1, dash="dot"))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["rsi"], name="RSI",
                             line=dict(color=C["primary"], width=1.6)))
    _plotly_layout(fig, 220)
    fig.update_yaxes(range=[0, 100])
    return fig


def graphe_macd(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    couleurs = [C["gain"] if v >= 0 else C["loss"] for v in df["macd_hist"]]
    fig.add_trace(go.Bar(x=df["timestamp"], y=df["macd_hist"], name="Histogramme",
                         marker_color=couleurs, marker_line_width=0, opacity=0.5))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd"], name="MACD",
                             line=dict(color=C["primary"], width=1.6)))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd_signal"], name="Signal",
                             line=dict(color=C["warn"], width=1.4)))
    _plotly_layout(fig, 220)
    return fig


def graphe_stoch(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=80, y1=100, fillcolor=C["warn"], opacity=0.10, line_width=0)
    fig.add_hrect(y0=0, y1=20, fillcolor=C["primary"], opacity=0.10, line_width=0)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["stoch_k"], name="%K",
                             line=dict(color=C["primary"], width=1.6)))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["stoch_d"], name="%D",
                             line=dict(color=C["warn"], width=1.4)))
    _plotly_layout(fig, 220)
    fig.update_yaxes(range=[0, 100])
    return fig


def graphe_equity(df: pd.DataFrame, equity: list[float], capital: float) -> go.Figure:
    bh = capital * df["close"] / float(df["close"].iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=bh, name="Buy & Hold",
                             line=dict(color=C["muted"], width=1.4, dash="dot")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=equity, name="Stratégie",
                             line=dict(color=C["primary"], width=2),
                             fill="tozeroy", fillcolor=C["bb_fill"]))
    _plotly_layout(fig, 300)
    return fig


# -----------------------------------------------------------------------------
# Corps de la page
# -----------------------------------------------------------------------------
if lancer:
    st.session_state["analyse_demandee"] = True

if st.session_state.get("analyse_demandee"):
    try:
        df = charger_brut(symbol, timeframe, limit).copy()
    except Exception as exc:
        st.error(f"Impossible de récupérer les données : {exc}")
        st.stop()

    indicators.add_all(df, ucfg)
    strat = RsiSmaStrategy(config=ucfg) if strategy_name == "rsi_sma" else get_strategy(strategy_name)
    df = strat.generate_signals(df)
    derniere = df.iloc[-1]
    tendance = indicators.detect_trend(df, short=sma_s, long=sma_l)

    # --- Métriques clés ---
    a, b, c, d = st.columns(4)
    a.metric("Dernier prix", f"{derniere['close']:,.2f}")
    rsi = derniere.get("rsi", float("nan"))
    etat = "suracheté" if rsi > 70 else "survendu" if rsi < 30 else "neutre"
    b.metric("RSI", f"{rsi:.1f}", etat)
    c.metric("Tendance", tendance)
    sig_map = {1: "ACHAT 📈", -1: "VENTE 📉", 0: "neutre"}
    d.metric("Dernier signal", sig_map.get(int(derniere["signal"]), "?"))

    # --- Alertes ---
    for alerte in notifications.build_alerts(df, config=ucfg):
        tone = "warn" if "SURACHAT" in alerte else "info"
        callout(alerte, tone=tone)

    # --- Graphe principal ---
    st.subheader("Prix, volume et signaux")
    st.plotly_chart(graphe_prix(df), use_container_width=True)

    # --- Sous-graphes optionnels ---
    sous = [(show_rsi, "RSI", graphe_rsi), (show_macd, "MACD", graphe_macd),
            (show_stoch, "Stochastique", graphe_stoch)]
    actifs = [(t, f) for show, t, f in sous if show]
    if actifs:
        cols = st.columns(len(actifs)) if len(actifs) > 1 else [st]
        for col, (titre, fonction) in zip(cols, actifs):
            with col:
                st.caption(titre)
                st.plotly_chart(fonction(df), use_container_width=True)

    # --- Backtest ---
    st.subheader(f"Backtest — stratégie « {strategy_name} »")
    res = backtest(df, initial_capital=capital, fee_pct=fee)
    m = st.columns(5)
    m[0].metric("Rendement", f"{res.total_return_pct:+.1f} %",
                f"{res.total_return_pct - res.buy_hold_return_pct:+.1f} % vs B&H")
    m[1].metric("Buy & Hold", f"{res.buy_hold_return_pct:+.1f} %")
    m[2].metric("Trades", res.num_trades)
    m[3].metric("Sharpe", f"{res.sharpe_ratio:.2f}")
    m[4].metric("Drawdown max", f"{res.max_drawdown_pct:.1f} %")

    st.caption("Capital simulé vs Buy & Hold")
    st.plotly_chart(graphe_equity(df, res.equity_curve, capital), use_container_width=True)

    # --- Comparaison des stratégies ---
    st.subheader("Comparaison des stratégies")
    rows = []
    for name in AVAILABLE_STRATEGIES:
        s = (RsiSmaStrategy(config=ucfg) if name == "rsi_sma" else get_strategy(name))
        r = backtest(s.generate_signals(df), initial_capital=capital, fee_pct=fee)
        rows.append({"Stratégie": name, "Rendement %": round(r.total_return_pct, 2),
                     "Trades": r.num_trades, "Réussite %": round(r.win_rate_pct, 1),
                     "Sharpe": round(r.sharpe_ratio, 2), "Drawdown %": round(r.max_drawdown_pct, 1)})
    st.dataframe(pd.DataFrame(rows).set_index("Stratégie"), use_container_width=True)

    # --- Journal des signaux ---
    with st.expander("📋 Journal des signaux (points d'entrée)"):
        sig, prec = df["signal"], df["signal"].shift(1)
        entrees = df[(sig != 0) & (sig != prec)][["timestamp", "close", "signal"]].copy()
        entrees["Signal"] = entrees["signal"].map({1: "Achat", -1: "Vente"})
        entrees = entrees.rename(columns={"timestamp": "Date", "close": "Prix"})[["Date", "Signal", "Prix"]]
        if entrees.empty:
            st.write("Aucun signal sur la période.")
        else:
            st.dataframe(entrees[::-1], use_container_width=True, hide_index=True)

    # --- Exports ---
    st.subheader("Exporter")
    e1, e2 = st.columns(2)
    e1.download_button("⬇️ Données + indicateurs (CSV)",
                       df.to_csv(index=False).encode("utf-8"),
                       file_name=f"{symbol.replace('/', '-')}_{timeframe}.csv",
                       use_container_width=True)
    trades_csv = pd.DataFrame({"pnl": res.trades}).to_csv(index=False).encode("utf-8")
    e2.download_button("⬇️ Trades du backtest (CSV)", trades_csv,
                       file_name=f"trades_{strategy_name}.csv", use_container_width=True)

    callout("Performance simulée sur données passées (frais inclus). Ne garantit rien "
            "sur l'avenir. Aucun ordre réel n'est passé.", tone="info", icon="📌")

    # --- Glossaire ---
    with st.expander("📖 Comprendre les indicateurs"):
        st.markdown(
            "- **RSI** : force de la tendance, de 0 à 100. > 70 = suracheté, < 30 = survendu.\n"
            "- **SMA / EMA** : moyennes mobiles du prix (simple / exponentielle) ; lissent la tendance.\n"
            "- **MACD** : différence de deux moyennes ; son croisement signale un changement de momentum.\n"
            "- **Bandes de Bollinger** : enveloppe de volatilité autour d'une moyenne.\n"
            "- **Stochastique** : situe la clôture dans la fourchette récente (> 80 / < 20).\n"
            "- **Buy & Hold** : référence « acheter et garder » ; une stratégie doit faire mieux qu'elle.\n"
            "- **Sharpe** : rendement ajusté du risque (plus c'est haut, mieux c'est).\n"
            "- **Drawdown** : pire baisse depuis un sommet."
        )
else:
    st.write("👈 Règle tes paramètres dans la barre latérale, puis clique **Analyser**.")
