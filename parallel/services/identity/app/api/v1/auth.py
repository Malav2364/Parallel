from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
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