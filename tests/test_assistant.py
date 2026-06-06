"""Tests de l'assistant pédagogique (moteur d'intentions déterministe)."""

from core import assistant


def test_rsi_reconnu():
    rep = assistant.answer("c'est quoi le RSI ?")
    assert "RSI" in rep
    assert "suracheté" in rep or "survendu" in rep


def test_accents_et_casse_ignores():
    # « suracheté » écrit sans accent et en majuscules doit matcher le RSI
    assert "RSI" in assistant.answer("PARLE MOI DU SURACHETE")


def test_macd_reconnu():
    assert "MACD" in assistant.answer("explique le macd")


def test_refus_de_conseil():
    rep = assistant.answer("Dois-je acheter du Bitcoin maintenant ?")
    low = rep.lower()
    assert "pas un conseil" in low or "pas te dire" in low


def test_trading_reel_renvoie_securite():
    rep = assistant.answer("comment activer le trading réel ?").lower()
    assert "verrouill" in rep or "heberge" in rep or "i_understand_real_money_risk" in rep


def test_legal_mentionne_amf_ou_mica():
    rep = assistant.answer("est-ce légal ?")
    assert "AMF" in rep or "MiCA" in rep


def test_question_vide():
    assert assistant.answer("   ").startswith("Pose-moi")


def test_fallback_sur_hors_sujet():
    rep = assistant.answer("quelle est la météo à Paris demain")
    assert "Aide" in rep or "FAQ" in rep


def test_suggestions_non_vides():
    sugg = assistant.suggestions()
    assert isinstance(sugg, list) and len(sugg) >= 3
    # chaque suggestion doit produire une réponse non vide
    for q in sugg:
        assert assistant.answer(q).strip()


# --- Capacités en direct (prix + actualités) ---------------------------------

def test_detect_prix_avec_symbole():
    assert assistant.detect("c'est quoi le prix du bitcoin ?") == ("price", "BTC/USDT")
    assert assistant.detect("combien vaut l'ethereum") == ("price", "ETH/USDT")


def test_detect_news():
    assert assistant.detect("quelles sont les news ?") == ("news", None)
    assert assistant.detect("quoi de neuf sur le marché") == ("news", None)
    assert assistant.detect("Les dernières actus crypto ?") == ("news", None)


def test_detect_rien_pour_question_statique():
    assert assistant.detect("c'est quoi le RSI") == (None, None)


def test_respond_prix_en_direct():
    rep = assistant.respond("prix du bitcoin", price_fn=lambda s: 61234.5)
    assert "BTC" in rep and "61" in rep


def test_respond_news_en_direct():
    fake = [{"title": "Titre test", "link": "https://x.test", "source": "Src"}]
    rep = assistant.respond("les news crypto", news_fn=lambda: fake)
    assert "Titre test" in rep and "https://x.test" in rep


def test_respond_se_rabat_sur_la_base_statique():
    # sans fournisseur live et hors intent live -> réponse statique RSI
    assert "RSI" in assistant.respond("c'est quoi le RSI", price_fn=lambda s: 1.0)


# --- Sentiment, détection d'actifs, escalade LLM -----------------------------

def test_detect_assets():
    found = assistant.detect_assets("Le Bitcoin et l'Ethereum montent, Solana suit")
    assert found == ["BTC/USDT", "ETH/USDT", "SOL/USDT"]


def test_detect_assets_aucun():
    assert assistant.detect_assets("Une journée calme sur les marchés") == []


def test_detect_sentiment():
    assert assistant.detect("le marché a-t-il peur ?") == ("sentiment", None)
    assert assistant.detect("fear and greed du jour") == ("sentiment", None)


def test_respond_sentiment():
    rep = assistant.respond("le marché a peur ?",
                            sentiment_fn=lambda: {"value": 25, "label_fr": "Peur"})
    assert "25" in rep and "Peur" in rep


def test_respond_llm_escalade_sur_question_inconnue():
    rep = assistant.respond("dissertation hors sujet totalement xyz",
                            llm_fn=lambda q: "Réponse de l'IA")
    assert "Réponse de l'IA" in rep


def test_respond_llm_pas_appele_si_match_statique():
    appels = {"n": 0}

    def fake_llm(q):
        appels["n"] += 1
        return "IA"

    rep = assistant.respond("c'est quoi le RSI", llm_fn=fake_llm)
    assert "RSI" in rep and appels["n"] == 0
