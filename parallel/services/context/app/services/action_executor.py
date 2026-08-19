from app.clients.goals_client import GoalsClient
from app.clients.projects_client import ProjectsClient
from app.clients.workspace_client import WorkspaceClient
from app.schemas.decision import ContextDecision
from app.clients.habits_client import HabitsClient
from app.clients.reminders_client import RemindersClient


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

    def execute(
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
            return self._create_project(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_goal":
            return self._create_goal(
                user_id=user_id,
                decision=decision,
            )
        
        if decision.action == "create_habit":
            return self._create_habit(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_reminder":
            return self._create_reminder(
                user_id=user_id,
                decision=decision,
            )

        return {
            "executed": False,
            "action": decision.action,
            "reason": "Action is not implemented yet.",
        }

    def _create_goal(
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

        goal = self.goals_client.get_by_name(
            user_id=user_id,
            name=goal_name,
        )
        goal_created = False

        if goal is None:
            goal = self.goals_client.create_goal(
                user_id=user_id,
                name=goal_name,
                description=decision.goal_description,
                status=decision.goal_status or "active",
                target_date=decision.goal_target_date,
            )
            goal_created = True

        return {
            "executed": goal_created,
            "action": "create_goal",
            "goal": goal,
            "goal_created": goal_created,
        }

    def _create_habit(
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

        existing = self.habits_client.get_by_name(
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
            }

        habit = self.habits_client.create_habit(
            user_id=user_id,
            name=decision.habit_name,
            schedule=decision.habit_schedule,
            description=decision.habit_description,
            time_window=decision.habit_time_window,
            status=decision.habit_status or "active",
        )

        return {
            "executed": True,
            "action": "create_habit",
            "habit": habit,
            "habit_created": True,
        }

    def _create_reminder(
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

        if not decision.reminder_scheduled_for:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder scheduled time was not provided.",
            }

        reminder = self.reminders_client.create_reminder(
            user_id=user_id,
            title=decision.reminder_title,
            description=decision.reminder_description,
            scheduled_for=decision.reminder_scheduled_for,
            recurrence=decision.reminder_recurrence,
            status=decision.reminder_status or "pending",
        )

        return {
            "executed": True,
            "action": "create_reminder",
            "reminder": reminder,
            "reminder_created": True,
        }

    def _create_project(
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

        # --------------------------------------------------
        # Project
        # --------------------------------------------------

        project = self.projects_client.get_by_name(
            user_id=user_id,
            name=decision.project_name,
        )

        project_created = False

        if project is None:
            project = self.projects_client.create_project(
                user_id=user_id,
                name=decision.project_name,
                description=decision.project_description,
            )
            project_created = True

        # --------------------------------------------------
        # Space
        # --------------------------------------------------

        space = None
        space_created = False

        if decision.space_candidate:
            space = self.workspace_client.get_by_name(
                user_id=user_id,
                name=decision.space_candidate,
            )

            if space is None:
                space = self.workspace_client.create_space(
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

        association = None

        if space is not None:
            association = self.workspace_client.associate_project(
                space_id=space["id"],
                project_id=project["id"],
            )

        return {
            "executed": project_created or space_created,
            "action": "create_project",
            "project": project,
            "space": space,
            "association": association,
            "project_created": project_created,
            "space_created": space_created,
        }
