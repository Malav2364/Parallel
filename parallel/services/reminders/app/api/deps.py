from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.reminder_repository import ReminderRepository
from app.services.reminder_service import ReminderService


def get_reminder_repository(
    db: Session = Depends(get_db),
) -> ReminderRepository:
    return ReminderRepository(db)


def get_reminder_service(
    repository: ReminderRepository = Depends(
        get_reminder_repository
    ),
) -> ReminderService:
    return ReminderService(repository)