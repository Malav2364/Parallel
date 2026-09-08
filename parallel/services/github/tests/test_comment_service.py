from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.repositories import IdempotencyRepository
from app.services.comment_service import CommentService
from app.services.errors import GithubWriteError, NotConnectedError


def _memory_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _comment(body="LGTM"):
    return {
        "id": 555,
        "html_url": "https://github.com/acme/app/pull/42#issuecomment-555",
        "body": body,
    }


def _service(github, token="ghp_token"):
    token_service = Mock()
    token_service.get_token.return_value = token
    idempotency = IdempotencyRepository(_memory_session())
    return CommentService(idempotency, token_service, github)


def test_post_comment_stores_and_returns_response():
    github = Mock()
    github.create_issue_comment.return_value = _comment()
    service = _service(github)

    result = service.post_comment("user-1", "acme/app", 42, "LGTM")

    assert result == _comment()
    github.create_issue_comment.assert_called_once_with(
        "ghp_token", "acme/app", 42, "LGTM"
    )


def test_replayed_key_returns_stored_without_reposting():
    github = Mock()
    github.create_issue_comment.return_value = _comment()
    service = _service(github)

    first = service.post_comment("user-1", "acme/app", 42, "LGTM")
    second = service.post_comment("user-1", "acme/app", 42, "LGTM")

    assert first == second == _comment()
    # The retry is served from the ledger -- GitHub is written to exactly once.
    github.create_issue_comment.assert_called_once()


def test_missing_token_raises_not_connected():
    github = Mock()
    service = _service(github, token=None)

    with pytest.raises(NotConnectedError):
        service.post_comment("user-1", "acme/app", 42, "LGTM")

    github.create_issue_comment.assert_not_called()


def test_write_failure_raises_github_write_error():
    request = httpx.Request("POST", "https://api.github.com")
    github = Mock()
    github.create_issue_comment.side_effect = httpx.HTTPStatusError(
        "denied",
        request=request,
        response=httpx.Response(403, request=request),
    )
    service = _service(github)

    with pytest.raises(GithubWriteError):
        service.post_comment("user-1", "acme/app", 42, "LGTM")
