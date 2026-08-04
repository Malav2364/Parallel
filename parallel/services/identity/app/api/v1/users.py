from fastapi import APIRouter, Depends

from app.core.permissions import require_permission

# from app.api.deps import get_current_user
from app.models.user import User

# from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def get_me(
    current_user: User = Depends(
        require_permission(
            "view_profile",
        ),
    ),
):
    return current_user
