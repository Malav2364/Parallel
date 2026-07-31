from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.jwt import decode_access_token
from app.exceptions.auth import InvalidTokenException
from app.models.user import User
from app.repositories.user_repository import UserRepository




def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

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