from tests.factories import USER_DATA
from tests.utils import (
    assign_permission_to_user,
    login_user,
    register_and_verify_user,
)


def test_user_with_permission_can_view_profile(client):
    register_and_verify_user(client)

    assign_permission_to_user(
        USER_DATA["email"],
        "view_profile",
    )

    tokens = login_user(client)

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200


def test_user_without_permission_gets_403(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 403


def test_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_user_with_manage_roles_permission_can_get_roles(client):
    register_and_verify_user(client)

    assign_permission_to_user(
        USER_DATA["email"],
        "manage_roles",
    )

    tokens = login_user(client)

    response = client.get(
        "/api/v1/roles",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200


def test_user_without_manage_roles_permission_gets_403(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    response = client.get(
        "/api/v1/roles",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 403


def test_user_with_manage_permissions_can_get_permissions(client):
    register_and_verify_user(client)

    assign_permission_to_user(
        USER_DATA["email"],
        "manage_permissions",
    )

    tokens = login_user(client)

    response = client.get(
        "/api/v1/permissions",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200


def test_user_without_manage_permissions_gets_403(client):
    register_and_verify_user(client)

    tokens = login_user(client)

    response = client.get(
        "/api/v1/permissions",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 403
