"""
Cerveau optionnel de l'assistant : un vrai LLM, **seulement si** une clé API est
fournie en variable d'environnement. Sinon, tout reste sur le moteur local.

- ANTHROPIC_API_KEY → Claude
- OPENAI_API_KEY → OpenAI

100 % stdlib (urllib). Tout échec retombe en silence sur `None` : l'assistant se
rabat alors sur sa base de connaissances locale. Jamais de conseil en
investissement (rappelé dans la consigne système).
"""

from __future__ import annotations

import json
import os
import urllib.request

SYSTEM = (
    "Tu es l'assistant pédagogique d'un outil de trading crypto ÉDUCATIF. "
    "Réponds en français, clairement et brièvement. Tu expliques les concepts "
    "(indicateurs, stratégies, risques, fiscalité, cadre légal). Tu ne donnes "
    "JAMAIS de conseil en investissement personnalisé ni de prédiction de prix, "
    "et tu rappelles que rien n'est un conseil. Si on te demande quoi acheter ou "
    "si un actif va monter, refuse poliment et explique comment l'utilisateur peut "
    "analyser par lui-même."
)


def available() -> str | None:
    """Renvoie 'anthropic', 'openai' ou None selon la clé présente."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def _post(url: str, headers: dict, payload: dict, timeout: int = 20) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read())


def _anthropic(question: str, context: str) -> str | None:
    key = os.environ["ANTHROPIC_API_KEY"]
    content = (f"{context}\n\n{question}" if context else question)
    data = _post(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        {"model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
         "max_tokens": 600, "system": SYSTEM,
         "messages": [{"role": "user", "content": content}]},
    )
    parts = data.get("content", [])
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return text.strip() or None


def _openai(question: str, context: str) -> str | None:
    key = os.environ["OPENAI_API_KEY"]
    content = (f"{context}\n\n{question}" if context else question)
    data = _post(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {key}", "content-type": "application/json"},
        {"model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), "max_tokens": 600,
         "messages": [{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": content}]},
    )
    return (data["choices"][0]["message"]["content"] or "").strip() or None


def ask(question: str, context: str = "") -> str | None:
    """Interroge le LLM si une clé est présente, sinon None. Ne lève jamais."""
    provider = available()
    if not provider:
        return None
    try:
        return _anthropic(question, context) if provider == "anthropic" else _openai(question, context)
    except Exception:
        return None
