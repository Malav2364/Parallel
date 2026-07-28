from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    return{
        "status" : "healthy",
        "service" : settings.APP_NAME,
        "version" : settings.APP_VERSION,
        "environment" : settings.APP_ENV,
    }