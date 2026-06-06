"""Tests des garde-fous de trading réel (limites, coupe-circuit, journal)."""

import pytest

from core import trading_guard as tg


def test_ordre_ok_dans_les_limites():
    g = tg.Guardrails(max_order_usdt=50, daily_loss_limit_usdt=100, max_trades_per_day=10)
    # Ne lève rien.
    tg.validate_order(g, order_value_usdt=20, trades_today=0, loss_today_usdt=0.0)


def test_ordre_trop_gros_refuse():
    g = tg.Guardrails(max_order_usdt=50)
    with pytest.raises(tg.GuardrailError):
        tg.validate_order(g, order_value_usdt=51)


def test_valeur_inconnue_refusee_par_securite():
    g = tg.Guardrails()
    with pytest.raises(tg.GuardrailError):
        tg.validate_order(g, order_value_usdt=0)


def test_trop_d_ordres_dans_la_journee():
    g = tg.Guardrails(max_trades_per_day=3)
    with pytest.raises(tg.GuardrailError):
        tg.validate_order(g, order_value_usdt=10, trades_today=3)


def test_perte_du_jour_depassee():
    g = tg.Guardrails(daily_loss_limit_usdt=100)
    with pytest.raises(tg.GuardrailError):
        tg.validate_order(g, order_value_usdt=10, loss_today_usdt=100)


def test_coupe_circuit_bloque_tout():
    g = tg.Guardrails()
    with pytest.raises(tg.GuardrailError):
        tg.validate_order(g, order_value_usdt=10, kill_switch=True)


def test_coupe_circuit_fichier(tmp_path):
    f = tmp_path / "KILL_SWITCH"
    assert tg.kill_switch_active(f) is False
    tg.engage_kill_switch("test", path=f)
    assert tg.kill_switch_active(f) is True
    tg.release_kill_switch(f)
    assert tg.kill_switch_active(f) is False
    tg.release_kill_switch(f)  # idempotent : pas d'erreur si déjà absent


def test_journal_ordres_du_jour(tmp_path):
    assert tg.today_stats(tmp_path)["trades"] == 0
    tg.record_trade(25.0, data_dir=tmp_path)
    tg.record_trade(15.0, realized_pnl_usdt=-5.0, data_dir=tmp_path)
    stats = tg.today_stats(tmp_path)
    assert stats["trades"] == 2
    assert stats["notional"] == pytest.approx(40.0)
    assert stats["loss"] == pytest.approx(5.0)


def test_guardrails_validate_rejette_valeurs_absurdes():
    with pytest.raises(ValueError):
        tg.Guardrails(max_order_usdt=0).validate()
    with pytest.raises(ValueError):
        tg.Guardrails(max_trades_per_day=0).validate()
