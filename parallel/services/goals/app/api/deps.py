from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import GoalRepository
from app.services import GoalService


def get_goal_repository(
    db: Session = Depends(get_db),
) -> GoalRepository:
    return GoalRepository(db)


def get_goal_service(
    repository: GoalRepository = Depends(get_goal_repository),
) -> GoalService:
    return GoalService(repository)
