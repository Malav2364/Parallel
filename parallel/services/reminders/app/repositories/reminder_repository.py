from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        reminder: Reminder,
    ) -> Reminder:
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def list_by_owner(
        self,
        owner_id: str,
    ) -> list[Reminder]:
        statement = (
            select(Reminder)
            .where(Reminder.owner_id == owner_id)
            .order_by(Reminder.scheduled_for.asc())
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_id(
        self,
        reminder_id: str,
    ) -> Reminder | None:
        statement = select(Reminder).where(
            Reminder.id == reminder_id
        )

        return self.db.scalar(statement)

    def get_pending_due(
        self,
        now: datetime,
    ) -> list[Reminder]:
        statement = (
            select(Reminder)
            .where(
                Reminder.status == "pending",
                Reminder.scheduled_for <= now,
            )
            .order_by(Reminder.scheduled_for.asc())
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        reminder: Reminder,
    ) -> Reminder:
        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def delete(
        self,
        reminder: Reminder,
    ) -> None:
        self.db.delete(reminder)
        self.db.commit()

    def claim_due_reminder(
        self,
        reminder_id: str,
        now: datetime,
    ) -> Reminder | None:
        statement = (
            update(Reminder)
            .where(
                Reminder.id == reminder_id,
                Reminder.status == "pending",
                Reminder.scheduled_for <= now,
            )
            .values(
                status="processing",
                updated_at=now,
                processing_started_at=now,
            )
            .returning(Reminder)
        )

        reminder = self.db.execute(statement).scalar_one_or_none()

        self.db.commit()

        return reminder

    def claim_reminder(
        self,
        reminder_id: str,
        now: datetime,
    ) -> Reminder | None:
        statement = (
            update(Reminder)
            .where(
                Reminder.id == reminder_id,
                Reminder.status == "pending",
            )
            .values(
                status="processing",
                last_attempt_at=now,
                processing_started_at=now,
            )
            .returning(Reminder)
        )

        result = self.db.execute(statement)
        reminder = result.scalar_one_or_none()

        if reminder is not None:
            self.db.commit()

        return reminder

    def mark_failed(
        self,
        reminder_id: str,
        error: str,
        max_attempts: int,
    ) -> Reminder | None:
        reminder = self.get_by_id(reminder_id)

        if reminder is None:
            return None

        reminder.attempt_count += 1
        reminder.status = "pending"
        reminder.last_error = error[:2000]
        reminder.processing_started_at = None

        if reminder.attempt_count >= max_attempts:
            reminder.status = "failed"
        else:
            reminder.status = "pending"

        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def mark_sent(
        self,
        reminder: Reminder,
        processed_at: datetime,
    ) -> Reminder:
        reminder.status = "sent"
        reminder.processed_at = processed_at

        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def recover_stale_processing(
        self,
        cutoff: datetime,
    ) -> int:
        statement = (
            update(Reminder)
            .where(
                Reminder.status == "processing",
                Reminder.processing_started_at < cutoff,
            )
            .values(
                status="pending",
                processing_started_at=None,
            )
        )

        result = self.db.execute(statement)
        self.db.commit()

        return result.rowcount

    def reschedule(
        self,
        reminder: Reminder,
        next_scheduled_for: datetime,
    ) -> Reminder:
        reminder.scheduled_for = next_scheduled_for
        reminder.status = "pending"
        reminder.processed_at = None

        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def get_duplicate(
        self,
        owner_id: str,
        title: str,
        scheduled_for: datetime,
    ) -> Reminder | None:
        statement = (
            select(Reminder)
            .where(
                Reminder.owner_id == owner_id,
                Reminder.title == title,
                Reminder.scheduled_for == scheduled_for,
                Reminder.status.in_(
                    ["pending", "processing"]
                ),
            )
            .order_by(Reminder.created_at.asc())
            .limit(1)
        )

        return self.db.scalar(statement)