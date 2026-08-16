from app.clients.goals_client import GoalsClient
from app.clients.projects_client import ProjectsClient
from app.clients.workspace_client import WorkspaceClient
from app.schemas.decision import ContextDecision


class ActionExecutor:
    def __init__(
        self,
        projects_client: ProjectsClient,
        workspace_client: WorkspaceClient,
        goals_client: GoalsClient | None = None,
    ) -> None:
        self.projects_client = projects_client
        self.workspace_client = workspace_client
        self.goals_client = goals_client

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
