"""Page : auto-optimisation d'une stratégie (avec test du sur-apprentissage)."""

import os
import sys

# S'assurer que la racine du projet est importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core.market_data import fetch_ohlcv
from core.optimizer import optimize_strategy
from core.strategy import (
    BollingerStrategy,
    BreakoutStrategy,
    EmaCrossStrategy,
    RsiSmaStrategy,
)
from utils.ui import callout, page_header, setup_page

setup_page("Optimisation", icon="⚙️")
page_header(
    "Auto-optimisation",
    "Le bot teste plein de réglages et garde le meilleur, puis on vérifie s'il "
    "tient sur des données jamais vues — le seul vrai test.",
    icon="⚙️",
)

# Stratégies optimisables et leurs grilles de paramètres candidates.
GRILLES = {
    "ema_cross": (EmaCrossStrategy, {
        "short": [5, 10, 20, 30],
        "long": [50, 100, 150, 200],
    }),
    "bollinger": (BollingerStrategy, {
        "window": [10, 20, 30],
        "num_std": [1.5, 2.0, 2.5],
    }),
    "rsi_sma": (RsiSmaStrategy, {
        "rsi_oversold": [20, 30, 40],
        "rsi_overbought": [60, 70, 80],
        "sma_long": [50, 100],
    }),
    "breakout": (BreakoutStrategy, {
        "window": [10, 20, 30, 50],
    }),
}

with st.sidebar:
    st.header("Paramètres")
    symbol = st.text_input("Actif", value="BTC/USDT")
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2)
    limit = st.slider("Nombre de bougies", 200, 1000, 500, step=50)
    strat_name = st.selectbox("Stratégie à optimiser", list(GRILLES))
    metric = st.selectbox("Critère à maximiser", ["total_return_pct", "sharpe_ratio"])
    train_frac = st.slider("Part entraînement (%)", 50, 90, 70, step=5) / 100
    fee = st.number_input("Frais (%)", min_value=0.0, value=0.1, step=0.05)
    lancer = st.button("Optimiser", type="primary")

if lancer:
    strategy_class, param_grid = GRILLES[strat_name]
    try:
        df = fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as exc:
        st.error(f"Données indisponibles : {exc}")
        st.stop()

    n_combis = 1
    for v in param_grid.values():
        n_combis *= len(v)
    with st.spinner(f"Test de {n_combis} combinaisons..."):
        res = optimize_strategy(df, strategy_class, param_grid,
                                fee_pct=fee, train_frac=train_frac, metric=metric)

    st.subheader("Résultat")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entraînement (passé)", f"{res.train_return_pct:+.1f} %")
    c2.metric("Test (futur simulé)", f"{res.test_return_pct:+.1f} %",
              f"{-res.overfitting_gap:+.1f} % vs entraînement")
    c3.metric("Buy & Hold (test)", f"{res.buy_hold_test_pct:+.1f} %")

    st.write("**Meilleurs paramètres :**", res.best_params)

    if res.overfitting_gap > 20:
        callout("Gros écart entre entraînement et test : c'est du <b>sur-apprentissage</b>. "
                "Les paramètres ont mémorisé le passé sans réelle capacité de prédiction. "
                "Méfie-toi des stratégies « parfaites » sur l'historique.", tone="warn")
    else:
        callout("L'écart entraînement/test est raisonnable : la stratégie semble "
                "se généraliser.", tone="gain")

    st.subheader("Toutes les combinaisons testées (sur l'entraînement)")
    tableau = pd.DataFrame(
        [{**p, "rendement_entrainement_%": round(r, 2)} for p, r in res.all_results]
    )
    st.dataframe(tableau, use_container_width=True)
else:
    callout("Choisis une stratégie dans la barre latérale, puis clique "
            "<b>Optimiser</b>.", tone="info", icon="👈")
