"""
Composants d'interface pour les comptes utilisateurs.

La connexion est **persistante** : à la connexion, un jeton de session aléatoire
est créé côté serveur (table `sessions`) et placé dans l'URL (`?s=...`). À chaque
chargement de page, `sidebar_account()` restaure l'utilisateur depuis ce jeton.
La session survit donc au changement de page et au rafraîchissement.

- `sidebar_account()` : restaure la session + affiche l'état (appelé par
  `ui.start_page`).
- `current_user()` / `require_login()` : helpers de garde d'accès.
- `login_form()` / `signup_form()` : formulaires de la page Compte.
"""

from __future__ import annotations

import time

import streamlit as st

from core import accounts
from utils.ui import callout

_MAX_FAILS = 5          # tentatives avant verrouillage
_COOLDOWN = 60          # secondes de verrouillage


def current_user() -> str | None:
    return st.session_state.get("user")


def _restore_from_token() -> None:
    """Restaure l'utilisateur depuis le jeton d'URL si la session l'a perdu."""
    if current_user():
        return
    token = st.query_params.get("s")
    if not token:
        return
    user = accounts.session_user(token)
    if user:
        st.session_state["user"] = user
    elif "s" in st.query_params:
        del st.query_params["s"]  # jeton invalide : on nettoie


def do_login(username: str) -> None:
    """Connecte l'utilisateur et pose un jeton de session persistant."""
    token = accounts.create_session(username)
    st.session_state["user"] = username
    st.query_params["s"] = token


def do_logout() -> None:
    token = st.query_params.get("s")
    if token:
        accounts.delete_session(token)
        del st.query_params["s"]
    st.session_state.pop("user", None)


def sidebar_account() -> None:
    """Restaure la session et affiche l'état de connexion en haut de la sidebar."""
    _restore_from_token()
    with st.sidebar:
        user = current_user()
        if user:
            st.markdown(f"👤 **{user}**")
            if st.button("Se déconnecter", key="logout_btn", use_container_width=True):
                do_logout()
                st.rerun()
        else:
            st.caption("Non connecté — va sur la page **Compte** pour t'inscrire.")
        st.divider()


def require_login(feature: str = "cette page") -> str:
    """Bloque la page si l'utilisateur n'est pas connecté. Renvoie le pseudo sinon."""
    user = current_user()
    if not user:
        callout(f"Connecte-toi (page <b>Compte</b> dans la barre latérale) pour "
                f"accéder à {feature}.", tone="info", icon="🔒")
        st.stop()
    return user


def login_form() -> None:
    """Formulaire de connexion, avec limitation anti-force-brute."""
    locked_until = st.session_state.get("login_locked_until", 0.0)
    reste = int(locked_until - time.time())
    if reste > 0:
        st.error(f"Trop de tentatives. Réessaie dans {reste} s.")
        return

    with st.form("login_form"):
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
    if not ok:
        return

    try:
        valide = accounts.authenticate(u, p)
    except Exception:
        st.error("Le service de comptes est momentanément indisponible. Réessaie.")
        return

    if valide:
        st.session_state["login_fails"] = 0
        do_login(u.strip())
        st.rerun()
        return

    fails = st.session_state.get("login_fails", 0) + 1
    st.session_state["login_fails"] = fails
    if fails >= _MAX_FAILS:
        st.session_state["login_locked_until"] = time.time() + _COOLDOWN
        st.session_state["login_fails"] = 0
        st.error(f"Trop de tentatives. Connexion verrouillée {_COOLDOWN} s.")
    else:
        st.error(f"Identifiant ou mot de passe incorrect. "
                 f"({_MAX_FAILS - fails} essai(s) restant(s))")


def signup_form() -> None:
    """Formulaire d'inscription."""
    with st.form("signup_form"):
        u = st.text_input("Choisis un identifiant (min. 3 caractères)")
        e = st.text_input("E-mail (facultatif)")
        p1 = st.text_input("Mot de passe (min. 8 caractères)", type="password")
        p2 = st.text_input("Confirme le mot de passe", type="password")
        ok = st.form_submit_button("Créer mon compte", type="primary", use_container_width=True)
    if ok:
        if p1 != p2:
            st.error("Les deux mots de passe ne correspondent pas.")
            return
        try:
            accounts.create_user(u, p1, email=e)
        except ValueError as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error("Le service de comptes est momentanément indisponible. Réessaie "
                     "plus tard.")
            return
        do_login(u.strip())
        st.rerun()
