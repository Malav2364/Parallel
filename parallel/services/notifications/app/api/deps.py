from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.notification_repository import (
    NotificationRepository,
)
from app.services.notification_service import NotificationService


def get_notification_repository(
    db: Session = Depends(get_db),
) -> NotificationRepository:
    return NotificationRepository(db)


def get_notification_service(
    repository: NotificationRepository = Depends(
        get_notification_repository,
    ),
) -> NotificationService:
    return NotificationService(repository)