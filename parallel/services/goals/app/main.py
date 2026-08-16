from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(router)
app.include_router(health_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "status": "running",
    }
