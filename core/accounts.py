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

from core import supabase_store as sb
from utils.config import DATA_DIR

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _use_supabase(path: Path | None) -> bool:
    """Supabase est utilisé quand aucun chemin SQLite explicite n'est donné
    (les tests passent un chemin) ET que Supabase est configuré."""
    return path is None and sb.enabled()


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
            CREATE TABLE IF NOT EXISTS holdings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL,
                symbol    TEXT NOT NULL,
                quantity  REAL NOT NULL,
                buy_price REAL NOT NULL,
                added_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL,
                symbol    TEXT NOT NULL,
                kind      TEXT NOT NULL,
                threshold REAL NOT NULL,
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

    salt = secrets.token_hex(16)
    pwd_hash = _hash(password, salt)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = {"username": username, "email": email, "salt": salt,
           "pwd_hash": pwd_hash, "created_at": created}

    if _use_supabase(path):
        if sb.select("users", {"username": f"eq.{username}"}, "username"):
            raise ValueError("Ce nom d'utilisateur est déjà pris.")
        sb.insert("users", row)
        return

    init_db(path)
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
    username = username.strip()
    if _use_supabase(path):
        rows = sb.select("users", {"username": f"eq.{username}"}, "salt,pwd_hash")
        if not rows:
            return False
        candidate = _hash(password, rows[0]["salt"])
        return hmac.compare_digest(candidate, rows[0]["pwd_hash"])

    init_db(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT salt, pwd_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return False
    candidate = _hash(password, row["salt"])
    return hmac.compare_digest(candidate, row["pwd_hash"])


def user_exists(username: str, path: Path | None = None) -> bool:
    username = username.strip()
    if _use_supabase(path):
        return bool(sb.select("users", {"username": f"eq.{username}"}, "username"))
    init_db(path)
    with _connect(path) as conn:
        return conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone() is not None


# --- Sessions (connexion persistante par jeton) ---

def create_session(username: str, path: Path | None = None) -> str:
    """Crée un jeton de session aléatoire pour l'utilisateur et le renvoie."""
    token = secrets.token_urlsafe(24)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if _use_supabase(path):
        sb.insert("sessions", {"token": token, "username": username, "created_at": created})
        return token
    init_db(path)
    with _connect(path) as conn:
        conn.execute("INSERT INTO sessions (token, username, created_at) VALUES (?, ?, ?)",
                     (token, username, created))
    return token


def session_user(token: str, path: Path | None = None) -> str | None:
    """Renvoie l'utilisateur associé à un jeton, ou None s'il est invalide."""
    if not token:
        return None
    if _use_supabase(path):
        rows = sb.select("sessions", {"token": f"eq.{token}"}, "username")
        return rows[0]["username"] if rows else None
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT username FROM sessions WHERE token = ?", (token,)).fetchone()
    return row["username"] if row else None


def delete_session(token: str, path: Path | None = None) -> None:
    if not token:
        return
    if _use_supabase(path):
        sb.delete("sessions", {"token": f"eq.{token}"})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# --- Watchlist ---

def add_watch(username: str, symbol: str, path: Path | None = None) -> None:
    symbol = symbol.upper().strip()
    if _use_supabase(path):
        sb.upsert("watchlist", {"username": username, "symbol": symbol},
                  on_conflict="username,symbol", merge=False)
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("INSERT OR IGNORE INTO watchlist (username, symbol) VALUES (?, ?)",
                     (username, symbol))


def remove_watch(username: str, symbol: str, path: Path | None = None) -> None:
    symbol = symbol.upper().strip()
    if _use_supabase(path):
        sb.delete("watchlist", {"username": f"eq.{username}", "symbol": f"eq.{symbol}"})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM watchlist WHERE username = ? AND symbol = ?",
                     (username, symbol))


def get_watchlist(username: str, path: Path | None = None) -> list[str]:
    if _use_supabase(path):
        rows = sb.select("watchlist", {"username": f"eq.{username}"}, "symbol", order="symbol")
        return [r["symbol"] for r in rows]
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT symbol FROM watchlist WHERE username = ? ORDER BY symbol", (username,)
        ).fetchall()
    return [r["symbol"] for r in rows]


# --- Portefeuille manuel (holdings) ---

def add_holding(username: str, symbol: str, quantity: float, buy_price: float,
                path: Path | None = None) -> None:
    if quantity <= 0 or buy_price <= 0:
        raise ValueError("Quantité et prix d'achat doivent être positifs.")
    symbol = symbol.upper().strip()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if _use_supabase(path):
        sb.insert("holdings", {"username": username, "symbol": symbol,
                               "quantity": float(quantity), "buy_price": float(buy_price),
                               "added_at": created})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO holdings (username, symbol, quantity, buy_price, added_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, symbol, float(quantity), float(buy_price), created),
        )


def get_holdings(username: str, path: Path | None = None) -> list[dict]:
    if _use_supabase(path):
        return sb.select("holdings", {"username": f"eq.{username}"},
                         "id,symbol,quantity,buy_price", order="symbol")
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, symbol, quantity, buy_price FROM holdings WHERE username = ? "
            "ORDER BY symbol", (username,)
        ).fetchall()
    return [dict(r) for r in rows]


def remove_holding(username: str, holding_id: int, path: Path | None = None) -> None:
    if _use_supabase(path):
        sb.delete("holdings", {"username": f"eq.{username}", "id": f"eq.{holding_id}"})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM holdings WHERE username = ? AND id = ?",
                     (username, holding_id))


# --- Alertes de prix / RSI ---

def add_alert(username: str, symbol: str, kind: str, threshold: float,
              path: Path | None = None) -> None:
    symbol = symbol.upper().strip()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if _use_supabase(path):
        sb.insert("alerts", {"username": username, "symbol": symbol, "kind": kind,
                             "threshold": float(threshold), "created_at": created})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO alerts (username, symbol, kind, threshold, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, symbol, kind, float(threshold), created),
        )


def get_alerts(username: str, path: Path | None = None) -> list[dict]:
    if _use_supabase(path):
        return sb.select("alerts", {"username": f"eq.{username}"},
                         "id,symbol,kind,threshold", order="symbol")
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, symbol, kind, threshold FROM alerts WHERE username = ? "
            "ORDER BY symbol", (username,)
        ).fetchall()
    return [dict(r) for r in rows]


def remove_alert(username: str, alert_id: int, path: Path | None = None) -> None:
    if _use_supabase(path):
        sb.delete("alerts", {"username": f"eq.{username}", "id": f"eq.{alert_id}"})
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM alerts WHERE username = ? AND id = ?",
                     (username, alert_id))


# --- Préférences ---

def set_pref(username: str, key: str, value: str, path: Path | None = None) -> None:
    if _use_supabase(path):
        sb.upsert("prefs", {"username": username, "key": key, "value": value},
                  on_conflict="username,key", merge=True)
        return
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO prefs (username, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(username, key) DO UPDATE SET value = excluded.value",
            (username, key, value),
        )


def get_pref(username: str, key: str, default: str = "", path: Path | None = None) -> str:
    if _use_supabase(path):
        rows = sb.select("prefs", {"username": f"eq.{username}", "key": f"eq.{key}"}, "value")
        return rows[0]["value"] if rows else default
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT value FROM prefs WHERE username = ? AND key = ?", (username, key)
        ).fetchone()
    return row["value"] if row else default
