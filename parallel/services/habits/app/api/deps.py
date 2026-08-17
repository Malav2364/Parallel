from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.habit_repository import HabitRepository
from app.services.habit_service import HabitService


def get_habit_service(
    db: Session = Depends(get_db),
) -> HabitService:
    repository = HabitRepository(db)

    return HabitService(repository)