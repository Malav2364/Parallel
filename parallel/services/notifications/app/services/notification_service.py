from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
    ) -> None:
        self.repository = repository

    def create_notification(
        self,
        request: NotificationCreate,
        owner_id: str,
    ) -> NotificationResponse:
        notification = self.repository.create(
            owner_id=owner_id,
            title=request.title,
            message=request.message,
            notification_type=request.type,
            priority=request.priority,
        )

        return NotificationResponse.model_validate(notification)

    def list_notifications(
        self,
        owner_id: str,
    ) -> list[NotificationResponse]:
        notifications = self.repository.list_by_owner(owner_id)

        return [
            NotificationResponse.model_validate(notification)
            for notification in notifications
        ]

    def get_notification(
        self,
        notification_id: str,
        owner_id: str,
    ) -> NotificationResponse | None:
        notification = self.repository.get_by_id(
            notification_id=notification_id,
            owner_id=owner_id,
        )

        if notification is None:
            return None

        return NotificationResponse.model_validate(notification)

    def mark_as_read(
        self,
        notification_id: str,
        owner_id: str,
    ) -> NotificationResponse | None:
        notification = self.repository.get_by_id(
            notification_id=notification_id,
            owner_id=owner_id,
        )

        if notification is None:
            return None

        notification = self.repository.mark_as_read(notification)

        return NotificationResponse.model_validate(notification)