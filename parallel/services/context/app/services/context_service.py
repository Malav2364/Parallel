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

    # -----------------------------------------
    # Goal normalization
    # -----------------------------------------

    @staticmethod
    def normalize_goal(goal) -> dict | None:
        """
        Convert both legacy string goals and structured
        goal objects into one consistent structure.
        """

        # Legacy format:
        # "apply for MBA"
        if isinstance(goal, str):
            goal = goal.strip()

            if not goal:
                return None

            return {
                "name": goal,
                "status": "active",
                "target_date": None,
            }

        # New structured format:
        # {
        #     "name": "Pursue an MBA",
        #     "status": "active",
        #     "target_date": "2027",
        # }
        if isinstance(goal, dict):
            name = goal.get("name")

            if not isinstance(name, str):
                return None

            name = name.strip()

            if not name:
                return None

            return {
                "name": name,
                "status": goal.get(
                    "status",
                    "active",
                ),
                "target_date": goal.get("target_date"),
            }

        return None

    @classmethod
    def normalize_goals(
        cls,
        goals: list,
    ) -> list[dict]:
        """
        Normalize all existing goals and remove
        exact duplicates.
        """

        normalized = []
        seen = set()

        for goal in goals:
            normalized_goal = cls.normalize_goal(goal)

            if normalized_goal is None:
                continue

            key = normalized_goal["name"].strip().lower()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(normalized_goal)

        return normalized

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
        # Goals
        # -----------------------------------------

        existing_goals = self.normalize_goals(current_context.get("goals", []))

        existing_names = {goal["name"].strip().lower() for goal in existing_goals}

        goals_to_add = updates_dict.get(
            "goals_to_add",
            [],
        )

        for goal in goals_to_add:
            normalized_goal = self.normalize_goal(goal)

            if normalized_goal is None:
                continue

            key = normalized_goal["name"].strip().lower()

            if key not in existing_names:
                existing_goals.append(normalized_goal)
                existing_names.add(key)

        current_context["goals"] = existing_goals

        return self.update_context(
            user_id=user_id,
            request=ContextUpdate(
                updates=current_context,
            ),
        )

    def list_changes(
        self,
        user_id: str,
    ) -> list[ContextChangeEntity]:
        return self.repository.list_changes(user_id)
