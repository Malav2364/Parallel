from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Goal


class GoalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, goal: Goal) -> Goal:
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def get_by_id(self, goal_id: str) -> Goal | None:
        return self.db.get(Goal, goal_id)

    def get_by_owner_and_name(
        self,
        owner_id: str,
        normalized_name: str,
    ) -> Goal | None:
        statement = select(Goal).where(
            Goal.owner_id == owner_id,
            Goal.normalized_name == normalized_name,
        )
        return self.db.scalar(statement)

    def list_by_owner(self, owner_id: str) -> list[Goal]:
        statement = (
            select(Goal)
            .where(Goal.owner_id == owner_id)
            .order_by(Goal.created_at)
        )
        return list(self.db.scalars(statement).all())

    def rollback(self) -> None:
        self.db.rollback()
