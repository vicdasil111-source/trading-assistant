"""Page : prédiction par Machine Learning (évaluée honnêtement)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core.market_data import fetch_ohlcv
from core.ml_strategy import evaluate_ml
from utils.ui import callout, page_header, setup_page

setup_page("Machine Learning", icon="🧠")
page_header(
    "Prédiction par Machine Learning",
    "Un modèle apprend à prédire la prochaine bougie. On l'évalue sur des données "
    "jamais vues : la seule mesure honnête.",
    icon="🧠",
)

callout("Prédire les marchés est très difficile. Une précision proche de <b>50 %</b> "
        "= « pas mieux qu'un tirage à pile ou face ». C'est souvent le résultat, et "
        "c'est une vraie leçon : méfie-toi des promesses d'IA qui « bat le marché ».",
        tone="warn")

with st.sidebar:
    st.header("Paramètres")
    symbol = st.text_input("Actif", value="BTC/USDT")
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2)
    limit = st.slider("Nombre de bougies", 200, 1000, 700, step=50)
    kind = st.selectbox("Modèle", ["logistic", "tree"],
                        format_func=lambda k: "Régression logistique" if k == "logistic" else "Arbre de décision")
    train_frac = st.slider("Part entraînement (%)", 50, 90, 70, step=5) / 100
    fee = st.number_input("Frais (%)", min_value=0.0, value=0.1, step=0.05)
    lancer = st.button("Entraîner et évaluer", type="primary")

if lancer:
    try:
        df = fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as exc:
        st.error(f"Données indisponibles : {exc}")
        st.stop()

    try:
        with st.spinner("Entraînement du modèle..."):
            ev = evaluate_ml(df, kind=kind, train_frac=train_frac, fee_pct=fee)
    except Exception as exc:
        st.error(f"Erreur : {exc}")
        st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("Précision entraînement", f"{ev.train_accuracy:.1%}")
    c2.metric("Précision test (hors échantillon)", f"{ev.test_accuracy:.1%}",
              f"{(ev.test_accuracy - 0.5) * 100:+.1f} pts vs hasard")
    c3.metric("Rendement backtest (test)", f"{ev.test_return_pct:+.1f} %",
              f"B&H : {ev.buy_hold_test_pct:+.1f} %")

    if ev.test_accuracy < 0.55:
        callout("Le modèle ne fait pas significativement mieux que le hasard sur les "
                "données de test. Normal et instructif : prédire le prix est très dur.",
                tone="danger", icon="🎲")
    else:
        callout("Le modèle dépasse un peu le hasard sur le test — à confirmer sur "
                "d'autres périodes avant de s'emballer.", tone="gain")

    st.code(ev.summary(), language=None)
    st.caption(f"Échantillons : {ev.n_train} pour l'entraînement, {ev.n_test} pour le test.")
else:
    callout("Choisis un modèle dans la barre latérale, puis clique "
            "<b>Entraîner et évaluer</b>.", tone="info", icon="👈")
