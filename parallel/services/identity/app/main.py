from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.core.logger import logger
from app.exceptions.handlers import parallel_exception_handler
from app.exceptions.exceptions import ParallelException


logger.info("Starting Identity Service")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Identity Service for Parallel",
)
app.add_exception_handler(
    ParallelException,
    parallel_exception_handler,
)

app.include_router(health_router)



@app.get("/")
async def root():
    return {
        "message": "Welcome to Parallel Identity Service"
    }