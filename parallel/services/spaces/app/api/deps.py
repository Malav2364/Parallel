from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db as _get_db
from app.repositories import (
    SpaceProjectRepository,
    SpaceRepository,
    WorkspaceRepository,
)
from app.services.space_project_service import SpaceProjectService
from app.services.space_service import SpaceService
from app.services.workspace_service import WorkspaceService


def get_db() -> Generator[Session]:
    """Expose database dependencies to API routes."""
    yield from _get_db()


def get_workspace_repository(
    db: Session = Depends(get_db),
) -> WorkspaceRepository:
    return WorkspaceRepository(db)


def get_space_repository(
    db: Session = Depends(get_db),
) -> SpaceRepository:
    return SpaceRepository(db)


def get_workspace_service(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    space_repository: SpaceRepository = Depends(get_space_repository),
) -> WorkspaceService:
    return WorkspaceService(workspace_repository, space_repository)


def get_space_service(
    repository: SpaceRepository = Depends(get_space_repository),
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
) -> SpaceService:
    return SpaceService(repository, workspace_repository)


def get_space_project_repository(
    db: Session = Depends(get_db),
) -> SpaceProjectRepository:
    return SpaceProjectRepository(db)


def get_space_project_service(
    repository: SpaceProjectRepository = Depends(
        get_space_project_repository,
    ),
) -> SpaceProjectService:
    return SpaceProjectService(repository)
