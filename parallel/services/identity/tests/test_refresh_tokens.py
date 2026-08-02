from tests.utils import (
    login_user,
    register_and_verify_user,
)


def test_refresh_success(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    old_refresh = tokens["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data

    assert data["refresh_token"] != old_refresh


def test_old_refresh_token_cannot_be_used(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    old_refresh = tokens["refresh_token"]

    client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh,
        },
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh,
        },
    )

    assert response.status_code == 401


def test_invalid_refresh_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401


def test_refresh_missing_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    assert response.status_code == 422
