from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
)
from app.exceptions.permission import (
    PermissionDeniedException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


def require_permission(
    permission_name: str,
):
    def dependency(
        current_user: User = Depends(
            get_current_user,
        ),
        db: Session = Depends(
            get_db,
        ),
    ) -> User:

        repository = UserRepository(db)

        if not repository.has_permission(
            current_user.id,
            permission_name,
        ):
            raise PermissionDeniedException()

        return current_user

    return dependency
