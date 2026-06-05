"""Page : compte utilisateur (inscription / connexion)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from core import accounts
from utils import account_ui
from utils.ui import callout, page_header, start_page

start_page("Compte", icon="👤")
page_header(
    "Ton compte",
    "Crée un compte pour enregistrer ta liste de suivi et tes préférences. "
    "Le mot de passe est haché, jamais stocké en clair.",
    icon="👤",
)

user = account_ui.current_user()

if user:
    callout(f"Tu es connecté en tant que <b>{user}</b>.", tone="gain", icon="👤")
    nb = len(accounts.get_watchlist(user))
    c1, c2 = st.columns(2)
    c1.metric("Identifiant", user)
    c2.metric("Actifs suivis", nb)
    if st.button("Se déconnecter", type="primary"):
        account_ui.do_logout()
        st.rerun()
else:
    onglet_co, onglet_inscr = st.tabs(["Se connecter", "Créer un compte"])
    with onglet_co:
        account_ui.login_form()
    with onglet_inscr:
        account_ui.signup_form()
    callout("Astuce : n'utilise pas un mot de passe que tu réutilises ailleurs. "
            "Ce projet est éducatif ; le stockage est local et peut être réinitialisé "
            "sur l'hébergement gratuit.", tone="info")
