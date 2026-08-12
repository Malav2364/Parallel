from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_space_project_service, get_space_service
from app.schemas.space import SpaceCreateRequest, SpaceResponse
from app.schemas.space_project import (
    SpaceProjectCreate,
    SpaceProjectResponse,
)
from app.services.space_project_service import SpaceProjectService
from app.services.space_service import SpaceService

router = APIRouter()


@router.post("", response_model=SpaceResponse, status_code=201)
def create_space(
    request: SpaceCreateRequest,
    x_user_id: str = Header(...),
    service: SpaceService = Depends(get_space_service),
) -> SpaceResponse:
    """Create a custom space in the current user's workspace."""
    try:
        space = service.create_space(x_user_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if space is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not initialized",
        )
    return space


@router.get("", response_model=list[SpaceResponse])
def list_spaces(
    x_user_id: str = Header(...),
    service: SpaceService = Depends(get_space_service),
) -> list[SpaceResponse]:
    """Return spaces for the current user's workspace."""
    return service.list_spaces(x_user_id)


@router.get("/{space_id}", response_model=SpaceResponse)
def get_space(
    space_id: str,
    x_user_id: str = Header(...),
    service: SpaceService = Depends(get_space_service),
) -> SpaceResponse:
    """Return a space only when it belongs to the requested workspace."""
    space = service.get_space(x_user_id, space_id)
    if space is None:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


@router.post(
    "/{space_id}/projects",
    response_model=SpaceProjectResponse,
)
def associate_project(
    space_id: str,
    request: SpaceProjectCreate,
    service: SpaceProjectService = Depends(get_space_project_service),
) -> SpaceProjectResponse:
    association = service.associate(
        space_id=space_id,
        project_id=request.project_id,
    )
    return SpaceProjectResponse(
        id=association.id,
        space_id=association.space_id,
        project_id=association.project_id,
    )


@router.get("/{space_id}/projects")
def list_space_projects(
    space_id: str,
    service: SpaceProjectService = Depends(get_space_project_service),
) -> list[SpaceProjectResponse]:
    associations = service.list_projects(space_id)
    return [
        SpaceProjectResponse(
            id=association.id,
            space_id=association.space_id,
            project_id=association.project_id,
        )
        for association in associations
    ]
