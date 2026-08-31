from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import GithubSignal
from app.repositories import SignalRepository
from app.services.errors import NotConnectedError
from app.services.signal_service import SignalService


def _item(number, kind="review_request"):
    url = f"https://github.com/acme/app/pull/{number}"
    return {
        "external_id": url,
        "kind": kind,
        "repo": "acme/app",
        "number": number,
        "title": f"PR {number}",
        "url": url,
        "author": "octocat",
        "updated_at": "2026-08-29T00:00:00Z",
    }


def _memory_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_sync_requires_a_connected_token():
    repository = Mock()
    token_service = Mock()
    token_service.get_token.return_value = None
    service = SignalService(repository, token_service, Mock())

    with pytest.raises(NotConnectedError):
        service.sync("user-1")

    repository.upsert.assert_not_called()


def test_sync_upserts_each_signal_and_counts():
    repository = Mock()
    token_service = Mock()
    token_service.get_token.return_value = "ghp_token"
    github = Mock()
    github.list_review_requests.return_value = [_item(1)]
    github.list_my_open_prs.return_value = [_item(2, kind="my_pr")]
    service = SignalService(repository, token_service, github)

    result = service.sync("user-1")

    assert result == {"review_requests": 1, "my_prs": 1}
    assert repository.upsert.call_count == 2

    first = repository.upsert.call_args_list[0].kwargs
    assert first["kind"] == "review_request"
    assert first["external_id"] == "https://github.com/acme/app/pull/1"
    assert first["payload"]["repo"] == "acme/app"
    # payload carries only the whitelisted fields, not kind/external_id
    assert "kind" not in first["payload"]
    assert "external_id" not in first["payload"]


def test_resync_dedupes_on_external_id():
    session = _memory_session()
    repository = SignalRepository(session)

    _, created_first = repository.upsert(
        user_id="user-1",
        kind="review_request",
        external_id="https://github.com/acme/app/pull/1",
        payload={"title": "PR 1"},
    )
    _, created_second = repository.upsert(
        user_id="user-1",
        kind="review_request",
        external_id="https://github.com/acme/app/pull/1",
        payload={"title": "PR 1 (updated)"},
    )

    assert created_first is True
    assert created_second is False

    rows = session.scalars(select(GithubSignal)).all()
    assert len(rows) == 1
    assert rows[0].payload["title"] == "PR 1 (updated)"


def test_list_unnotified_and_mark_notified():
    from datetime import datetime, timezone

    session = _memory_session()
    repository = SignalRepository(session)

    signal, _ = repository.upsert(
        user_id="user-1",
        kind="review_request",
        external_id="https://github.com/acme/app/pull/1",
        payload={"title": "PR 1"},
    )

    pending = repository.list_unnotified("user-1", "review_request")
    assert [s.id for s in pending] == [signal.id]

    repository.mark_notified([signal.id], datetime.now(timezone.utc))

    assert repository.list_unnotified("user-1", "review_request") == []
