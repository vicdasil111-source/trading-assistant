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
