from fastapi import APIRouter, Depends, Request, Response, status, HTTPException

from app.api.deps import get_project_service
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from app.schemas.project_activity import ProjectActivityUpdate

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
)
def create_project(
    request: ProjectCreate,
    http_request: Request,
    service: ProjectService = Depends(
        get_project_service,
    ),
):

    owner_id = http_request.headers.get("x-user-id")

    return service.create_project(
        request,
        owner_id,
    )


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    http_request: Request,
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    owner_id = http_request.headers.get("x-user-id")

    return service.list_projects(owner_id)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: str,
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    return service.get_project(
        project_id,
    )

@router.patch(
    "/{project_id}/activity",
)
def update_project_activity(
    project_id: str,
    request: ProjectActivityUpdate,
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    project = service.update_activity(
        project_id=project_id,
        current_focus=request.current_focus,
        latest_activity=request.latest_activity,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: str,
    request: ProjectUpdate,
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    return service.update_project(
        project_id,
        request,
    )

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: str,
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    service.delete_project(
        project_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
