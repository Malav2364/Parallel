from unittest.mock import MagicMock

from app.worker import ReminderWorker


def test_process_reminder_success():
    worker = ReminderWorker()

    service = MagicMock()

    reminder = MagicMock()
    reminder.id = "reminder-1"
    reminder.owner_id = "user-1"
    reminder.title = "Test Reminder"
    reminder.description = "Test message"

    service.repository.claim_due_reminder.return_value = reminder

    worker.notifications_client = MagicMock()

    service.complete_reminder = MagicMock()

    worker.process_reminder(
        service=service,
        reminder_id="reminder-1",
    )

    worker.notifications_client.create_notification.assert_called_once_with(
        user_id="user-1",
        title="Test Reminder",
        message="Test message",
        notification_type="reminder",
    )

    service.complete_reminder.assert_called_once_with(reminder)

    service.mark_failed.assert_not_called()