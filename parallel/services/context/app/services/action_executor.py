from app.clients.projects_client import ProjectsClient
from app.clients.workspace_client import WorkspaceClient
from app.schemas.decision import ContextDecision


class ActionExecutor:
    def __init__(
        self,
        projects_client: ProjectsClient,
        workspace_client: WorkspaceClient,
    ) -> None:
        self.projects_client = projects_client
        self.workspace_client = workspace_client

    def execute(self, user_id: str, decision: ContextDecision) -> dict:
        if decision.action == "none":
            return {"executed": False, "action": "none"}

        if decision.action == "create_project":
            if not decision.project_name:
                return {
                    "executed": False,
                    "action": "create_project",
                    "reason": "Project name was not provided.",
                }

            project = self.projects_client.create_project(
                user_id=user_id,
                name=decision.project_name,
                description=decision.project_description,
            )

            space = None
            if decision.space_candidate:
                space = self.workspace_client.create_space(
                    user_id=user_id,
                    name=decision.space_candidate,
                    description=decision.project_description,
                    space_type="custom",
                    visibility="private",
                    source="ai",
                )

                association = self.workspace_client.associate_project(
                    space_id=space["id"],
                    project_id=project["id"],
                )
            else:
                association = None

            return {
                "executed": True,
                "action": "create_project",
                "project": project,
                "space": space,
                "association": association,
            }

        return {
            "executed": False,
            "action": decision.action,
            "reason": "Action is not implemented yet.",
        }
