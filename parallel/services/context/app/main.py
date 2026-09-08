from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import router
from app.core.config import settings
from app.core.logger import logger

logger.info("Starting Context Service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One pooled HTTP client shared by every downstream service call, so
    # connections are reused across requests instead of dialled per call.
    async with httpx.AsyncClient(timeout=10.0) as client:
        app.state.http_client = client
        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(health_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to Parallel Context Service",
    }
    
