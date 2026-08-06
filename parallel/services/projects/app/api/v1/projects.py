from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import get_project_service
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

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
    service: ProjectService = Depends(
        get_project_service,
    ),
):
    return service.list_projects()


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
