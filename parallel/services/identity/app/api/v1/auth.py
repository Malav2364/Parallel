from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AccessTokenResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    service = UserService(
        user_repository,
        refresh_token_repository,
    )

    created_user = service.register_user(user)

    return created_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    service = UserService(
        user_repository,
        refresh_token_repository,
    )

    user = service.authenticate_user(
        form_data.username,
        form_data.password,
    )

    access_token = create_access_token(
        data={
            "sub": user.email,
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
        }
    )

    service.save_refresh_token(
        user=user,
        refresh_token=refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    service = UserService(
        user_repository,
        refresh_token_repository,
    )

    access_token = service.refresh_access_token(
        request.refresh_token,
    )

    return AccessTokenResponse(
        access_token=access_token,
    )