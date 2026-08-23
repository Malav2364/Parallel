"""Deterministic idempotency key behaviour."""

from app.services.idempotency import build_key


def test_key_is_deterministic() -> None:
    a = build_key("user-1", "create_reminder", "Call mom", "2026-08-24T09:00")
    b = build_key("user-1", "create_reminder", "Call mom", "2026-08-24T09:00")
    assert a == b


def test_key_normalises_whitespace_and_case() -> None:
    a = build_key("user-1", "create_reminder", "  Call Mom ")
    b = build_key("user-1", "create_reminder", "call mom")
    assert a == b


def test_key_differs_on_user() -> None:
    a = build_key("user-1", "create_reminder", "Call mom")
    b = build_key("user-2", "create_reminder", "Call mom")
    assert a != b


def test_key_differs_on_natural_key() -> None:
    a = build_key("user-1", "create_reminder", "Call mom", "09:00")
    b = build_key("user-1", "create_reminder", "Call dad", "09:00")
    assert a != b


def test_key_is_sha256_hex() -> None:
    key = build_key("user-1", "create_reminder", "Call mom")
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)


def test_missing_parts_are_treated_as_empty() -> None:
    a = build_key("user-1", "create_reminder", None)
    b = build_key("user-1", "create_reminder", "")
    assert a == b
