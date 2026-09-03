"""GET /briefing composes the github reads and never 500s on a connector fault.

Endpoint tests in the house style (``tests/test_process_endpoint.py``): a
dependency-override fake for the GithubClient, not httpx transport mocking. The
fake records whether ``get_status`` was consulted so a test can prove the
non-empty-signals path short-circuits the extra round trip.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_github_client
from app.main import app

BRIEFING_URL = "/api/v1/context/briefing"
HEADERS = {"X-User-Id": "user-1"}


def _signal(kind: str, **payload) -> dict:
    return {"kind": kind, "payload": payload}


class FakeGithubClient:
    def __init__(self, signals=None, status=None, raise_error=False) -> None:
        self._signals = signals or []
        self._status = status or {}
        self._raise = raise_error
        self.status_calls = 0

    async def list_signals(self, user_id, unread=False):
        if self._raise:
            raise httpx.HTTPError("connector down")
        return self._signals

    async def get_status(self, user_id):
        self.status_calls += 1
        return self._status


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _use(fake: FakeGithubClient) -> None:
    app.dependency_overrides[get_github_client] = lambda: fake


def test_signals_present_compose_briefing_without_status_call() -> None:
    fake = FakeGithubClient(
        signals=[
            _signal("review_request", repo="me/api", number=12, url="https://x/12"),
            _signal("review_request", repo="me/api", number=13, url="https://x/13"),
            _signal("my_pr", repo="me/web", number=7, url="https://x/7"),
        ],
    )
    _use(fake)

    with TestClient(app) as client:
        response = client.get(BRIEFING_URL, headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["review_requests"] == 2
    assert body["my_open_prs"] == 1
    assert body["message"] == "2 PRs waiting on your review, and 1 of your own is open."
    assert len(body["review_requests_items"]) == 2
    assert body["review_requests_items"][0]["number"] == 12
    assert body["my_pr_items"][0]["repo"] == "me/web"
    # Non-empty signals short-circuit the extra /status round trip.
    assert fake.status_calls == 0


def test_no_signals_calls_status_and_reports_caught_up_when_connected() -> None:
    fake = FakeGithubClient(signals=[], status={"connected": True})
    _use(fake)

    with TestClient(app) as client:
        response = client.get(BRIEFING_URL, headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["review_requests"] == 0
    assert body["my_open_prs"] == 0
    assert (
        body["message"]
        == "You're all caught up — nothing on GitHub needs you right now."
    )
    # Empty signals: /status is consulted to tell connected from caught-up.
    assert fake.status_calls == 1


def test_no_signals_and_not_connected_prompts_to_connect() -> None:
    fake = FakeGithubClient(signals=[], status={"connected": False})
    _use(fake)

    with TestClient(app) as client:
        response = client.get(BRIEFING_URL, headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["message"] == "Connect GitHub to see your pull requests."
    assert fake.status_calls == 1


def test_connector_down_degrades_to_not_connected_never_500() -> None:
    fake = FakeGithubClient(raise_error=True)
    _use(fake)

    with TestClient(app) as client:
        response = client.get(BRIEFING_URL, headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["review_requests"] == 0
    assert body["my_open_prs"] == 0
    assert body["message"] == "Connect GitHub to see your pull requests."
