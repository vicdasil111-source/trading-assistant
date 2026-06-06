"""Page : actualités crypto en direct (les « journaux »).

Agrège des flux RSS publics (Google Actualités FR, Cointelegraph, Decrypt) via
core/news.py — aucune clé, aucune dépendance. Purement informatif.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import news
from utils.ui import callout, news_cards, page_header, section, start_page

start_page("Actualités", icon="📰")
page_header("Actualités crypto en direct",
            "Les titres des journaux du moment, agrégés. Clique un article pour le "
            "lire à la source. Information seulement — pas un conseil en investissement.",
            icon="📰")


@st.cache_data(ttl=600, show_spinner=False)
def charger_news() -> list[dict]:
    return news.latest_news(20)


c1, c2 = st.columns([4, 1])
with c2:
    if st.button("🔄 Rafraîchir", use_container_width=True):
        charger_news.clear()
        st.rerun()

section("À la une", "mis à jour en direct", live=True)
with st.spinner("Chargement des actualités…"):
    items = charger_news()
news_cards(items)

callout("Sources agrégées : Google Actualités (presse FR), Cointelegraph, Decrypt. "
        "Les titres sont récupérés en direct ; leur exactitude relève de leurs "
        "éditeurs. Rien ici n'est un conseil d'achat.", tone="info", icon="📰")
