"""
Sentiment du marché crypto : l'indice « Fear & Greed » (Peur & Avidité).

Source : API publique gratuite alternative.me (pas de clé). 100 % stdlib.
Purement informatif — ce n'est PAS un signal d'achat.
"""

from __future__ import annotations

import json
import urllib.request

FNG_URL = "https://api.alternative.me/fng/?limit=1"

_LABELS_FR = {
    "Extreme Fear": "Peur extrême",
    "Fear": "Peur",
    "Neutral": "Neutre",
    "Greed": "Avidité",
    "Extreme Greed": "Avidité extrême",
}

_HEADERS = {"User-Agent": "Mozilla/5.0 (TradingAssistant/1.0)", "Accept": "application/json"}


def parse_fng(raw) -> dict:
    """Extrait {value:int, label:str, label_fr:str} d'une réponse alternative.me.
    Pur → testable hors-ligne."""
    data = json.loads(raw) if isinstance(raw, (str, bytes, bytearray)) else raw
    entry = (data.get("data") or [{}])[0]
    value = int(float(entry.get("value", 0)))
    label = (entry.get("value_classification") or "").strip()
    return {"value": value, "label": label, "label_fr": _LABELS_FR.get(label, label or "—")}


def fear_greed() -> dict | None:
    """Renvoie l'indice du jour, ou None si indisponible (réseau coupé)."""
    try:
        req = urllib.request.Request(FNG_URL, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:  # noqa: S310
            return parse_fng(resp.read())
    except Exception:
        return None
