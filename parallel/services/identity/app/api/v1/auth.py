from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_user_service
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
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
    service: UserService = Depends(get_user_service),
):

    created_user = service.register_user(user)

    return created_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(
        get_user_service,
    ),
):

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
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh(
    request: RefreshTokenRequest,
    service: UserService = Depends(
        get_user_service,
    ),
):
    return service.refresh_access_token(
        request.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: LogoutRequest,
    service: UserService = Depends(
        get_user_service,
    ),
):

    service.logout(
        request.refresh_token,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    token: str = Query(...),
    service: UserService = Depends(
        get_user_service,
    ),
):

    service.verify_email(token)

    return MessageResponse(
        message="Email verified successfully",
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def resend_verification(
    request: ResendVerificationRequest,
    service: UserService = Depends(
        get_user_service,
    ),
):

    service.resend_verification_email(
        request.email,
    )

    return MessageResponse(
        message="Verification email sent successfully.",
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request: ForgotPasswordRequest,
    service: UserService = Depends(
        get_user_service,
    ),
):

    service.forgot_password(
        request.email,
    )

    return MessageResponse(
        message=(
            "If an account with that email exists, "
            "a password reset email has been sent."
        ),
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    request: ResetPasswordRequest,
    service: UserService = Depends(
        get_user_service,
    ),
):

    service.reset_password(
        token=request.token,
        new_password=request.new_password,
    )

    return MessageResponse(
        message="Password reset successfully.",
    )
