from fastapi import APIRouter

from app.api.v1.context import router as context_router

router = APIRouter()

router.include_router(
    context_router,
prefix="/api/v1/context",
    tags=["Context"],
)
