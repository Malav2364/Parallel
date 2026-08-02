from app.core.jwt import create_email_verification_token
from app.models.refresh_token import RefreshToken
from tests.database import TestingSessionLocal
from tests.factories import USER_DATA


def test_login_success(client):
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    # Generate verification token
    token = create_email_verification_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    # Verify email
    client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    db = TestingSessionLocal()

    tokens = db.query(RefreshToken).all()

    assert len(tokens) == 1

    db.close()


def test_login_wrong_password(client):
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

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401


def test_login_unverified_email(client):
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )

    assert response.status_code == 403


def test_login_unknown_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "Password@123",
        },
    )

    assert response.status_code == 401
