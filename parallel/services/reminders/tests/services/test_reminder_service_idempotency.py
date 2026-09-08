from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate
from app.services.reminder_service import ReminderService


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def service(repository):
    return ReminderService(repository)


def _request():
    return ReminderCreate(
        title="Call mom",
        scheduled_for=datetime(2026, 8, 25, 10, 0),
        timezone="Asia/Kolkata",
    )


def test_matching_key_returns_existing_without_touching_create(
    service,
    repository,
):
    existing = Mock(spec=Reminder)
    repository.get_by_idempotency_key.return_value = existing

    result = service.create_reminder(
        request=_request(),
        owner_id="user-1",
        idempotency_key="key-1",
    )

    assert result is existing
    repository.get_by_idempotency_key.assert_called_once_with("key-1")
    repository.get_duplicate.assert_not_called()
    repository.create.assert_not_called()


def test_new_key_is_stored_on_the_created_reminder(
    service,
    repository,
):
    repository.get_by_idempotency_key.return_value = None
    repository.get_duplicate.return_value = None
    repository.create.side_effect = lambda reminder: reminder

    service.create_reminder(
        request=_request(),
        owner_id="user-1",
        idempotency_key="key-1",
    )

    created = repository.create.call_args.args[0]
    assert created.idempotency_key == "key-1"


def test_integrity_error_returns_the_race_winner_by_key(
    service,
    repository,
):
    winner = Mock(spec=Reminder)
    # Pre-insert lookup misses; the post-conflict lookup finds the winner.
    repository.get_by_idempotency_key.side_effect = [None, winner]
    repository.get_duplicate.return_value = None
    repository.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    result = service.create_reminder(
        request=_request(),
        owner_id="user-1",
        idempotency_key="key-1",
    )

    assert result is winner
    repository.rollback.assert_called_once()


def test_integrity_error_without_key_falls_back_to_natural_duplicate(
    service,
    repository,
):
    winner = Mock(spec=Reminder)
    repository.get_duplicate.side_effect = [None, winner]
    repository.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    result = service.create_reminder(
        request=_request(),
        owner_id="user-1",
    )

    assert result is winner
    repository.rollback.assert_called_once()
    repository.get_by_idempotency_key.assert_not_called()


def test_integrity_error_with_no_recoverable_row_reraises(
    service,
    repository,
):
    repository.get_by_idempotency_key.side_effect = [None, None]
    repository.get_duplicate.side_effect = [None, None]
    repository.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    with pytest.raises(IntegrityError):
        service.create_reminder(
            request=_request(),
            owner_id="user-1",
            idempotency_key="key-1",
        )

    repository.rollback.assert_called_once()
