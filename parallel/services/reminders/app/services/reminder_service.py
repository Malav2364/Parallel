from datetime import datetime, timezone, timedelta
from app.services.recurrence_service import RecurrenceService
from app.models.reminder import Reminder
from app.core.config import settings
from app.repositories.reminder_repository import ReminderRepository
from app.utils.datetime_utils import normalize_to_utc
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
)


class ReminderService:
    def __init__(
        self,
        repository: ReminderRepository,
    ) -> None:
        self.repository = repository

    def create_reminder(
        self,
        request: ReminderCreate,
        owner_id: str,
    ) -> Reminder:
        title = request.title.strip()

        existing = self.repository.get_duplicate(
            owner_id=owner_id,
            title=title,
            scheduled_for=request.scheduled_for,
            # recurrence=request.recurrence,
        )

        if existing is not None:
            return existing

        scheduled_for = normalize_to_utc(
            request.scheduled_for,
            request.timezone,
        )

        reminder = Reminder(
            owner_id=owner_id,
            title=title,
            description=request.description,
            scheduled_for=request.scheduled_for,
            recurrence=request.recurrence,
            status=request.status,
        )

        return self.repository.create(reminder)

    def list_reminders(
        self,
        owner_id: str,
    ) -> list[Reminder]:

        return self.repository.list_by_owner(
            owner_id
        )

    def get_reminder(
        self,
        reminder_id: str,
    ) -> Reminder | None:

        return self.repository.get_by_id(
            reminder_id
        )

    def update_reminder(
        self,
        reminder_id: str,
        request: ReminderUpdate,
    ) -> Reminder | None:

        reminder = self.repository.get_by_id(
            reminder_id
        )

        if reminder is None:
            return None

        if request.title is not None:
            reminder.title = request.title.strip()

        if request.description is not None:
            reminder.description = request.description

        if request.scheduled_for is not None:
            reminder.scheduled_for = normalize_to_utc(
                request.scheduled_for,
                request.timezone or "Asia/Kolkata",
            )

        if request.recurrence is not None:
            reminder.recurrence = request.recurrence

        if request.status is not None:
            reminder.status = request.status

        return self.repository.update(reminder)

    def delete_reminder(
        self,
        reminder_id: str,
    ) -> bool:

        reminder = self.repository.get_by_id(
            reminder_id
        )

        if reminder is None:
            return False

        self.repository.delete(reminder)

        return True

    def get_due_reminders(self) -> list[Reminder]:

        now = datetime.now(timezone.utc)

        return self.repository.get_pending_due(now)

    def claim_due_reminder(
        self,
        reminder_id: str,
    ) -> Reminder | None:
        now = datetime.now(timezone.utc)

        return self.repository.claim_due_reminder(
            reminder_id=reminder_id,
            now=now,
        )

    def mark_sent(
        self,
        reminder: Reminder,
    ) -> Reminder:
        return self.repository.mark_sent(
            reminder=reminder,
            processed_at=datetime.now(timezone.utc),
        )

    def mark_failed(
        self,
        reminder: Reminder,
        error: str,
    ) -> Reminder | None:
        return self.repository.mark_failed(
            reminder_id=reminder.id,
            error=error,
            max_attempts=settings.MAX_RETRY_ATTEMPTS,
        )

    def complete_reminder(
        self,
        reminder: Reminder,
    ) -> Reminder:

        next_occurrence = (
            RecurrenceService.get_next_occurrence(
                scheduled_for=reminder.scheduled_for,
                recurrence=reminder.recurrence,
            )
        )

        if next_occurrence is not None:
            return self.repository.reschedule(
                reminder=reminder,
                next_scheduled_for=next_occurrence,
            )

        return self.repository.mark_sent(
            reminder=reminder,
            processed_at=datetime.now(timezone.utc),
        )

    def claim_reminder(
        self,
        reminder_id: str,
    ) -> Reminder | None:
        now = datetime.now(timezone.utc)

        return self.repository.claim_reminder(
            reminder_id=reminder_id,
            now=now,
        )

    def fail_reminder(
        self,
        reminder_id: str,
        error: str,
    ) -> Reminder | None:
        return self.repository.mark_failed(
            reminder_id=reminder_id,
            error=error,
        )

    def recover_stale_reminders(
        self,
        timeout_minutes: int = 5,
    ) -> int:
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(minutes=timeout_minutes)
        )

        return self.repository.recover_stale_processing(
            cutoff=cutoff,
        )