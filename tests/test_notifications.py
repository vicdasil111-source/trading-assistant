"""Tests du module de notifications/alertes (sans réseau)."""

import pandas as pd

from utils import notifications
from utils.config import Config


def _df(close, rsi, signal=None):
    data = {"close": close, "rsi": rsi}
    if signal is not None:
        data["signal"] = signal
    return pd.DataFrame(data)


def test_alerte_surachat():
    df = _df(close=[100, 105], rsi=[50, 80])  # RSI 80 > 70
    alertes = notifications.build_alerts(df)
    assert any("SURACHAT" in a for a in alertes)


def test_alerte_survente():
    df = _df(close=[100, 95], rsi=[50, 20])  # RSI 20 < 30
    alertes = notifications.build_alerts(df)
    assert any("SURVENTE" in a for a in alertes)


def test_pas_d_alerte_en_zone_neutre():
    df = _df(close=[100, 101], rsi=[50, 55])
    alertes = notifications.build_alerts(df)
    assert alertes == []


def test_alerte_signal_achat():
    df = _df(close=[100, 101], rsi=[50, 50], signal=[0, 1])
    alertes = notifications.build_alerts(df)
    assert any("ACHAT" in a for a in alertes)


def test_seuils_personnalises():
    cfg = Config(rsi_overbought=60)
    df = _df(close=[100, 101], rsi=[50, 65])  # 65 > 60 (seuil custom)
    alertes = notifications.build_alerts(df, config=cfg)
    assert any("SURACHAT" in a for a in alertes)


def test_telegram_renvoie_false_sans_configuration(monkeypatch):
    # Sans variables d'environnement, l'envoi Telegram échoue proprement (False).
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert notifications.send_telegram("test") is False


def test_dataframe_vide_ne_plante_pas():
    df = pd.DataFrame({"close": [], "rsi": []})
    assert notifications.build_alerts(df) == []
