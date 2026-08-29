import httpx
import pytest

from app.clients.github_client import GitHubClient


def _search_payload(number):
    url = f"https://github.com/acme/app/pull/{number}"
    return {
        "items": [
            {
                "html_url": url,
                "number": number,
                "title": f"PR {number}",
                "repository_url": "https://api.github.com/repos/acme/app",
                "user": {"login": "octocat"},
                "updated_at": "2026-08-29T00:00:00Z",
            }
        ]
    }


def test_list_review_requests_normalizes(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return httpx.Response(
            200, json=_search_payload(7), request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    signals = GitHubClient().list_review_requests("ghp_token")

    assert captured["url"].endswith("/search/issues")
    assert captured["params"]["q"] == "is:open is:pr review-requested:@me"
    assert captured["headers"]["Authorization"] == "Bearer ghp_token"

    assert signals == [
        {
            "external_id": "https://github.com/acme/app/pull/7",
            "kind": "review_request",
            "repo": "acme/app",
            "number": 7,
            "title": "PR 7",
            "url": "https://github.com/acme/app/pull/7",
            "author": "octocat",
            "updated_at": "2026-08-29T00:00:00Z",
        }
    ]


def test_list_my_open_prs_uses_author_query(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["params"] = params
        return httpx.Response(
            200, json=_search_payload(9), request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    signals = GitHubClient().list_my_open_prs("ghp_token")

    assert captured["params"]["q"] == "is:open is:pr author:@me"
    assert signals[0]["kind"] == "my_pr"


def test_get_authenticated_user_raises_on_bad_token(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(
            401,
            json={"message": "Bad credentials"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        GitHubClient().get_authenticated_user("bad-token")


def test_get_authenticated_user_returns_login(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(
            200, json={"login": "octocat"}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert GitHubClient().get_authenticated_user("ghp_token") == {"login": "octocat"}
