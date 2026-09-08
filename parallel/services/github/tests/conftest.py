import os

from cryptography.fernet import Fernet

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("CONNECTOR_VAULT_KEY", Fernet.generate_key().decode())

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
