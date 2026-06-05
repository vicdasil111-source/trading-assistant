"""
Comptes utilisateurs (intégrés, SQLite).

⚠️ Sécurité : les mots de passe ne sont JAMAIS stockés en clair. On garde
seulement un hachage PBKDF2-HMAC-SHA256 (200 000 itérations) avec un sel
aléatoire par utilisateur. Vérifier un mot de passe = re-hacher la saisie et
comparer en temps constant.

⚠️ Persistance : la base vit dans `data/accounts.db`. En local elle persiste ;
sur un hébergement gratuit au système de fichiers éphémère (Streamlit Cloud),
elle peut être réinitialisée à un redéploiement. Pour des comptes durables,
pointer ACCOUNTS_DB vers un volume persistant ou une base externe.

Ce module gère aussi les données par utilisateur : liste de suivi (watchlist)
et préférences.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from utils.config import DATA_DIR

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def db_path() -> Path:
    """Chemin de la base ; surchargé par la variable d'environnement ACCOUNTS_DB."""
    env = os.environ.get("ACCOUNTS_DB")
    return Path(env) if env else DATA_DIR / "accounts.db"


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path | None = None) -> None:
    """Crée les tables si besoin (idempotent)."""
    with _connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                username   TEXT PRIMARY KEY,
                email      TEXT,
                salt       TEXT NOT NULL,
                pwd_hash   TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                username TEXT NOT NULL,
                symbol   TEXT NOT NULL,
                PRIMARY KEY (username, symbol)
            );
            CREATE TABLE IF NOT EXISTS prefs (
                username TEXT NOT NULL,
                key      TEXT NOT NULL,
                value    TEXT,
                PRIMARY KEY (username, key)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                username   TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


# --- Hachage ---

def _hash(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                             bytes.fromhex(salt), _ITERATIONS)
    return dk.hex()


# --- Utilisateurs ---

def create_user(username: str, password: str, email: str = "",
                path: Path | None = None) -> None:
    """Crée un compte. Lève ValueError si invalide ou déjà pris."""
    username = (username or "").strip()
    if len(username) < 3:
        raise ValueError("Le nom d'utilisateur doit faire au moins 3 caractères.")
    if len(password) < 6:
        raise ValueError("Le mot de passe doit faire au moins 6 caractères.")
    if email and not _EMAIL_RE.match(email):
        raise ValueError("Adresse e-mail invalide.")

    init_db(path)
    salt = secrets.token_hex(16)
    pwd_hash = _hash(password, salt)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with _connect(path) as conn:
            conn.execute(
                "INSERT INTO users (username, email, salt, pwd_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, email, salt, pwd_hash, created),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("Ce nom d'utilisateur est déjà pris.") from exc


def authenticate(username: str, password: str, path: Path | None = None) -> bool:
    """Renvoie True si le couple identifiant / mot de passe est correct."""
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT salt, pwd_hash FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if row is None:
        return False
    candidate = _hash(password, row["salt"])
    return hmac.compare_digest(candidate, row["pwd_hash"])


def user_exists(username: str, path: Path | None = None) -> bool:
    init_db(path)
    with _connect(path) as conn:
        return conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username.strip(),)
        ).fetchone() is not None


# --- Sessions (connexion persistante par jeton) ---

def create_session(username: str, path: Path | None = None) -> str:
    """Crée un jeton de session aléatoire pour l'utilisateur et le renvoie."""
    init_db(path)
    token = secrets.token_urlsafe(24)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect(path) as conn:
        conn.execute("INSERT INTO sessions (token, username, created_at) VALUES (?, ?, ?)",
                     (token, username, created))
    return token


def session_user(token: str, path: Path | None = None) -> str | None:
    """Renvoie l'utilisateur associé à un jeton, ou None s'il est invalide."""
    if not token:
        return None
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT username FROM sessions WHERE token = ?", (token,)).fetchone()
    return row["username"] if row else None


def delete_session(token: str, path: Path | None = None) -> None:
    if not token:
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# --- Watchlist ---

def add_watch(username: str, symbol: str, path: Path | None = None) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (username, symbol) VALUES (?, ?)",
            (username, symbol.upper().strip()),
        )


def remove_watch(username: str, symbol: str, path: Path | None = None) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE username = ? AND symbol = ?",
            (username, symbol.upper().strip()),
        )


def get_watchlist(username: str, path: Path | None = None) -> list[str]:
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT symbol FROM watchlist WHERE username = ? ORDER BY symbol", (username,)
        ).fetchall()
    return [r["symbol"] for r in rows]


# --- Préférences ---

def set_pref(username: str, key: str, value: str, path: Path | None = None) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO prefs (username, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(username, key) DO UPDATE SET value = excluded.value",
            (username, key, value),
        )


def get_pref(username: str, key: str, default: str = "", path: Path | None = None) -> str:
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT value FROM prefs WHERE username = ? AND key = ?", (username, key)
        ).fetchone()
    return row["value"] if row else default
