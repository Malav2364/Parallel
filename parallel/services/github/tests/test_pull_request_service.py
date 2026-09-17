from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.repositories import IdempotencyRepository
from app.services.errors import GithubWriteError, NotConnectedError
from app.services.pull_request_service import PullRequestService


def _memory_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _review():
    return {"id": 987, "state": "APPROVED"}


def _merge():
    return {
        "merged": True,
        "sha": "abc123",
        "message": "Pull Request successfully merged",
    }


def _closure():
    return {"number": 42, "state": "closed"}


def _service(github, token="ghp_token"):
    token_service = Mock()
    token_service.get_token.return_value = token
    idempotency = IdempotencyRepository(_memory_session())
    return PullRequestService(idempotency, token_service, github)


def test_approve_stores_and_returns_response():
    github = Mock()
    github.create_pull_review.return_value = _review()
    service = _service(github)

    result = service.approve("user-1", "acme/app", 42, body="nice work")

    assert result == _review()
    github.create_pull_review.assert_called_once_with(
        "ghp_token", "acme/app", 42, event="APPROVE", body="nice work"
    )


def test_merge_stores_and_returns_response():
    github = Mock()
    github.merge_pull.return_value = _merge()
    service = _service(github)

    result = service.merge("user-1", "acme/app", 42, merge_method="squash")

    assert result == _merge()
    github.merge_pull.assert_called_once_with("ghp_token", "acme/app", 42, "squash")


def test_close_stores_and_returns_response():
    github = Mock()
    github.close_pull.return_value = _closure()
    service = _service(github)

    result = service.close("user-1", "acme/app", 42)

    assert result == _closure()
    github.close_pull.assert_called_once_with("ghp_token", "acme/app", 42)


def test_replayed_approve_returns_stored_without_recalling():
    github = Mock()
    github.create_pull_review.return_value = _review()
    service = _service(github)

    first = service.approve("user-1", "acme/app", 42)
    second = service.approve("user-1", "acme/app", 42)

    assert first == second == _review()
    github.create_pull_review.assert_called_once()


def test_replayed_merge_returns_stored_without_recalling():
    github = Mock()
    github.merge_pull.return_value = _merge()
    service = _service(github)

    first = service.merge("user-1", "acme/app", 42, merge_method="merge")
    second = service.merge("user-1", "acme/app", 42, merge_method="merge")

    assert first == second == _merge()
    # A retried merge is served from the ledger -- the PR is merged exactly once.
    github.merge_pull.assert_called_once()


def test_replayed_close_returns_stored_without_recalling():
    github = Mock()
    github.close_pull.return_value = _closure()
    service = _service(github)

    first = service.close("user-1", "acme/app", 42)
    second = service.close("user-1", "acme/app", 42)

    assert first == second == _closure()
    github.close_pull.assert_called_once()


def test_different_merge_method_derives_different_key_and_recalls():
    github = Mock()
    github.merge_pull.return_value = _merge()
    service = _service(github)

    service.merge("user-1", "acme/app", 42, merge_method="merge")
    service.merge("user-1", "acme/app", 42, merge_method="squash")

    # Method is part of the key, so a different method is a distinct write.
    assert github.merge_pull.call_count == 2


def test_missing_token_raises_not_connected():
    github = Mock()
    service = _service(github, token=None)

    with pytest.raises(NotConnectedError):
        service.merge("user-1", "acme/app", 42)

    github.merge_pull.assert_not_called()


def test_write_failure_raises_github_write_error():
    request = httpx.Request("PUT", "https://api.github.com")
    github = Mock()
    github.merge_pull.side_effect = httpx.HTTPStatusError(
        "method not allowed",
        request=request,
        response=httpx.Response(405, request=request),
    )
    service = _service(github)

    with pytest.raises(GithubWriteError):
        service.merge("user-1", "acme/app", 42)
