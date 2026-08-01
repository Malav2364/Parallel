from fastapi import status

from app.exceptions.exceptions import ParallelException


class EmailAlreadyExistsException(ParallelException):
    """Raised when attempting to register an email that already exists."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="AUTH_001",
            message="Email already registered",
        )


class InvalidCredentialsException(ParallelException):
    """Raised when the supplied email or password is invalid."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_002",
            message="Invalid email or password",
        )


class UserNotFoundException(ParallelException):
    """Raised when a requested user cannot be found."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="AUTH_003",
            message="User not found",
        )

class InvalidTokenException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_004",
            message="Invalid or expired access token",
        )

class InvalidRefreshTokenException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_005",
            message="Invalid or expired refresh token",
        )

class RefreshTokenRevokedException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_006",
            message="Refresh token has been revoked",
        )