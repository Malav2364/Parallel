import asyncio
from datetime import UTC, datetime

from app.core.config import settings
from app.core.datetime import ensure_utc
from app.core.jwt import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_password_reset_token,
    decode_refresh_token,
    refresh_token_expiry,
)
from app.core.logger import logger
from app.core.security import (
    hash_password,
    verify_password,
)
from app.core.token_hash import hash_token
from app.exceptions.auth import (
    EmailAlreadyExistsException,
    EmailAlreadyVerifiedException,
    EmailNotVerifiedException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    InvalidTokenException,
    InvalidVerificationTokenException,
    RefreshTokenRevokedException,
    UserAlreadyVerifiedException,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RefreshTokenResponse
from app.schemas.user import UserCreate
from app.services.email_service import EmailService


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.repository = repository
        self.refresh_token_repository = refresh_token_repository
        self.email_service = EmailService()

    # ==========================================
    # Private Helpers
    # ==========================================

    def _send_verification_email(
        self,
        user: User,
    ) -> None:
        verification_token = create_email_verification_token(
            {
                "sub": user.email,
            }
        )

        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        )

        asyncio.run(
            self.email_service.send_verification_email(
                email=user.email,
                first_name=user.first_name,
                verification_link=verification_link,
            )
        )

    def _send_password_reset_email(
        self,
        user: User,
    ) -> None:
        reset_token = create_password_reset_token(
            {
                "sub": user.email,
            }
        )

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        asyncio.run(
            self.email_service.send_password_reset_email(
                email=user.email,
                first_name=user.first_name,
                reset_link=reset_link,
            )
        )

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

        logger.info(
            "User registered: %s",
            created_user.email,
        )

        self._send_verification_email(
            created_user,
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
            logger.warning(
                "Invalid login attempt for %s",
                email,
            )

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()
            logger.warning(
                "Invalid login attempt for %s",
                email,
            )

        if not user.is_verified:
            logger.warning(
                "Login attempted with unverified email: %s",
                email,
            )
            raise EmailNotVerifiedException()

        logger.info(
            "User logged in: %s",
            user.email,
        )

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

        expires_at = ensure_utc(
            stored_token.expires_at,
        )

        if expires_at < datetime.now(UTC):
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

        logger.info(
            "Email verified: %s",
            user.email,
        )

    def resend_verification_email(
        self,
        email: str,
    ) -> None:

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsException()

        if user.is_verified:
            raise UserAlreadyVerifiedException()

        self._send_verification_email(
            user,
        )

    def forgot_password(
        self,
        email: str,
    ) -> None:

        user = self.repository.get_by_email(email)

        if user is None:
            return

        logger.info(
            "Password reset requested: %s",
            user.email,
        )

        self._send_password_reset_email(
            user,
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

        logger.info(
            "User logged out: %s",
            stored_token.user_id,
        )

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> None:

        payload = decode_password_reset_token(
            token,
        )

        email = payload.get("sub")

        if email is None:
            raise InvalidTokenException()

        user = self.repository.get_by_email(
            email,
        )

        if user is None:
            raise InvalidTokenException()

        user.password_hash = hash_password(
            new_password,
        )

        self.repository.update(
            user,
        )

        self.refresh_token_repository.revoke_all_for_user(
            user.id,
        )

        logger.info(
            "Password reset completed: %s",
            user.email,
        )
