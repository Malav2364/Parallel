from tests.factories import USER_DATA


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == USER_DATA["email"]
    assert data["first_name"] == USER_DATA["first_name"]
    assert data["last_name"] == USER_DATA["last_name"]


def test_register_duplicate_email(client):
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    response = client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    assert response.status_code == 400


def test_register_invalid_email(client):
    invalid_user = USER_DATA.copy()
    invalid_user["email"] = "invalid-email"

    response = client.post(
        "/api/v1/auth/register",
        json=invalid_user,
    )

    assert response.status_code == 422


def test_register_missing_first_name(client):
    invalid_user = USER_DATA.copy()
    invalid_user.pop("first_name")

    response = client.post(
        "/api/v1/auth/register",
        json=invalid_user,
    )

    assert response.status_code == 422
