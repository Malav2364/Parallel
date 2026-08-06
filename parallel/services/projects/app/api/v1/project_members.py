from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_project_member_service
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberResponse,
)
from app.services.project_member_service import (
    ProjectMemberService,
)

router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["Project Members"],
)


@router.post(
    "",
    response_model=ProjectMemberResponse,
)
def add_member(
    project_id: str,
    request: ProjectMemberCreate,
    service: ProjectMemberService = Depends(
        get_project_member_service,
    ),
):
    return service.add_member(
        project_id,
        request,
    )


@router.get(
    "",
    response_model=list[ProjectMemberResponse],
)
def list_members(
    project_id: str,
    service: ProjectMemberService = Depends(
        get_project_member_service,
    ),
):
    return service.list_members(
        project_id,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member(
    project_id: str,
    user_id: str,
    service: ProjectMemberService = Depends(
        get_project_member_service,
    ),
):
    service.remove_member(
        project_id,
        user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
