import httpx

from app.core.config import settings


class NotificationsClient:
    def __init__(self) -> None:
        self.base_url = settings.NOTIFICATIONS_SERVICE_URL.rstrip("/")

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "reminder",
        priority: str = "normal",
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/notifications",
            headers={
                "X-User-Id": user_id,
            },
            json={
                "title": title,
                "message": message,
                "type": notification_type,
                "priority": priority,
            },
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()