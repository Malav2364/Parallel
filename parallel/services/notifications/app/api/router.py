from fastapi import APIRouter

from app.api.v1.notifications import router as notification_router


router = APIRouter()

router.include_router(
    notification_router,
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)