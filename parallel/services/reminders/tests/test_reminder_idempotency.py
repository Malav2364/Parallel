from uuid import uuid4


def _payload(title, scheduled_for="2026-08-25T21:00:00+05:30"):
    return {
        "title": title,
        "scheduled_for": scheduled_for,
        "timezone": "Asia/Kolkata",
        "status": "pending",
    }


def test_same_key_same_body_returns_one_row(client):
    owner = str(uuid4())
    title = f"Idem {uuid4()}"
    headers = {"X-User-Id": owner, "Idempotency-Key": str(uuid4())}

    first = client.post(
        "/api/v1/reminders",
        json=_payload(title),
        headers=headers,
    )
    second = client.post(
        "/api/v1/reminders",
        json=_payload(title),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    listing = client.get(
        "/api/v1/reminders",
        headers={"X-User-Id": owner},
    )

    assert listing.status_code == 200
    reminders = listing.json()
    assert len(reminders) == 1
    assert reminders[0]["id"] == first.json()["id"]


def test_same_key_different_body_returns_the_original(client):
    # A different scheduled_for slips past the natural-key dedup
    # (owner+title+scheduled_for), so only the idempotency key can
    # collapse these two into one row.
    owner = str(uuid4())
    title = f"Idem {uuid4()}"
    headers = {"X-User-Id": owner, "Idempotency-Key": str(uuid4())}

    first = client.post(
        "/api/v1/reminders",
        json=_payload(title, scheduled_for="2026-08-25T21:00:00+05:30"),
        headers=headers,
    )
    second = client.post(
        "/api/v1/reminders",
        json=_payload(title, scheduled_for="2026-08-26T09:00:00+05:30"),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    # The key wins: the second call returns the original row untouched.
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["scheduled_for"] == first.json()["scheduled_for"]

    listing = client.get(
        "/api/v1/reminders",
        headers={"X-User-Id": owner},
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_keyless_create_still_succeeds(client):
    owner = str(uuid4())
    title = f"Keyless {uuid4()}"

    response = client.post(
        "/api/v1/reminders",
        json=_payload(title),
        headers={"X-User-Id": owner},
    )

    assert response.status_code == 201
