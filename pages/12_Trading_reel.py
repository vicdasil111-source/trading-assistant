"""
Page : trading automatisé — du simulé au RÉEL, avec garde-fous.

Tu peux laisser le bot acheter/vendre à ta place :
  • soit en te demandant ta confirmation à chaque ordre,
  • soit en « autopilote » (il exécute seul) — c'est le mode le plus DANGEREUX.

⚠️ Le trading réel n'est possible que si tu héberges l'app toi-même avec TES
clés Binance et la variable I_UNDERSTAND_REAL_MONEY_RISK=yes. Sur le site public
partagé, aucune clé n'est présente : tout reste en simulation/testnet, par
conception (on ne manipule jamais l'argent de quelqu'un d'autre).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import execution, indicators
from core import trading_guard as tg
from core.market_data import fetch_ohlcv
from core.strategy import AVAILABLE_STRATEGIES, get_strategy
from utils.ui import callout, page_header, start_page

start_page("Trading réel", icon="⚡")
page_header("Trading automatisé — simulation, testnet ou réel",
            "Laisse le bot passer des ordres à ta place, avec confirmation ou en "
            "autopilote. Le réel n'est déverrouillé que si TU l'actives, avec des "
            "garde-fous. Lis bien la page Aide & FAQ avant.", icon="⚡")

callout("<b>AVERTISSEMENT — argent réel = risque réel.</b> Le trading de cryptos "
        "est très risqué : tu peux perdre la totalité de ton capital, vite. Un bot "
        "qui achète tout seul peut enchaîner les pertes pendant ton sommeil. "
        "Ceci n'est <b>pas un conseil en investissement</b>. N'engage que ce que tu "
        "peux te permettre de perdre. Voir la page <b>Aide &amp; FAQ</b>.", tone="danger")

PAIRES = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
mode_info = execution.account_mode()


def _last_price(symbol: str) -> float:
    df = fetch_ohlcv(symbol, "1h", limit=2)
    return float(df["close"].iloc[-1])


# --- État de l'environnement ------------------------------------------------
with st.expander("État de la connexion (ce qui est possible ici)", expanded=True):
    c1, c2, c3 = st.columns(3)
    c1.metric("Clés testnet", "✅ présentes" if mode_info["testnet_keys"] else "—")
    c2.metric("Clés réelles", "✅ présentes" if mode_info["real_keys"] else "—")
    c3.metric("Trading réel", "🔓 déverrouillé" if mode_info["real_available"] else "🔒 verrouillé")
    if not mode_info["real_available"]:
        callout("Le trading réel est <b>verrouillé ici</b> (site public partagé, sans "
                "clés). Pour l'activer, héberge l'app sur ta machine et définis tes "
                "variables d'environnement <code>BINANCE_API_KEY</code>, "
                "<code>BINANCE_SECRET</code> et <code>I_UNDERSTAND_REAL_MONEY_RISK=yes</code>. "
                "Utilise des clés <b>« trading » uniquement, SANS droit de retrait</b>.",
                tone="info")

# --- Argent investi réel (lecture seule) -----------------------------------
if mode_info["real_available"]:
    st.subheader("💰 Ton argent réel (positions)")
    if st.button("Rafraîchir le solde réel", key="refresh_bal"):
        st.session_state.pop("_real_snap", None)
    try:
        if "_real_snap" not in st.session_state:
            st.session_state["_real_snap"] = execution.account_positions(testnet=False)
        snap = st.session_state["_real_snap"]
        b1, b2 = st.columns(2)
        b1.metric("Liquidités (USDT)", f"{snap['cash_usdt']:,.2f}")
        b2.metric("Positions ouvertes", len(snap["positions"]))
        if snap["positions"]:
            import pandas as pd
            df_pos = pd.DataFrame(snap["positions"]).rename(
                columns={"asset": "Actif", "amount": "Quantité", "free": "Disponible"})
            st.dataframe(df_pos.set_index("Actif"), use_container_width=True)
        else:
            callout("Aucune position pour le moment (hors liquidités USDT).", tone="info")
        callout("Lecture seule : ce panneau n'achète ni ne vend rien. Tes fonds "
                "restent chez Binance.", tone="info", icon="🔒")
    except Exception as exc:
        callout(f"Impossible de lire le solde réel : {exc}", tone="warn")
else:
    callout("💰 <b>Argent investi réel</b> : ce panneau affichera tes liquidités et "
            "tes positions Binance une fois l'app <b>auto-hébergée</b> avec tes clés "
            "(<code>BINANCE_API_KEY</code> / <code>BINANCE_SECRET</code> + "
            "<code>I_UNDERSTAND_REAL_MONEY_RISK=yes</code>). Sur le site public il "
            "reste <b>verrouillé</b> — on ne touche jamais à l'argent d'autrui.",
            tone="info")

# --- 1. Acceptation des risques --------------------------------------------
st.subheader("1. Comprendre et accepter les risques")
acks = [
    ("perte", "Je comprends que je peux perdre **tout** l'argent engagé."),
    ("advice", "Je comprends que ceci n'est **pas** un conseil en investissement."),
    ("keys", "J'utilise des clés API « trading seulement », **sans droit de retrait**."),
    ("resp", "Je suis seul responsable de mes décisions, mes pertes et mes impôts."),
]
resultats = [st.checkbox(label, key=f"ack_{cle}") for cle, label in acks]
st.write("")
if not all(resultats):
    callout("Coche les quatre cases pour débloquer la suite.", tone="info", icon="🔒")
    st.stop()

# --- 2. Mode d'exécution ----------------------------------------------------
st.subheader("2. Mode d'exécution")
MODES = ["Simulation (rien n'est envoyé)", "Testnet (argent fictif)"]
if mode_info["real_available"]:
    MODES.append("RÉEL (argent réel) ⚠️")
mode = st.radio("Choisis le mode", MODES, horizontal=False)
is_real = mode.startswith("RÉEL")
is_testnet = mode.startswith("Testnet")
dry_run = mode.startswith("Simulation")
if is_real:
    callout("Mode <b>RÉEL</b> sélectionné. Chaque ordre engagera de l'argent réel.",
            tone="danger")

# --- 3. Garde-fous ----------------------------------------------------------
st.subheader("3. Garde-fous de sécurité")
st.caption("Limites appliquées **avant** chaque ordre réel. Le simulé/testnet n'est pas bridé.")
g1, g2, g3 = st.columns(3)
max_order = g1.number_input("Plafond par ordre (USDT)", 1.0, 1_000_000.0, 50.0, step=10.0)
daily_loss = g2.number_input("Perte max / jour (USDT)", 1.0, 1_000_000.0, 100.0, step=10.0)
max_trades = g3.number_input("Ordres max / jour", 1, 1000, 10, step=1)
guardrails = tg.Guardrails(float(max_order), float(daily_loss), int(max_trades))

stats = tg.today_stats()
st.caption(f"Aujourd'hui (réel) : {stats.get('trades', 0)} ordre(s), "
           f"{stats.get('notional', 0.0):.0f} USDT engagés, "
           f"{stats.get('loss', 0.0):.0f} USDT de pertes.")

# --- Coupe-circuit ----------------------------------------------------------
st.markdown("**Coupe-circuit d'urgence**")
if tg.kill_switch_active():
    callout("🛑 Coupe-circuit <b>ACTIF</b> : aucun ordre réel ne passera.", tone="danger")
    if st.button("Réactiver le trading (désarmer le coupe-circuit)"):
        tg.release_kill_switch()
        st.rerun()
else:
    if st.button("🛑 ARRÊT D'URGENCE — couper tout trading réel"):
        tg.engage_kill_switch("arrêt manuel via l'interface")
        st.rerun()

st.divider()

# --- 4. Ordre manuel (avec confirmation) -----------------------------------
st.subheader("4. Passer un ordre (avec confirmation)")
o1, o2, o3 = st.columns(3)
symbol = o1.selectbox("Actif", PAIRES, key="ord_sym")
side = o2.selectbox("Sens", ["buy", "sell"],
                    format_func=lambda s: "Acheter" if s == "buy" else "Vendre")
amount = o3.number_input("Quantité", min_value=0.0, value=0.001, step=0.001, format="%.6f")

valeur = None
try:
    prix = _last_price(symbol)
    valeur = prix * amount
    st.caption(f"Prix ~ {prix:,.2f} USDT → valeur de l'ordre ≈ **{valeur:,.2f} USDT**.")
except Exception:
    st.caption("Prix indisponible (la valeur de l'ordre ne pourra pas être vérifiée).")

confirme = True
if is_real:
    confirme = st.checkbox("Je confirme vouloir envoyer cet ordre RÉEL maintenant.")

if st.button("Envoyer l'ordre", type="primary", key="send_manual"):
    if is_real and not confirme:
        callout("Coche la confirmation avant d'envoyer un ordre réel.", tone="warn")
    else:
        try:
            res = execution.place_market_order(
                symbol, side, amount,
                testnet=is_testnet or dry_run, dry_run=dry_run,
                order_value_usdt=valeur, guardrails=guardrails)
            if res.get("dry_run"):
                callout(f"Simulation : {side} {amount} {symbol} — rien n'a été envoyé.",
                        tone="gain")
            else:
                cible = "testnet (fictif)" if is_testnet else "RÉEL"
                callout(f"Ordre envoyé sur {cible} : {side} {amount} {symbol}.",
                        tone="gain")
        except Exception as exc:
            callout(f"Ordre refusé : {exc}", tone="danger")

st.divider()

# --- 5. Autopilote sur signal ----------------------------------------------
st.subheader("5. Achat/vente automatique sur signal (autopilote)")
callout("L'autopilote calcule un signal de stratégie et <b>agit seul</b>, sans te "
        "redemander. C'est le mode le plus risqué : à n'utiliser qu'en simulation/"
        "testnet tant que tu n'es pas sûr de toi.", tone="warn")

a1, a2, a3 = st.columns(3)
sym2 = a1.selectbox("Actif à suivre", PAIRES, key="auto_sym")
strat = a2.selectbox("Stratégie", list(AVAILABLE_STRATEGIES), key="auto_strat")
amount2 = a3.number_input("Quantité par ordre", min_value=0.0, value=0.001,
                          step=0.001, format="%.6f", key="auto_amt")

autopilote = st.checkbox("⚠️ Activer l'autopilote : exécuter automatiquement, "
                         "sans me redemander.")
if autopilote and is_real:
    callout("Autopilote <b>RÉEL</b> armé : le prochain cycle pourra engager de "
            "l'argent réel tout seul (dans la limite des garde-fous).", tone="danger")

if st.button("Lancer un cycle d'autopilote", key="auto_cycle"):
    try:
        df = fetch_ohlcv(sym2, "1d", limit=200)
        indicators.add_all(df)
        df = get_strategy(strat).generate_signals(df)
        sig = int(df["signal"].iloc[-1])
        prix2 = float(df["close"].iloc[-1])
    except Exception as exc:
        callout(f"Données indisponibles : {exc}", tone="warn")
        st.stop()

    libelle = {1: "ACHÈTERAIT 📈", -1: "VENDRAIT 📉", 0: "n'agirait pas (neutre)"}[sig]
    callout(f"Signal <b>{strat}</b> sur {sym2} : le bot <b>{libelle}</b>.", tone="info")

    if sig == 0:
        st.stop()
    if not autopilote:
        callout("Autopilote désactivé : aucun ordre passé. Active la case ci-dessus "
                "pour qu'il agisse seul, ou passe l'ordre à la main au point 4.",
                tone="info")
        st.stop()

    try:
        res = execution.place_market_order(
            sym2, "buy" if sig == 1 else "sell", amount2,
            testnet=is_testnet or dry_run, dry_run=dry_run,
            order_value_usdt=prix2 * amount2, guardrails=guardrails)
        if res.get("dry_run"):
            callout(f"Autopilote (simulation) : {('buy' if sig==1 else 'sell')} "
                    f"{amount2} {sym2} — rien envoyé.", tone="gain")
        else:
            cible = "testnet (fictif)" if is_testnet else "RÉEL"
            callout(f"Autopilote a exécuté sur {cible} : "
                    f"{('buy' if sig==1 else 'sell')} {amount2} {sym2}.", tone="gain")
    except Exception as exc:
        callout(f"Autopilote bloqué par les garde-fous : {exc}", tone="danger")

callout("Pour un autopilote <b>continu</b> (24/7), lance-le en local : "
        "<code>python autopilot_runner.py --symbol BTC/USDT --strategy rsi_sma</code>. "
        "Par défaut il reste en simulation (argent fictif).", tone="info", icon="🤖")
