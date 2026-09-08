import httpx

from app.core.config import settings


class GoalsClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.GOALS_SERVICE_URL.rstrip("/")
        self._client = client

    async def create_goal(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        status: str = "active",
        target_date: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}

        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        response = await self._client.post(
            f"{self.base_url}/goals",
            headers=headers,
            json={
                "name": name,
                "description": description,
                "status": status,
                "target_date": target_date,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def list_goals(self, user_id: str) -> list[dict]:
        response = await self._client.get(
            f"{self.base_url}/goals",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_by_name(self, user_id: str, name: str) -> dict | None:
        normalized_name = name.strip().casefold()
        goals = await self.list_goals(user_id)
        return next(
            (
                goal
                for goal in goals
                if goal.get("name", "").strip().casefold() == normalized_name
            ),
            None,
        )
