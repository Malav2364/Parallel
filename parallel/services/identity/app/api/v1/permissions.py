from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_permission_service
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
)
from app.services.permission_service import PermissionService

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    request: PermissionCreate,
    current_user: User = Depends(
        require_permission("manage_permissions"),
    ),
    service: PermissionService = Depends(get_permission_service),
):
    return service.create_permission(
        request.name,
        request.description,
    )


@router.get(
    "",
    response_model=list[PermissionResponse],
)
def get_permissions(
    service: PermissionService = Depends(get_permission_service),
    current_user: User = Depends(
        require_permission("manage_permissions"),
    ),
):
    return service.get_permissions()


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
)
def get_permission(
    permission_id: str,
    current_user: User = Depends(
        require_permission("manage_permissions"),
    ),
    service: PermissionService = Depends(get_permission_service),
):
    return service.get_permission(permission_id)


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
)
def update_permission(
    permission_id: str,
    request: PermissionUpdate,
    current_user: User = Depends(
        require_permission("manage_permissions"),
    ),
    service: PermissionService = Depends(get_permission_service),
):
    return service.update_permission(
        permission_id,
        request.name,
        request.description,
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_permission(
    permission_id: str,
    current_user: User = Depends(
        require_permission("manage_permissions"),
    ),
    service: PermissionService = Depends(get_permission_service),
):
    service.delete_permission(permission_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
