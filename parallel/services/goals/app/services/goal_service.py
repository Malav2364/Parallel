from sqlalchemy.exc import IntegrityError

from app.models import Goal
from app.repositories import GoalRepository
from app.schemas.goal import GoalCreate


class GoalService:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    def create_goal(self, request: GoalCreate, owner_id: str) -> Goal:
        name = request.name.strip()
        normalized_name = name.casefold()

        existing = self.repository.get_by_owner_and_name(
            owner_id=owner_id,
            normalized_name=normalized_name,
        )
        if existing is not None:
            return existing

        goal = Goal(
            name=name,
            normalized_name=normalized_name,
            description=request.description,
            owner_id=owner_id,
            status=request.status,
            target_date=request.target_date,
        )

        try:
            return self.repository.create(goal)
        except IntegrityError:
            # The unique constraint closes the race between the lookup and
            # insert. Return the winner so retries remain idempotent.
            self.repository.rollback()
            existing = self.repository.get_by_owner_and_name(
                owner_id=owner_id,
                normalized_name=normalized_name,
            )
            if existing is None:
                raise
            return existing

    def list_goals(self, owner_id: str) -> list[Goal]:
        return self.repository.list_by_owner(owner_id)
