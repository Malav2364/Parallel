import httpx

GITHUB_API = "https://api.github.com"
API_VERSION = "2022-11-28"
TIMEOUT = 10.0


class GitHubClient:
    """First-party GitHub read-client.

    Method names are shaped like the future MCP tools (the seam we grow into an
    MCP host later): each returns already-normalized signal dicts.
    """

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }

    def get_authenticated_user(self, token: str) -> dict:
        response = httpx.get(
            f"{GITHUB_API}/user",
            headers=self._headers(token),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def list_review_requests(self, token: str) -> list[dict]:
        return self._search(
            "is:open is:pr review-requested:@me",
            "review_request",
            token,
        )

    def list_my_open_prs(self, token: str) -> list[dict]:
        return self._search(
            "is:open is:pr author:@me",
            "my_pr",
            token,
        )

    def _search(self, query: str, kind: str, token: str) -> list[dict]:
        response = httpx.get(
            f"{GITHUB_API}/search/issues",
            params={"q": query},
            headers=self._headers(token),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        return [self._normalize(item, kind) for item in items]

    @staticmethod
    def _normalize(item: dict, kind: str) -> dict:
        repository_url = item.get("repository_url") or ""
        repo = repository_url.split("/repos/")[-1] if repository_url else ""
        user = item.get("user") or {}
        return {
            "external_id": item.get("html_url", ""),
            "kind": kind,
            "repo": repo,
            "number": item.get("number"),
            "title": item.get("title"),
            "url": item.get("html_url", ""),
            "author": user.get("login"),
            "updated_at": item.get("updated_at"),
        }
