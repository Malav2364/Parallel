import httpx

from app.core.config import settings


class RemindersClient:
    def __init__(self) -> None:
        self.base_url = settings.REMINDERS_SERVICE_URL.rstrip("/")

    def create_reminder(
        self,
        user_id: str,
        title: str,
        scheduled_for: str,
        description: str | None = None,
        recurrence: str | None = None,
        status: str = "pending",
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/reminders",
            headers={"X-User-Id": user_id},
            json={
                "title": title,
                "description": description,
                "scheduled_for": scheduled_for,
                "recurrence": recurrence,
                "status": status,
            },
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()

    def get_by_details(
        self,
        user_id: str,
        title: str,
        scheduled_for: str,
    ):
        response = httpx.get(
            f"{self.base_url}/reminders",
            headers={
                "X-User-Id": user_id,
            },
            timeout=10.0,
        )

        response.raise_for_status()

        reminders = response.json()

        for reminder in reminders:
            if (
                reminder.get("title", "").strip().casefold()
                == title.strip().casefold()
                and reminder.get("scheduled_for")
                == scheduled_for
            ):
                return reminder

        return None