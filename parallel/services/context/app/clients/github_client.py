import httpx

from app.core.config import settings


class GithubClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.GITHUB_SERVICE_URL.rstrip("/")
        self._client = client

    async def list_signals(
        self,
        user_id: str,
        unread: bool = False,
    ) -> list[dict]:
        response = await self._client.get(
            f"{self.base_url}/signals",
            params={"unread": unread},
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_status(self, user_id: str) -> dict:
        response = await self._client.get(
            f"{self.base_url}/status",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def post_comment(
        self,
        user_id: str,
        repo: str,
        number: int,
        body: str,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = await self._client.post(
            f"{self.base_url}/comments",
            headers=headers,
            json={"repo": repo, "number": number, "body": body},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def approve_pr(
        self,
        user_id: str,
        repo: str,
        number: int,
        body: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = await self._client.post(
            f"{self.base_url}/reviews",
            headers=headers,
            json={"repo": repo, "number": number, "body": body},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def merge_pr(
        self,
        user_id: str,
        repo: str,
        number: int,
        merge_method: str,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = await self._client.post(
            f"{self.base_url}/merges",
            headers=headers,
            json={"repo": repo, "number": number, "merge_method": merge_method},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def close_pr(
        self,
        user_id: str,
        repo: str,
        number: int,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = await self._client.post(
            f"{self.base_url}/closures",
            headers=headers,
            json={"repo": repo, "number": number},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
