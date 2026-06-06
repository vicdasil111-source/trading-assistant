"""Page : assistant pédagogique. Une barre de questions directe vers l'agent.

L'assistant répond en local (core/assistant.py) : pas d'API, pas de clé. Il
explique les indicateurs, les stratégies, le risque, le trading réel et la loi —
mais ne donne jamais de conseil en investissement et n'exécute aucun ordre.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import assistant, news
from core.market_data import fetch_ohlcv
from utils.ui import callout, page_header, start_page

start_page("Assistant", icon="💬")
page_header("Assistant pédagogique",
            "Pose tes questions sur l'app, les indicateurs, les stratégies, le "
            "risque ou la loi. Il connaît aussi les **prix en direct** et les "
            "**actualités**. Pédagogique — jamais de conseil, jamais d'ordre passé.",
            icon="💬")

GREETING = ("Bonjour 👋 Je suis l'assistant du site. Je peux expliquer les "
            "indicateurs et stratégies, mais aussi te donner le **prix en direct** "
            "(« Prix du Bitcoin ? ») et les **dernières actualités** (« Quoi de neuf ? »). "
            "Demande-moi ce que tu veux.")

if "chat" not in st.session_state:
    st.session_state["chat"] = [{"role": "assistant", "content": GREETING}]


@st.cache_data(ttl=300, show_spinner=False)
def _live_price(symbol: str) -> float:
    df = fetch_ohlcv(symbol, "1h", limit=2)
    return float(df["close"].iloc[-1])


@st.cache_data(ttl=600, show_spinner=False)
def _live_news() -> list[dict]:
    return news.latest_news(6)


def ask(question: str) -> None:
    question = (question or "").strip()
    if not question:
        return
    st.session_state["chat"].append({"role": "user", "content": question})
    reply = assistant.respond(question, price_fn=_live_price, news_fn=_live_news)
    st.session_state["chat"].append({"role": "assistant", "content": reply})


# Question envoyée depuis la barre de l'accueil (st.switch_page + session).
_pending = st.session_state.pop("assistant_pending", None)
if _pending:
    ask(_pending)

# Suggestions cliquables
st.caption("Questions fréquentes")
sugg = assistant.suggestions()
cols = st.columns(3)
for i, s in enumerate(sugg):
    if cols[i % 3].button(s, key=f"sugg_{i}", use_container_width=True):
        ask(s)
        st.rerun()

st.divider()

# Historique de la conversation
avatars = {"assistant": "🤖", "user": "🧑"}
for msg in st.session_state["chat"]:
    with st.chat_message(msg["role"], avatar=avatars.get(msg["role"])):
        st.markdown(msg["content"])

if len(st.session_state["chat"]) > 1:
    if st.button("🗑️ Effacer la conversation"):
        st.session_state["chat"] = [{"role": "assistant", "content": GREETING}]
        st.rerun()

callout("Je n'exécute <b>aucun ordre</b> et ne donne <b>aucun conseil d'achat</b>. "
        "Pour les sources et le détail, vois la page <b>Aide &amp; FAQ</b>.", tone="info")

# La barre de questions (épinglée en bas de la page).
prompt = st.chat_input("Pose ta question… (ex. « C'est quoi le RSI ? »)")
if prompt:
    ask(prompt)
    st.rerun()
