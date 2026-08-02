from app.core.jwt import (
    create_access_token,
    decode_refresh_token,
    create_refresh_token,
    refresh_token_expiry,
    create_email_verification_token,
    decode_email_verification_token,
)
from app.services.email_service import EmailService
from app.core.security import (
    hash_password,
    verify_password,
)
from app.core.token_hash import hash_token
from app.exceptions.auth import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    RefreshTokenRevokedException,
    EmailAlreadyVerifiedException,
    InvalidVerificationTokenException,
    EmailNotVerifiedException,
    UserAlreadyVerifiedException,
)
import asyncio
from app.core.config import settings
from app.schemas.auth import RefreshTokenResponse
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
        self.email_service = EmailService()

    def register_user(
        self,
        user: UserCreate,
    ) -> User:

        existing_user = self.repository.get_by_email(
            user.email,
        )

        if existing_user:
            raise EmailAlreadyExistsException()

        hashed_password = hash_password(
            user.password,
        )

        new_user = User(
            email=user.email,
            password_hash=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        created_user = self.repository.create(
            new_user,
        )

        verification_token = create_email_verification_token(
            {
                "sub": created_user.email,
            }
        )

        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email"
            f"?token={verification_token}"
        )

        asyncio.run(
            self.email_service.send_verification_email(
                email=created_user.email,
                first_name=created_user.first_name,
                verification_link=verification_link,
            )
        )

        return created_user
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

        if not user.is_verified:
            raise EmailNotVerifiedException()

        return user

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> RefreshTokenResponse:

        payload = decode_refresh_token(refresh_token)

        token_hash = hash_token(refresh_token)

        stored_token = self.refresh_token_repository.get_by_token_hash(
            token_hash,
        )

        if stored_token is None:
            raise InvalidRefreshTokenException()

        if stored_token.is_revoked:
            raise RefreshTokenRevokedException()

        if stored_token.expires_at < datetime.now(UTC):
            raise InvalidRefreshTokenException()

        email = payload.get("sub")

        if email is None:
            raise InvalidRefreshTokenException()

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidRefreshTokenException()

        self.refresh_token_repository.revoke(
            stored_token,
        )

        access_token = create_access_token(
            {
                "sub": user.email,
            }
        )

        new_refresh_token = create_refresh_token(
            {
                "sub": user.email,
            }
        )

        self.save_refresh_token(
            user=user,
            refresh_token=new_refresh_token,
        )

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
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

    def verify_email(
        self,
        token: str,
    ) -> None:

        payload = decode_email_verification_token(
            token,
        )

        email = payload.get("sub")

        if email is None:
            raise InvalidVerificationTokenException()

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidVerificationTokenException()

        if user.is_verified:
            raise EmailAlreadyVerifiedException()

        user.is_verified = True

        self.repository.update(user)

    def resend_verification_email(
        self,
        email: str,
    ) -> None:

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsException()

        if user.is_verified:
            raise UserAlreadyVerifiedException()

        verification_token = create_email_verification_token(
            {
                "sub": user.email,
            }
        )

        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email"
            f"?token={verification_token}"
        )

        import asyncio

        asyncio.run(
            self.email_service.send_verification_email(
                email=user.email,
                first_name=user.first_name,
                verification_link=verification_link,
            )
        )

    def logout(
        self,
        refresh_token: str,
    ) -> None:
        decode_refresh_token(refresh_token)
        token_hash = hash_token(refresh_token)
        stored_token = self.refresh_token_repository.get_by_token_hash(
            token_hash,
        )

        if stored_token is None:
            raise InvalidRefreshTokenException()

        if stored_token.is_revoked:
            raise RefreshTokenRevokedException()
        
        self.refresh_token_repository.revoke(stored_token)