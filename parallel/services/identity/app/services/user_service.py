from app.core.jwt import (
    create_access_token,
    decode_refresh_token,
    refresh_token_expiry,
)
from app.core.security import (
    hash_password,
    verify_password,
)
from app.core.token_hash import hash_token
from app.exceptions.auth import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    RefreshTokenRevokedException
)

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from datetime import datetime, UTC

from app.core.token_hash import hash_token


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.repository = repository
        self.refresh_token_repository = refresh_token_repository

    def register_user(
        self,
        user: UserCreate,
    ) -> User:

        existing_user = self.repository.get_by_email(user.email)

        if existing_user:
            raise EmailAlreadyExistsException()

        hashed_password = hash_password(user.password)

        new_user = User(
            email=user.email,
            password_hash=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        return self.repository.create(new_user)

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsException()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        return user

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> str:

        # 1. Verify JWT signature & type
        payload = decode_refresh_token(refresh_token)

        # 2. Hash the incoming refresh token
        token_hash = hash_token(refresh_token)

        # 3. Find token in database
        stored_token = self.refresh_token_repository.get_by_token_hash(
            token_hash,
        )

        if stored_token is None:
            raise InvalidRefreshTokenException()

        # 4. Check if revoked
        if stored_token.is_revoked:
            raise RefreshTokenRevokedException()

        # 5. Check expiry stored in DB
        if stored_token.expires_at < datetime.now(UTC):
            raise InvalidRefreshTokenException()

        # 6. Get email from JWT
        email = payload.get("sub")

        if email is None:
            raise InvalidRefreshTokenException()

        # 7. Find user
        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidRefreshTokenException()

        # 8. Return new access token
        return create_access_token(
            {
                "sub": user.email,
            }
        )

    def save_refresh_token(
        self,
        user: User,
        refresh_token: str,
    ) -> None:

        hashed_token = hash_token(refresh_token)

        token = RefreshToken(
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=refresh_token_expiry(),
        )

        self.refresh_token_repository.create(token)

    def logout(
        self,
        refresh_token: str,
    ) -> None:

        # Verify JWT is valid
        decode_refresh_token(refresh_token)

        # Hash incoming refresh token
        token_hash = hash_token(refresh_token)

        # Find token in database
        stored_token = self.refresh_token_repository.get_by_token_hash(
            token_hash,
        )

        if stored_token is None:
            raise InvalidRefreshTokenException()

        # Already revoked
        if stored_token.is_revoked:
            raise RefreshTokenRevokedException()

        # Revoke token
        self.refresh_token_repository.revoke(stored_token)