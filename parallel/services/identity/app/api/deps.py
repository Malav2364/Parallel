from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import decode_access_token
from app.exceptions.auth import InvalidTokenException
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_permission_repository import (
    RolePermissionRepository,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.services.user_service import UserService


def get_user_service(
    db: Session = Depends(get_db),
) -> UserService:
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    return UserService(
        repository=user_repository,
        refresh_token_repository=refresh_token_repository,
    )


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)

    email = payload.get("sub")

    if email is None:
        raise InvalidTokenException()

    repository = UserRepository(db)

    user = repository.get_by_email(email)

    if user is None:
        raise InvalidTokenException()

    return user


# def get_role_service(
#     db: Session = Depends(get_db),
# ) -> RoleService:
#     repository = RoleRepository(db)

#     return RoleService(
#         repository,
#     )


def get_permission_service(
    db: Session = Depends(get_db),
) -> PermissionService:
    repository = PermissionRepository(db)

    return PermissionService(
        repository,
    )


def get_role_service(
    db: Session = Depends(get_db),
) -> RoleService:

    return RoleService(
        repository=RoleRepository(db),
        permission_repository=PermissionRepository(db),
        role_permission_repository=RolePermissionRepository(db),
    )
