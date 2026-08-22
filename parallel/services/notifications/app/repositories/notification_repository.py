from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        owner_id: str,
        title: str,
        message: str,
        notification_type: str,
        priority: str,
    ) -> Notification:
        notification = Notification(
            owner_id=owner_id,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            status="unread",
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

    def list_by_owner(
        self,
        owner_id: str,
    ) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.owner_id == owner_id)
            .order_by(Notification.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_by_id(
        self,
        notification_id: str,
        owner_id: str,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.owner_id == owner_id,
        )

        return self.db.scalar(statement)

    def mark_as_read(
        self,
        notification: Notification,
    ) -> Notification:
        notification.status = "read"
        notification.read_at = datetime.now().astimezone()

        self.db.commit()
        self.db.refresh(notification)

        return notification