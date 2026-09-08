import httpx

from app.core.config import settings


class RemindersClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.REMINDERS_SERVICE_URL.rstrip("/")
        self._client = client

    async def create_reminder(
        self,
        user_id: str,
        title: str,
        scheduled_for: str,
        description: str | None = None,
        recurrence: str | None = None,
        status: str = "pending",
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}

        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        response = await self._client.post(
            f"{self.base_url}/reminders",
            headers=headers,
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

    async def get_reminder(
        self,
        user_id: str,
        reminder_id: str,
    ) -> dict | None:
        """Fetch a single reminder by id, or ``None`` if it does not exist.

        Used to read a write back and confirm it actually persisted.
        """

        response = await self._client.get(
            f"{self.base_url}/reminders/{reminder_id}",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

    async def get_by_details(
        self,
        user_id: str,
        title: str,
        scheduled_for: str,
    ):
        response = await self._client.get(
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
                reminder.get("title", "").strip().casefold() == title.strip().casefold()
                and reminder.get("scheduled_for") == scheduled_for
            ):
                return reminder

        return None
