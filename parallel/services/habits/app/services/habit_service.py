from uuid import uuid4

from app.models.habit import Habit
from app.repositories.habit_repository import HabitRepository
from app.schemas.habit import HabitCreate


class HabitService:
    def __init__(
        self,
        repository: HabitRepository,
    ):
        self.repository = repository

    @staticmethod
    def normalize_name(name: str) -> str:
        return " ".join(name.strip().lower().split())

    def create_habit(
        self,
        request: HabitCreate,
        owner_id: str,
    ) -> Habit:
        normalized_name = self.normalize_name(request.name)

        existing = self.repository.get_by_owner_and_name(
            owner_id=owner_id,
            normalized_name=normalized_name,
        )

        if existing:
            return existing

        habit = Habit(
            id=str(uuid4()),
            name=request.name.strip(),
            normalized_name=normalized_name,
            description=request.description,
            owner_id=owner_id,
            schedule=request.schedule,
            time_window=request.time_window,
            status=request.status,
        )

        return self.repository.create(habit)

    def list_habits(
        self,
        owner_id: str,
    ) -> list[Habit]:
        return self.repository.get_by_owner(owner_id)

    def get_habit(
        self,
        habit_id: str,
    ) -> Habit | None:
        return self.repository.get_by_id(habit_id)