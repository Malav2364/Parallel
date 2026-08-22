from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.services.reminder_service import ReminderService


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def service(repository):
    return ReminderService(repository)


def test_create_reminder_stores_utc_and_timezone(
    service,
    repository,
):
    repository.get_duplicate.return_value = None

    request = ReminderCreate(
        title="Morning Meeting",
        description="Team meeting",
        scheduled_for=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        timezone="Asia/Kolkata",
    )

    created_reminder = Reminder(
        id="reminder-1",
        owner_id="user-1",
        title="Morning Meeting",
        description="Team meeting",
        scheduled_for=datetime(
            2026,
            8,
            25,
            4,
            30,
            tzinfo=timezone.utc,
        ),
        timezone="Asia/Kolkata",
    )

    repository.create.return_value = created_reminder

    result = service.create_reminder(
        request=request,
        owner_id="user-1",
    )

    repository.get_duplicate.assert_called_once_with(
        owner_id="user-1",
        title="Morning Meeting",
        scheduled_for=datetime(
            2026,
            8,
            25,
            4,
            30,
            tzinfo=timezone.utc,
        ),
    )

    created = repository.create.call_args.args[0]

    assert created.scheduled_for == datetime(
        2026,
        8,
        25,
        4,
        30,
        tzinfo=timezone.utc,
    )
    assert created.timezone == "Asia/Kolkata"

    assert result == created_reminder


def test_create_reminder_supports_different_timezone(
    service,
    repository,
):
    repository.get_duplicate.return_value = None

    request = ReminderCreate(
        title="New York Reminder",
        scheduled_for=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        timezone="America/New_York",
    )

    repository.create.side_effect = lambda reminder: reminder

    result = service.create_reminder(
        request=request,
        owner_id="user-1",
    )

    assert result.timezone == "America/New_York"

    # August 25, 2026: New York is UTC-4
    assert result.scheduled_for == datetime(
        2026,
        8,
        25,
        14,
        0,
        tzinfo=timezone.utc,
    )


def test_duplicate_reminder_returns_existing_reminder(
    service,
    repository,
):
    existing = Mock(spec=Reminder)

    repository.get_duplicate.return_value = existing

    request = ReminderCreate(
        title="Meeting",
        scheduled_for=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        timezone="Asia/Kolkata",
    )

    result = service.create_reminder(
        request=request,
        owner_id="user-1",
    )

    assert result == existing
    repository.create.assert_not_called()


def test_update_scheduled_time_uses_existing_timezone(
    service,
    repository,
):
    reminder = Mock(spec=Reminder)

    reminder.id = "reminder-1"
    reminder.timezone = "Asia/Kolkata"

    repository.get_by_id.return_value = reminder
    repository.update.return_value = reminder

    request = ReminderUpdate(
        scheduled_for=datetime(
            2026,
            8,
            25,
            15,
            0,
        ),
    )

    result = service.update_reminder(
        reminder_id="reminder-1",
        request=request,
    )

    assert reminder.scheduled_for == datetime(
        2026,
        8,
        25,
        9,
        30,
        tzinfo=timezone.utc,
    )

    assert reminder.timezone == "Asia/Kolkata"
    assert result == reminder


def test_update_timezone_and_scheduled_time(
    service,
    repository,
):
    reminder = Mock(spec=Reminder)

    reminder.id = "reminder-1"
    reminder.timezone = "Asia/Kolkata"

    repository.get_by_id.return_value = reminder
    repository.update.return_value = reminder

    request = ReminderUpdate(
        scheduled_for=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        timezone="America/New_York",
    )

    result = service.update_reminder(
        reminder_id="reminder-1",
        request=request,
    )

    assert reminder.timezone == "America/New_York"

    # 10:00 New York (UTC-4) = 14:00 UTC
    assert reminder.scheduled_for == datetime(
        2026,
        8,
        25,
        14,
        0,
        tzinfo=timezone.utc,
    )

    assert result == reminder


def test_update_only_timezone(
    service,
    repository,
):
    reminder = Mock(spec=Reminder)

    reminder.id = "reminder-1"
    reminder.timezone = "Asia/Kolkata"

    repository.get_by_id.return_value = reminder
    repository.update.return_value = reminder

    request = ReminderUpdate(
        timezone="America/New_York",
    )

    result = service.update_reminder(
        reminder_id="reminder-1",
        request=request,
    )

    assert reminder.timezone == "America/New_York"
    assert result == reminder


def test_update_nonexistent_reminder(
    service,
    repository,
):
    repository.get_by_id.return_value = None

    request = ReminderUpdate(
        title="Updated",
    )

    result = service.update_reminder(
        reminder_id="does-not-exist",
        request=request,
    )

    assert result is None
    repository.update.assert_not_called()