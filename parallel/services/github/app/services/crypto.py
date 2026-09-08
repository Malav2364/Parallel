from cryptography.fernet import Fernet

from app.core.config import settings


def _load_fernet() -> Fernet:
    key = settings.CONNECTOR_VAULT_KEY

    if not key:
        raise RuntimeError(
            "CONNECTOR_VAULT_KEY is not set; refusing to start the connector vault."
        )

    return Fernet(key.encode())


_fernet = _load_fernet()


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
