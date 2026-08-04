from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.permissions import router as permission_router
from app.api.v1.roles import router as roles_router
from app.api.v1.users import router as users_router

router = APIRouter()

router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    users_router,
)

router.include_router(
    roles_router,
)

router.include_router(permission_router)
