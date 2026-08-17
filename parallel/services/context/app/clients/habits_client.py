import httpx

from app.core.config import settings


class HabitsClient:
    def __init__(self) -> None:
        self.base_url = settings.HABITS_SERVICE_URL.rstrip("/")

    def create_habit(
        self,
        user_id: str,
        name: str,
        schedule: str,
        description: str | None = None,
        time_window: str | None = None,
        status: str = "active",
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/habits",
            headers={"X-User-Id": user_id},
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

    def list_habits(
        self,
        user_id: str,
    ) -> list[dict]:
        response = httpx.get(
            f"{self.base_url}/habits",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )

        response.raise_for_status()
        return response.json()

    def get_by_name(
        self,
        user_id: str,
        name: str,
    ) -> dict | None:
        normalized_name = name.strip().casefold()

        return next(
            (
                habit
                for habit in self.list_habits(user_id)
                if habit.get("name", "").strip().casefold()
                == normalized_name
            ),
            None,
        )