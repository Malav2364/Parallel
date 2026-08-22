from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
    }