from fastapi import APIRouter

from app.api.v1.spaces import router as space_router
from app.api.v1.workspaces import router as workspace_router

router = APIRouter(prefix="/api/v1")

router.include_router(
    workspace_router,
    prefix="/workspaces",
    tags=["Workspaces"],
)

router.include_router(
    space_router,
    prefix="/spaces",
    tags=["Spaces"],
)
