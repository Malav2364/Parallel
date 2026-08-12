from fastapi import APIRouter, Depends, Header

from app.api.deps import get_workspace_service
from app.schemas.workspace import WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("/initialize", response_model=WorkspaceResponse)
def initialize_workspace(
    x_user_id: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Create the owner's workspace and default system spaces."""
    return service.initialize_workspace(x_user_id)


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    x_user_id: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[WorkspaceResponse]:
    """Return the current user's workspace, when it exists."""
    workspace = service.get_workspace(x_user_id)
    return [] if workspace is None else [workspace]
