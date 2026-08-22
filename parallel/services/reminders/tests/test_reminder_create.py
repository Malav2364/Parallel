import pytest


def test_create_reminder(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study SQL",
            "description": "Practice joins",
            "scheduled_for": "2026-08-22T20:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "recurrence": None,
            "status": "pending",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Study SQL"
    assert data["description"] == "Practice joins"
    assert data["timezone"] == "Asia/Kolkata"
    assert data["recurrence"] is None
    assert data["status"] == "pending"


def test_create_reminder_rejects_empty_title(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "",
            "scheduled_for": "2026-08-22T20:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 422


def test_create_reminder_rejects_invalid_recurrence(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Invalid recurrence",
            "scheduled_for": "2026-08-22T20:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "recurrence": "yearly",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "recurrence",
    ["daily", "weekly", "monthly"],
)
def test_valid_recurrence_values(client, recurrence):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": f"Test {recurrence}",
            "scheduled_for": "2026-08-22T20:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "recurrence": recurrence,
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 201


def test_create_reminder_requires_scheduled_for(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study SQL",
            "timezone": "Asia/Kolkata",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 422


def test_create_reminder_rejects_invalid_datetime(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study SQL",
            "scheduled_for": "not-a-datetime",
            "timezone": "Asia/Kolkata",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 422


def test_create_reminder_uses_default_timezone(client):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study SQL",
            "scheduled_for": "2026-08-22T20:00:00+05:30",
        },
        headers={"X-User-Id": "test-user"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["timezone"] == "Asia/Kolkata"