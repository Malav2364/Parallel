from datetime import datetime, timedelta, UTC
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.exceptions.auth import InvalidTokenException,InvalidRefreshTokenException


def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    payload = data.copy()

    payload.update(
        {
            "exp": datetime.now(UTC) + expires_delta,
            "type": token_type,
        }
    )

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    data: dict[str, Any],
) -> str:
    return _create_token(
        data=data,
        expires_delta=timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
        token_type="access",
    )


def create_refresh_token(
    data: dict[str, Any],
) -> str:
    return _create_token(
        data=data,
        expires_delta=timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        ),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload

    except JWTError:
        raise InvalidTokenException()

def decode_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise InvalidTokenException()

    return payload

def decode_refresh_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise InvalidRefreshTokenException()

    return payload

def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )