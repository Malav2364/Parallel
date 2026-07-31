from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import status
from app.core.jwt import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.api.deps import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from fastapi.security import OAuth2PasswordRequestForm

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)

from app.schemas.auth import (
    RefreshTokenRequest,
    AccessTokenResponse,
)

router=APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):

    repository = UserRepository(db)
    service = UserService(repository)
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
    repository = UserRepository(db)
    service = UserService(repository)

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
    repository = UserRepository(db)
    service = UserService(repository)

    access_token = service.refresh_access_token(
        request.refresh_token,
    )

    return AccessTokenResponse(
        access_token=access_token,
    )