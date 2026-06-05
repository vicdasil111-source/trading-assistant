"""Page : alertes de prix / RSI personnelles. Nécessite un compte."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import accounts, alerts, indicators
from core.market_data import fetch_ohlcv
from utils import account_ui
from utils.ui import callout, page_header, start_page

start_page("Alertes", icon="🔔")
page_header("Mes alertes",
            "Définis des conditions (prix ou RSI) et vois en un coup d'œil celles qui "
            "sont déclenchées maintenant. À toi de décider quoi en faire.", icon="🔔")

user = account_ui.require_login("tes alertes")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]


@st.cache_data(show_spinner=False, ttl=300)
def _prix_rsi(symbol: str) -> tuple[float, float]:
    df = fetch_ohlcv(symbol, "1d", limit=60)
    indicators.add_rsi(df)
    return float(df["close"].iloc[-1]), float(df["rsi"].iloc[-1])


# --- Création d'une alerte ---
with st.sidebar:
    st.header("Nouvelle alerte")
    with st.form("ajout_alerte"):
        sym_choix = st.selectbox("Actif", PAIRES)
        sym_perso = st.text_input("…ou symbole personnalisé").strip().upper()
        kind = st.selectbox("Condition", list(alerts.KINDS),
                            format_func=lambda k: alerts.KINDS[k])
        seuil = st.number_input("Seuil", value=70000.0, step=1.0)
        ok = st.form_submit_button("➕ Créer l'alerte", type="primary", use_container_width=True)
    if ok:
        accounts.add_alert(user, sym_perso or sym_choix, kind, seuil)
        st.rerun()

mes_alertes = accounts.get_alerts(user)
if not mes_alertes:
    callout("Aucune alerte. Crée-en une depuis la barre latérale "
            "(ex. « BTC/USDT — Prix ≥ 70000 »).", tone="info", icon="🔔")
    st.stop()

st.subheader("État en direct")
for a in mes_alertes:
    libelle = alerts.describe(a["symbol"], a["kind"], a["threshold"])
    col1, col2 = st.columns([5, 1])
    with col1:
        try:
            prix, rsi = _prix_rsi(a["symbol"])
            actuel = f"prix {prix:,.2f} · RSI {rsi:.0f}"
            if alerts.is_triggered(a["kind"], a["threshold"], prix, rsi):
                callout(f"<b>{libelle}</b> — déclenchée ✅ (actuellement {actuel}).", tone="gain")
            else:
                callout(f"{libelle} — en attente ({actuel}).", tone="info", icon="⏳")
        except Exception:
            callout(f"{libelle} — données indisponibles pour {a['symbol']}.", tone="warn")
    with col2:
        if st.button("🗑️", key=f"del_{a['id']}", help="Supprimer cette alerte"):
            accounts.remove_alert(user, a["id"])
            st.rerun()

callout("Les alertes sont vérifiées quand tu ouvres cette page (pas de notification "
        "push). Aucune transaction n'est déclenchée.", tone="info", icon="📌")
