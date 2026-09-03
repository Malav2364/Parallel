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
