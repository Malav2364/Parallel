from app.core.jwt import create_password_reset_token
from tests.factories import USER_DATA
from tests.utils import (
    login_user,
    register_and_verify_user,
)


def test_forgot_password_success(client):
    register_and_verify_user(client)

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": USER_DATA["email"],
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "If an account with that email exists, " "a password reset email has been sent."
    )


def test_forgot_password_unknown_email(client):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "unknown@gmail.com",
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "If an account with that email exists, " "a password reset email has been sent."
    )


def test_reset_password_success(client):
    register_and_verify_user(client)

    token = create_password_reset_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == ("Password reset successfully.")


def test_old_password_no_longer_works(client):
    register_and_verify_user(client)

    token = create_password_reset_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )

    assert response.status_code == 401


def test_new_password_works(client):
    register_and_verify_user(client)

    token = create_password_reset_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": "NewPassword@123",
        },
    )

    assert response.status_code == 200


def test_reset_password_invalid_token(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid-token",
            "new_password": "Password@123",
        },
    )

    assert response.status_code == 401


def test_reset_password_missing_fields(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={},
    )

    assert response.status_code == 422


def test_password_reset_revokes_refresh_tokens(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    refresh_token = tokens["refresh_token"]

    token = create_password_reset_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
