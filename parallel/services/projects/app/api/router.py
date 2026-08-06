from fastapi import APIRouter

from app.api.v1.project_members import (
    router as project_member_router,
)
from app.api.v1.projects import router as project_router

router = APIRouter()

router.include_router(
    project_member_router,
    prefix="/api/v1",
)

router.include_router(
    project_router,
    prefix="/api/v1/projects",
    tags=["Projects"],
)
