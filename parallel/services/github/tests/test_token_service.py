from unittest.mock import Mock

import pytest

from app.services import crypto
from app.services.errors import InvalidTokenError
from app.services.token_service import TokenService


def _service():
    repository = Mock()
    github = Mock()
    return TokenService(repository, github), repository, github


def test_store_token_encrypts_and_upserts():
    service, repository, github = _service()
    github.get_authenticated_user.return_value = {"login": "octocat"}
    repository.upsert.return_value = Mock(token_hint="7890", github_login="octocat")

    result = service.store_token("user-1", "ghp_secretpat1234567890")

    github.get_authenticated_user.assert_called_once_with("ghp_secretpat1234567890")
    assert result == {"connected": True, "hint": "7890", "login": "octocat"}

    kwargs = repository.upsert.call_args.kwargs
    assert kwargs["user_id"] == "user-1"
    assert kwargs["token_hint"] == "7890"
    assert kwargs["github_login"] == "octocat"
    # stored value is ciphertext, never the raw PAT, and decrypts back to it
    assert kwargs["encrypted_token"] != "ghp_secretpat1234567890"
    assert crypto.decrypt(kwargs["encrypted_token"]) == "ghp_secretpat1234567890"


def test_store_token_rejects_invalid_pat():
    service, repository, github = _service()
    github.get_authenticated_user.side_effect = InvalidTokenError()

    with pytest.raises(InvalidTokenError):
        service.store_token("user-1", "bad-token")

    repository.upsert.assert_not_called()


def test_get_token_decrypts_stored_value():
    service, repository, _ = _service()
    repository.get.return_value = Mock(
        encrypted_token=crypto.encrypt("ghp_secretpat1234567890")
    )

    assert service.get_token("user-1") == "ghp_secretpat1234567890"


def test_get_token_returns_none_when_absent():
    service, repository, _ = _service()
    repository.get.return_value = None

    assert service.get_token("user-1") is None


def test_status_reports_disconnected_when_absent():
    service, repository, _ = _service()
    repository.get.return_value = None

    assert service.status("user-1") == {
        "connected": False,
        "hint": None,
        "login": None,
    }


def test_revoke_delegates_to_repository():
    service, repository, _ = _service()

    service.revoke("user-1")

    repository.delete.assert_called_once_with("user-1")
