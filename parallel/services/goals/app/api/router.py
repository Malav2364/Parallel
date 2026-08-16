from fastapi import APIRouter

from app.api.v1.goals import router as goal_router

router = APIRouter()

router.include_router(
    goal_router,
    prefix="/api/v1/goals",
    tags=["Goals"],
)
