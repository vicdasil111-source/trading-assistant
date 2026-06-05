"""
Accès à Supabase (PostgREST) en bibliothèque standard — aucune dépendance.

Activé uniquement si les variables d'environnement SUPABASE_URL et SUPABASE_KEY
sont présentes. Sinon, le projet utilise SQLite (voir core/accounts.py).

On expose des opérations génériques (select / insert / upsert / delete) que
core/accounts.py utilise pour stocker comptes, sessions, watchlist, etc.
Les filtres suivent la syntaxe PostgREST : {"username": "eq.alice"}.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


def _creds() -> tuple[str | None, str | None]:
    return os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")


def enabled() -> bool:
    """True si Supabase est configuré (URL + clé présentes)."""
    url, key = _creds()
    return bool(url and key)


def _headers(prefer: str | None = None) -> dict:
    _, key = _creds()
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    return h


def _endpoint(table: str, params: dict | None = None) -> str:
    url, _ = _creds()
    base = f"{url.rstrip('/')}/rest/v1/{table}"
    if params:
        base += "?" + urllib.parse.urlencode(params)
    return base


def _request(method: str, table: str, params: dict | None = None,
             body=None, prefer: str | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(_endpoint(table, params), data=data,
                                 method=method, headers=_headers(prefer))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        raise RuntimeError(f"Supabase {exc.code} sur {table} : {detail}") from exc
    return json.loads(raw) if raw else []


def select(table: str, filters: dict | None = None, columns: str = "*",
           order: str | None = None) -> list[dict]:
    params = {"select": columns}
    if filters:
        params.update(filters)
    if order:
        params["order"] = order
    return _request("GET", table, params=params)


def insert(table: str, row: dict) -> None:
    _request("POST", table, body=row, prefer="return=minimal")


def upsert(table: str, row: dict, on_conflict: str, merge: bool = True) -> None:
    resolution = "merge-duplicates" if merge else "ignore-duplicates"
    _request("POST", table, params={"on_conflict": on_conflict}, body=row,
             prefer=f"resolution={resolution},return=minimal")


def delete(table: str, filters: dict) -> None:
    _request("DELETE", table, params=filters, prefer="return=minimal")
