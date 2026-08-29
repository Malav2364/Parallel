from unittest.mock import Mock

import pytest

from app.api.deps import get_signal_service, get_token_service
from app.main import app
from app.services.errors import InvalidTokenError, NotConnectedError

HEADERS = {"X-User-Id": "user-1"}


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_connect_token_returns_status_without_echoing_pat(client):
    fake = Mock()
    fake.store_token.return_value = {
        "connected": True,
        "hint": "7890",
        "login": "octocat",
    }
    app.dependency_overrides[get_token_service] = lambda: fake

    response = client.post(
        "/api/v1/github/token",
        headers=HEADERS,
        json={"pat": "ghp_secretpat1234567890"},
    )

    assert response.status_code == 200
    assert response.json() == {"connected": True, "hint": "7890", "login": "octocat"}
    # the raw PAT must never appear in the response body
    assert "ghp_secretpat1234567890" not in response.text
    fake.store_token.assert_called_once_with("user-1", "ghp_secretpat1234567890")


def test_connect_token_rejects_invalid_pat(client):
    fake = Mock()
    fake.store_token.side_effect = InvalidTokenError()
    app.dependency_overrides[get_token_service] = lambda: fake

    response = client.post(
        "/api/v1/github/token",
        headers=HEADERS,
        json={"pat": "bad"},
    )

    assert response.status_code == 400


def test_status_reports_connection(client):
    fake = Mock()
    fake.status.return_value = {"connected": False, "hint": None, "login": None}
    app.dependency_overrides[get_token_service] = lambda: fake

    response = client.get("/api/v1/github/status", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_disconnect_token_returns_204(client):
    fake = Mock()
    app.dependency_overrides[get_token_service] = lambda: fake

    response = client.delete("/api/v1/github/token", headers=HEADERS)

    assert response.status_code == 204
    fake.revoke.assert_called_once_with("user-1")


def test_sync_returns_counts(client):
    fake = Mock()
    fake.sync.return_value = {"review_requests": 2, "my_prs": 1}
    app.dependency_overrides[get_signal_service] = lambda: fake

    response = client.post("/api/v1/github/sync", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {"review_requests": 2, "my_prs": 1}


def test_sync_requires_connection(client):
    fake = Mock()
    fake.sync.side_effect = NotConnectedError()
    app.dependency_overrides[get_signal_service] = lambda: fake

    response = client.post("/api/v1/github/sync", headers=HEADERS)

    assert response.status_code == 409


def test_list_signals_passes_unread_filter(client):
    fake = Mock()
    fake.list_signals.return_value = []
    app.dependency_overrides[get_signal_service] = lambda: fake

    response = client.get("/api/v1/github/signals?unread=true", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == []
    fake.list_signals.assert_called_once_with("user-1", unread_only=True)
