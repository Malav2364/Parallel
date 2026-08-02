from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.exceptions.exceptions import ResourceNotFoundException

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    logger.info("Health endpoint called")
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@router.get("/test-error")
async def test_error():
    raise ResourceNotFoundException("User")


@router.get("/db-health")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {"status": "connected"}
