from fastapi import APIRouter

from app.api.v1.reminders import router as reminder_router


router = APIRouter()

router.include_router(
    reminder_router,
    prefix="/api/v1/reminders",
    tags=["Reminders"],
)