from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import api_router
from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.logger import logger
from app.exceptions.exceptions import ParallelException
from app.exceptions.handlers import parallel_exception_handler

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

app.include_router(api_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Parallel Identity Service"}


app.include_router(
    api_v1_router,
    prefix="/api/v1",
)
