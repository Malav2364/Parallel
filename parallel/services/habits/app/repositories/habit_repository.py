from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.habit import Habit


class HabitRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_owner_and_name(
        self,
        owner_id: str,
        normalized_name: str,
    ) -> Habit | None:
        statement = select(Habit).where(
            Habit.owner_id == owner_id,
            Habit.normalized_name == normalized_name,
        )

        return self.db.scalar(statement)

    def get_by_id(
        self,
        habit_id: str,
    ) -> Habit | None:
        statement = select(Habit).where(
            Habit.id == habit_id,
        )

        return self.db.scalar(statement)

    def get_by_owner(
        self,
        owner_id: str,
    ) -> list[Habit]:
        statement = (
            select(Habit)
            .where(Habit.owner_id == owner_id)
            .order_by(Habit.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def create(
        self,
        habit: Habit,
    ) -> Habit:
        self.db.add(habit)
        self.db.commit()
        self.db.refresh(habit)

        return habit

    def update(
        self,
        habit: Habit,
    ) -> Habit:
        self.db.commit()
        self.db.refresh(habit)

        return habit

    def delete(
        self,
        habit: Habit,
    ) -> None:
        self.db.delete(habit)
        self.db.commit()