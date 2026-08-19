from fastapi import Depends
from sqlalchemy.orm import Session
from app.clients.habits_client import HabitsClient
from app.clients.reminders_client import RemindersClient
from app.clients.goals_client import GoalsClient
from app.clients.projects_client import ProjectsClient
from app.clients.workspace_client import WorkspaceClient
from app.db.database import get_db
from app.repositories import ContextRepository
from app.services import (
    ContextDecisionEngine,
    ContextExtractor,
    ContextService,
    ProjectResolver,
)
from app.services.action_executor import ActionExecutor
from app.services.project_activity_extractor import (
    ProjectActivityExtractor,
)


def get_context_repository(
    db: Session = Depends(get_db),
) -> ContextRepository:
    return ContextRepository(db)


def get_context_service(
    repository: ContextRepository = Depends(get_context_repository),
) -> ContextService:
    return ContextService(repository)


def get_context_extractor() -> ContextExtractor:
    return ContextExtractor()


def get_context_decision_engine() -> ContextDecisionEngine:
    return ContextDecisionEngine()


def get_projects_client() -> ProjectsClient:
    return ProjectsClient()


def get_goals_client() -> GoalsClient:
    return GoalsClient()

def get_habits_client() -> HabitsClient:
    return HabitsClient()

def get_reminders_client() -> RemindersClient:
    return RemindersClient()

def get_workspace_client() -> WorkspaceClient:
    return WorkspaceClient()


def get_project_activity_extractor() -> ProjectActivityExtractor:
    return ProjectActivityExtractor()


def get_project_resolver(
    projects_client: ProjectsClient = Depends(get_projects_client),
) -> ProjectResolver:
    return ProjectResolver(projects_client)


def get_action_executor(
    projects_client: ProjectsClient = Depends(get_projects_client),
    workspace_client: WorkspaceClient = Depends(get_workspace_client),
    goals_client: GoalsClient = Depends(get_goals_client),
    habits_client: HabitsClient = Depends(get_habits_client),
    reminders_client: RemindersClient = Depends(get_reminders_client),
) -> ActionExecutor:
    return ActionExecutor(
        projects_client,
        workspace_client,
        goals_client,
        habits_client,
        reminders_client,
    )
