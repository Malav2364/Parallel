from fastapi import APIRouter

from app.api.v1.github import router as github_router

router = APIRouter()

router.include_router(
    github_router,
    prefix="/api/v1/github",
    tags=["GitHub"],
)
