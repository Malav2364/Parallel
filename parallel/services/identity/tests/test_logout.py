from tests.utils import (
    login_user,
    register_and_verify_user,
)


def test_logout_success(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 204


def test_logout_twice(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 401


def test_logout_invalid_token(client):
    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401


def test_logout_missing_token(client):
    response = client.post(
        "/api/v1/auth/logout",
        json={},
    )

    assert response.status_code == 422
