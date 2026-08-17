from fastapi import APIRouter

from app.api.v1.habits import router as habit_router


router = APIRouter(prefix="/api/v1")

router.include_router(
    habit_router,
    prefix="/habits",
    tags=["Habits"],
)