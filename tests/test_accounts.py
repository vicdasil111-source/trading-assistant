"""Tests des comptes utilisateurs (hachage, auth, watchlist, préférences)."""

import pytest

from core import accounts


@pytest.fixture
def db(tmp_path):
    """Base de test isolée (un fichier par test)."""
    return tmp_path / "accounts.db"


def test_creation_et_authentification(db):
    accounts.create_user("victor", "motdepasse1", email="v@example.com", path=db)
    assert accounts.authenticate("victor", "motdepasse1", path=db) is True
    assert accounts.authenticate("victor", "mauvais", path=db) is False
    assert accounts.authenticate("inconnu", "motdepasse1", path=db) is False


def test_mot_de_passe_jamais_en_clair(db):
    accounts.create_user("alice", "secret123", path=db)
    import sqlite3
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT pwd_hash, salt FROM users WHERE username='alice'").fetchone()
    pwd_hash, salt = row
    assert "secret123" not in pwd_hash      # haché, pas en clair
    assert len(salt) == 32                   # 16 octets en hexa


def test_doublon_refuse(db):
    accounts.create_user("bob", "azerty12", path=db)
    with pytest.raises(ValueError):
        accounts.create_user("bob", "autre123", path=db)


def test_validation_entrees(db):
    with pytest.raises(ValueError):
        accounts.create_user("ab", "azerty12", path=db)      # nom trop court
    with pytest.raises(ValueError):
        accounts.create_user("charlie", "123", path=db)      # mdp trop court
    with pytest.raises(ValueError):
        accounts.create_user("dora", "azerty12", email="pasunemail", path=db)


def test_watchlist(db):
    accounts.create_user("eve", "azerty12", path=db)
    accounts.add_watch("eve", "btc/usdt", path=db)           # normalisé en majuscules
    accounts.add_watch("eve", "ETH/USDT", path=db)
    accounts.add_watch("eve", "BTC/USDT", path=db)           # doublon ignoré
    assert accounts.get_watchlist("eve", path=db) == ["BTC/USDT", "ETH/USDT"]
    accounts.remove_watch("eve", "BTC/USDT", path=db)
    assert accounts.get_watchlist("eve", path=db) == ["ETH/USDT"]


def test_preferences(db):
    accounts.create_user("frank", "azerty12", path=db)
    assert accounts.get_pref("frank", "theme", default="dark", path=db) == "dark"
    accounts.set_pref("frank", "theme", "light", path=db)
    accounts.set_pref("frank", "theme", "light", path=db)    # upsert sans erreur
    assert accounts.get_pref("frank", "theme", path=db) == "light"


def test_sessions_persistantes(db):
    accounts.create_user("gaia", "azerty12", path=db)
    token = accounts.create_session("gaia", path=db)
    assert token
    assert accounts.session_user(token, path=db) == "gaia"
    accounts.delete_session(token, path=db)
    assert accounts.session_user(token, path=db) is None


def test_session_jeton_invalide(db):
    accounts.init_db(db)
    assert accounts.session_user("jeton-bidon", path=db) is None
    assert accounts.session_user("", path=db) is None


def test_hash_deterministe_avec_sel():
    h1 = accounts._hash("abc", "00ff")
    h2 = accounts._hash("abc", "00ff")
    h3 = accounts._hash("abc", "ff00")
    assert h1 == h2          # même mdp + même sel -> même hachage
    assert h1 != h3          # sel différent -> hachage différent
