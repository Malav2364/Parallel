import httpx
from fastapi import Depends, Request
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


def get_http_client(request: Request) -> httpx.AsyncClient:
    # The pooled client created in the app lifespan; shared by all
    # downstream service clients so connections are reused.
    return request.app.state.http_client


def get_projects_client(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> ProjectsClient:
    return ProjectsClient(client)


def get_goals_client(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> GoalsClient:
    return GoalsClient(client)

def get_habits_client(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> HabitsClient:
    return HabitsClient(client)

def get_reminders_client(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> RemindersClient:
    return RemindersClient(client)

def get_workspace_client(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> WorkspaceClient:
    return WorkspaceClient(client)


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
