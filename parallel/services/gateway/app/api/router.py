from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.proxy import router as proxy_router

router = APIRouter()

router.include_router(health_router)
router.include_router(proxy_router)
