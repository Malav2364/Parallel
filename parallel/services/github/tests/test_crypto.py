import pytest

from app.services import crypto


def test_encrypt_decrypt_round_trip():
    secret = "ghp_examplepat1234567890"

    ciphertext = crypto.encrypt(secret)

    assert ciphertext != secret
    assert crypto.decrypt(ciphertext) == secret


def test_encrypt_is_non_deterministic():
    secret = "ghp_examplepat1234567890"

    assert crypto.encrypt(secret) != crypto.encrypt(secret)


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(crypto.settings, "CONNECTOR_VAULT_KEY", "")

    with pytest.raises(RuntimeError):
        crypto._load_fernet()
