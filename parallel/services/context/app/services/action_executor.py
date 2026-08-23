import httpx

from app.clients.goals_client import GoalsClient
from app.clients.projects_client import ProjectsClient
from app.clients.workspace_client import WorkspaceClient
from app.schemas.decision import ContextDecision
from app.clients.habits_client import HabitsClient
from app.clients.reminders_client import RemindersClient
from app.services.idempotency import build_key
from app.services.reminder_datetime import ReminderDateTimeResolver
from datetime import datetime
from zoneinfo import ZoneInfo


class ActionExecutor:
    def __init__(
        self,
        projects_client: ProjectsClient,
        workspace_client: WorkspaceClient,
        goals_client: GoalsClient | None = None,
        habits_client: HabitsClient | None = None,
        reminders_client: RemindersClient | None = None,
    ) -> None:
        self.projects_client = projects_client
        self.workspace_client = workspace_client
        self.goals_client = goals_client
        self.habits_client = habits_client
        self.reminders_client = reminders_client

    async def execute(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if decision.action == "none":
            return {
                "executed": False,
                "action": "none",
            }

        if decision.action == "create_project":
            return await self._create_project(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_goal":
            return await self._create_goal(
                user_id=user_id,
                decision=decision,
            )
        
        if decision.action == "create_habit":
            return await self._create_habit(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_reminder":
            return await self._create_reminder(
                user_id=user_id,
                decision=decision,
            )

        return {
            "executed": False,
            "action": decision.action,
            "reason": "Action is not implemented yet.",
        }

    async def _create_goal(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if self.goals_client is None:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": "Goals client is not configured.",
            }

        goal_name = decision.goal_name or next(
            (
                signal.name
                for signal in decision.signals
                if signal.type == "goal" and signal.name
            ),
            None,
        )

        if not goal_name:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": "Goal name was not provided.",
            }

        idempotency_key = build_key(user_id, "create_goal", goal_name)

        try:
            existing = await self.goals_client.get_by_name(
                user_id=user_id,
                name=goal_name,
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_goal",
                    "reason": "Goal already exists.",
                    "goal": existing,
                    "goal_created": False,
                    "idempotency_key": idempotency_key,
                }

            goal = await self.goals_client.create_goal(
                user_id=user_id,
                name=goal_name,
                description=decision.goal_description,
                status=decision.goal_status or "active",
                target_date=decision.goal_target_date,
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": f"Goals service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the goal is findable by the same natural key we
        # dedup on before reporting success, rather than trusting the create
        # response alone.
        try:
            verified = await self.goals_client.get_by_name(
                user_id=user_id,
                name=goal_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_goal",
            "goal": verified or goal,
            "goal_created": True,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }

    async def _create_habit(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if self.habits_client is None:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habits client is not configured.",
            }

        if not decision.habit_name:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habit activity was not provided.",
            }

        if not decision.habit_schedule:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habit schedule was not provided.",
            }

        idempotency_key = build_key(user_id, "create_habit", decision.habit_name)

        try:
            existing = await self.habits_client.get_by_name(
                user_id=user_id,
                name=decision.habit_name,
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_habit",
                    "reason": "Habit already exists.",
                    "habit": existing,
                    "habit_created": False,
                    "idempotency_key": idempotency_key,
                }

            habit = await self.habits_client.create_habit(
                user_id=user_id,
                name=decision.habit_name,
                schedule=decision.habit_schedule,
                description=decision.habit_description,
                time_window=decision.habit_time_window,
                status=decision.habit_status or "active",
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": f"Habits service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the habit is findable by the same natural key we
        # dedup on before reporting success, rather than trusting the create
        # response alone.
        try:
            verified = await self.habits_client.get_by_name(
                user_id=user_id,
                name=decision.habit_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_habit",
            "habit": verified or habit,
            "habit_created": True,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }

    async def _create_reminder(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:

        if self.reminders_client is None:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminders client is not configured.",
            }

        if not decision.reminder_title:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder title was not provided.",
            }

        if not decision.reminder_date:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder date was not provided.",
            }

        if not decision.reminder_time:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder time was not provided.",
            }

        try:
            scheduled_for = ReminderDateTimeResolver.resolve(
                date_expression=decision.reminder_date,
                time_expression=decision.reminder_time,
            )

        except ValueError as exc:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": str(exc),
            }

        now = datetime.now(
            ZoneInfo("Asia/Kolkata")
        )

        if scheduled_for <= now:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": (
                    "Resolved reminder time is in the past."
                ),
            }

        idempotency_key = build_key(
            user_id,
            "create_reminder",
            decision.reminder_title,
            scheduled_for.isoformat(),
        )

        try:
            existing = await self.reminders_client.get_by_details(
                user_id=user_id,
                title=decision.reminder_title,
                scheduled_for=scheduled_for.isoformat(),
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": "Reminder already exists.",
                    "reminder": existing,
                    "reminder_created": False,
                    "idempotency_key": idempotency_key,
                }

            reminder = await self.reminders_client.create_reminder(
                user_id=user_id,
                title=decision.reminder_title,
                description=decision.reminder_description,
                scheduled_for=scheduled_for.isoformat(),
                recurrence=decision.reminder_recurrence,
                status=decision.reminder_status or "pending",
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": f"Reminders service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the write is actually queryable before reporting
        # success, rather than trusting the create response alone.
        reminder_id = reminder.get("id") if isinstance(reminder, dict) else None

        if not reminder_id:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder create returned no id; not verified.",
                "reminder": reminder,
                "idempotency_key": idempotency_key,
            }

        try:
            verified = await self.reminders_client.get_reminder(
                user_id=user_id,
                reminder_id=reminder_id,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_reminder",
            "reminder": verified or reminder,
            "reminder_created": True,
            "verified": verified is not None,
            "scheduled_for": scheduled_for.isoformat(),
            "idempotency_key": idempotency_key,
        }

    async def _create_project(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if not decision.project_name:
            return {
                "executed": False,
                "action": "create_project",
                "reason": "Project name was not provided.",
            }

        idempotency_key = build_key(
            user_id,
            "create_project",
            decision.project_name,
        )

        project = None
        space = None
        association = None
        project_created = False
        space_created = False

        try:
            # --------------------------------------------------
            # Project
            # --------------------------------------------------

            project = await self.projects_client.get_by_name(
                user_id=user_id,
                name=decision.project_name,
            )

            if project is None:
                project = await self.projects_client.create_project(
                    user_id=user_id,
                    name=decision.project_name,
                    description=decision.project_description,
                    idempotency_key=idempotency_key,
                )
                project_created = True

            # --------------------------------------------------
            # Space
            # --------------------------------------------------

            if decision.space_candidate:
                space = await self.workspace_client.get_by_name(
                    user_id=user_id,
                    name=decision.space_candidate,
                )

                if space is None:
                    space = await self.workspace_client.create_space(
                        user_id=user_id,
                        name=decision.space_candidate,
                        description=decision.project_description,
                        space_type="custom",
                        visibility="private",
                        source="ai",
                    )
                    space_created = True

            # --------------------------------------------------
            # Association
            # --------------------------------------------------

            if space is not None:
                association = await self.workspace_client.associate_project(
                    space_id=space["id"],
                    project_id=project["id"],
                )

        except httpx.HTTPError as exc:
            return {
                "executed": project_created or space_created,
                "action": "create_project",
                "reason": f"Projects service request failed: {exc}",
                "project": project,
                "space": space,
                "project_created": project_created,
                "space_created": space_created,
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the project is findable by name before reporting
        # success, rather than trusting the create response alone.
        try:
            verified = await self.projects_client.get_by_name(
                user_id=user_id,
                name=decision.project_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": project_created or space_created,
            "action": "create_project",
            "project": verified or project,
            "space": space,
            "association": association,
            "project_created": project_created,
            "space_created": space_created,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }
