from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_role_service
from app.schemas.role import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.services.role_service import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.permission import PermissionResponse


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    request: RoleCreate,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    return service.create_role(
        name=request.name,
        description=request.description,
    )


@router.get(
    "",
    response_model=list[RoleResponse],
)
def get_roles(
    service: RoleService = Depends(get_role_service),
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
):
    return service.get_roles()


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: str,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    return service.get_role(role_id)


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: str,
    request: RoleUpdate,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    return service.update_role(
        role_id=role_id,
        name=request.name,
        description=request.description,
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: str,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    service.delete_role(role_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def assign_permission(
    role_id: str,
    permission_id: str,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    service.assign_permission(
        role_id=role_id,
        permission_id=permission_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_permission(
    role_id: str,
    permission_id: str,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    service.remove_permission(
        role_id=role_id,
        permission_id=permission_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/{role_id}/permissions",
    response_model=list[PermissionResponse],
)
def get_permissions(
    role_id: str,
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
    service: RoleService = Depends(get_role_service),
):
    return service.get_permissions(
        role_id,
    )
