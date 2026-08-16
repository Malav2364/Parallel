import httpx

from app.core.config import settings


class GoalsClient:
    def __init__(self) -> None:
        self.base_url = settings.GOALS_SERVICE_URL.rstrip("/")

    def create_goal(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        status: str = "active",
        target_date: str | None = None,
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/goals",
            headers={"X-User-Id": user_id},
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

    def list_goals(self, user_id: str) -> list[dict]:
        response = httpx.get(
            f"{self.base_url}/goals",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def get_by_name(self, user_id: str, name: str) -> dict | None:
        normalized_name = name.strip().casefold()
        return next(
            (
                goal
                for goal in self.list_goals(user_id)
                if goal.get("name", "").strip().casefold() == normalized_name
            ),
            None,
        )
