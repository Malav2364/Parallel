from fastapi import APIRouter
from app.core.config import settings
from app.core.logger import logger

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    logger.info("Health endpoint called")
    return{
        "status" : "healthy",
        "service" : settings.APP_NAME,
        "version" : settings.APP_VERSION,
        "environment" : settings.APP_ENV,
    }