from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import router
from app.core.config import settings
from app.core.logger import logger

logger.info("Starting Context Service")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(router)
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Parallel Context Service",
    }
