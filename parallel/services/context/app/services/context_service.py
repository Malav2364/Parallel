from uuid import uuid4

from app.models import ContextChangeEntity, UserContextEntity
from app.repositories import ContextRepository
from app.schemas import ContextUpdate


class ContextService:
    """Manage the user's current, versioned context state."""

    def __init__(self, repository: ContextRepository):
        self.repository = repository

    def get_context(self, user_id: str) -> UserContextEntity:
        context = self.repository.get_by_user_id(user_id)
        if context is not None:
            return context

        return self.repository.create(
            UserContextEntity(
                id=str(uuid4()),
                user_id=user_id,
                context={},
                version=1,
            )
        )

    def update_context(
        self,
        user_id: str,
        request: ContextUpdate,
    ) -> UserContextEntity:
        context = self.get_context(user_id)

        old_context = dict(context.context)
        new_context = dict(old_context)
        new_context.update(request.updates)

        changes = self.detect_changes(old_context, new_context)
        if not changes:
            return context

        context.context = new_context
        context.version += 1

        updated_context = self.repository.update(context)
        self.repository.create_change(
            ContextChangeEntity(
                id=str(uuid4()),
                user_id=user_id,
                context_id=context.id,
                changes=changes,
            )
        )

        return updated_context

    @staticmethod
    def detect_changes(
        old_context: dict,
        new_context: dict,
    ) -> dict:
        changes = {}
        keys = set(old_context) | set(new_context)

        for key in keys:
            old_value = old_context.get(key)
            new_value = new_context.get(key)

            if old_value != new_value:
                changes[key] = {
                    "previous": old_value,
                    "current": new_value,
                }

        return changes

    def apply_updates(
        self,
        user_id: str,
        updates,
    ) -> UserContextEntity:
        context = self.get_context(user_id)

        current_context = dict(context.context or {})
        updates_dict = dict(updates)

        # -----------------------------------------
        # Normal current-state updates
        # -----------------------------------------

        for key, value in updates_dict.items():
            if key == "goals_to_add":
                continue

            if value is not None:
                current_context[key] = value

        # -----------------------------------------
        # Goals are additive
        # -----------------------------------------

        goals_to_add = updates_dict.get("goals_to_add", [])

        if goals_to_add:
            goals = list(current_context.get("goals", []))

            existing_goals = {
                goal.strip().lower()
                for goal in goals
                if isinstance(goal, str)
            }

            for goal in goals_to_add:
                if not isinstance(goal, str):
                    continue

                goal = goal.strip()

                if not goal:
                    continue

                if goal.lower() not in existing_goals:
                    goals.append(goal)
                    existing_goals.add(goal.lower())

            current_context["goals"] = goals

        return self.update_context(
            user_id=user_id,
            request=ContextUpdate(
                updates=current_context,
            ),
        )

    def list_changes(self, user_id: str) -> list[ContextChangeEntity]:
        return self.repository.list_changes(user_id)
