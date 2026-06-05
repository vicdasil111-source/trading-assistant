"""Page : portefeuille manuel (suivi de positions). Nécessite un compte."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from core import accounts, portfolio
from core.market_data import fetch_ohlcv
from utils import account_ui
from utils.ui import callout, page_header, start_page

start_page("Portefeuille", icon="💼")
page_header("Mon portefeuille",
            "Enregistre tes positions (fictives ou réelles) et suis leur valeur et "
            "ta plus/moins-value en temps réel. Aucune exécution d'ordre.", icon="💼")

user = account_ui.require_login("ton portefeuille")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
          "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT"]


@st.cache_data(show_spinner=False, ttl=300)
def _prix(symbol: str) -> float:
    df = fetch_ohlcv(symbol, "1d", limit=30)
    return float(df["close"].iloc[-1])


# --- Ajout d'une position ---
with st.sidebar:
    st.header("Ajouter une position")
    with st.form("ajout_position"):
        sym_choix = st.selectbox("Actif", PAIRES)
        sym_perso = st.text_input("…ou symbole personnalisé").strip().upper()
        qte = st.number_input("Quantité", min_value=0.0, value=1.0, step=0.1, format="%.4f")
        prix_achat = st.number_input("Prix d'achat moyen", min_value=0.0, value=100.0, step=1.0)
        ok = st.form_submit_button("➕ Ajouter", type="primary", use_container_width=True)
    if ok:
        try:
            accounts.add_holding(user, sym_perso or sym_choix, qte, prix_achat)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

holdings = accounts.get_holdings(user)
if not holdings:
    callout("Ton portefeuille est vide. Ajoute une position depuis la barre latérale.",
            tone="info", icon="💼")
    st.stop()

# --- Évaluation ---
prix = {}
for h in holdings:
    try:
        prix[h["symbol"]] = _prix(h["symbol"])
    except Exception:
        pass
res = portfolio.evaluate(holdings, prix)

m = st.columns(4)
m[0].metric("Valeur actuelle", f"{res['total_value']:,.2f}")
m[1].metric("Investi (coût)", f"{res['total_cost']:,.2f}")
m[2].metric("Plus/moins-value", f"{res['total_pnl']:+,.2f}")
m[3].metric("Performance", f"{res['total_pnl_pct']:+.1f} %")

# --- Tableau des positions ---
lignes = []
for r in res["rows"]:
    lignes.append({
        "Actif": r["symbol"],
        "Quantité": r["quantity"],
        "Prix d'achat": r["buy_price"],
        "Prix actuel": r["price"] if r["price"] is not None else "—",
        "Valeur": round(r["value"], 2) if r["value"] is not None else "—",
        "P&L": round(r["pnl"], 2) if r["pnl"] is not None else "—",
        "P&L %": round(r["pnl_pct"], 1) if r["pnl_pct"] is not None else "—",
    })
st.dataframe(pd.DataFrame(lignes).set_index("Actif"), use_container_width=True)

# --- Retrait ---
options = {f"{h['symbol']} · {h['quantity']:g} @ {h['buy_price']:g}": h["id"] for h in holdings}
col1, col2 = st.columns([3, 1])
choix = col1.selectbox("Retirer une position", list(options))
if col2.button("🗑️ Retirer", use_container_width=True):
    accounts.remove_holding(user, options[choix])
    st.rerun()

callout("Valeurs au dernier cours quotidien (rafraîchies toutes les 5 min). "
        "Outil de suivi : aucune transaction n'est exécutée.", tone="info", icon="📌")
