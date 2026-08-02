from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.services.email_service import EmailService
from tests.database import (
    TestingSessionLocal,
    create_tables,
    drop_tables,
)


def override_get_db():
    db = TestingSessionLocal()

    print(">>> USING TEST DATABASE <<<")

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    drop_tables()
    create_tables()

    yield

    drop_tables()


@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    monkeypatch.setattr(
        EmailService,
        "send_verification_email",
        AsyncMock(),
    )

    monkeypatch.setattr(
        EmailService,
        "send_password_reset_email",
        AsyncMock(),
    )


@pytest.fixture(autouse=True)
def clean_database():
    db = TestingSessionLocal()

    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

    db.commit()
    db.close()
