from app.core.jwt import create_email_verification_token
from tests.factories import USER_DATA


def register_and_verify_user(client):
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


def login_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )

    return response.json()
