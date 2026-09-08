import httpx

from app.core.config import settings


class HabitsClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.HABITS_SERVICE_URL.rstrip("/")
        self._client = client

    async def create_habit(
        self,
        user_id: str,
        name: str,
        schedule: str,
        description: str | None = None,
        time_window: str | None = None,
        status: str = "active",
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}

        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        response = await self._client.post(
            f"{self.base_url}/habits",
            headers=headers,
            json={
                "name": name,
                "description": description,
                "schedule": schedule,
                "time_window": time_window,
                "status": status,
            },
            timeout=10.0,
        )

        response.raise_for_status()
        return response.json()

    async def list_habits(
        self,
        user_id: str,
    ) -> list[dict]:
        response = await self._client.get(
            f"{self.base_url}/habits",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )

        response.raise_for_status()
        return response.json()

    async def get_by_name(
        self,
        user_id: str,
        name: str,
    ) -> dict | None:
        normalized_name = name.strip().casefold()

        habits = await self.list_habits(user_id)

        return next(
            (
                habit
                for habit in habits
                if habit.get("name", "").strip().casefold() == normalized_name
            ),
            None,
        )
