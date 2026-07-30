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
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)

    user = service.authenticate_user(
        credentials.email,
        credentials.password,
    )

    access_token = create_access_token(
        data={
            "sub": user.email,
        }
    )

    return TokenResponse(
        access_token=access_token,
    )