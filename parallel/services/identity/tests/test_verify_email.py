from app.core.jwt import create_email_verification_token
from tests.factories import USER_DATA


def test_verify_email_success(client):
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    token = create_email_verification_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    response = client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == ("Email verified successfully")


def test_verify_email_already_verified(client):
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    token = create_email_verification_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )

    response = client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )

    assert response.status_code == 400


def test_verify_email_invalid_token(client):
    response = client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": "invalid-token",
        },
    )

    assert response.status_code == 401


def test_verify_email_missing_token(client):
    response = client.get(
        "/api/v1/auth/verify-email",
    )

    assert response.status_code == 422


def test_verify_email_non_existing_user(client):
    token = create_email_verification_token(
        {
            "sub": "nouser@example.com",
        }
    )

    response = client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )

    assert response.status_code == 401
