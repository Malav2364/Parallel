import logging
import time
from datetime import datetime, timezone

from app.clients.notifications_client import NotificationsClient
from app.core.database import SessionLocal
from app.repositories.reminder_repository import ReminderRepository
from app.services.reminder_service import ReminderService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class ReminderWorker:
    def __init__(
        self,
        poll_interval: int = 5,
    ) -> None:
        self.poll_interval = poll_interval
        self.notifications_client = NotificationsClient()

    def run(self) -> None:
        logger.info("Reminder worker started.")

        while True:
            try:
                self.process_due_reminders()

            except Exception:
                logger.exception(
                    "Unexpected error while processing reminders"
                )

            time.sleep(self.poll_interval)

    def process_due_reminders(self) -> None:
        db = SessionLocal()

        try:
            repository = ReminderRepository(db)
            service = ReminderService(repository)

            reminders = service.get_due_reminders()

            if not reminders:
                return

            logger.info(
                "Found %s due reminder(s)",
                len(reminders),
            )

            for reminder in reminders:
                self.process_reminder(
                    service=service,
                    reminder_id=reminder.id,
                )

        finally:
            db.close()

    def process_reminder(
        self,
        service: ReminderService,
        reminder_id: str,
    ) -> None:
        now = datetime.now(timezone.utc)

        # --------------------------------------------------
        # Claim reminder
        # --------------------------------------------------

        reminder = service.repository.claim_due_reminder(
            reminder_id=reminder_id,
            now=now,
        )

        # Another worker may have already claimed it.
        if reminder is None:
            return

        try:
            # --------------------------------------------------
            # Send notification
            # --------------------------------------------------

            self.notifications_client.create_notification(
                user_id=reminder.owner_id,
                title=reminder.title,
                message=(
                    reminder.description
                    or f"Reminder: {reminder.title}"
                ),
                notification_type="reminder",
            )

            # --------------------------------------------------
            # Mark successful
            # --------------------------------------------------

            service.complete_reminder(reminder)

            logger.info(
                "Reminder sent successfully: %s (%s)",
                reminder.id,
                reminder.title,
            )

        except Exception as exc:
            # --------------------------------------------------
            # Mark failed / schedule retry
            # --------------------------------------------------

            service.mark_failed(
                reminder,
                str(exc),
            )

            logger.exception(
                "Reminder failed: %s (%s)",
                reminder.id,
                reminder.title,
            )


if __name__ == "__main__":
    print("Starting Reminder Worker...", flush=True)

    worker = ReminderWorker()

    print("Reminder worker initialized.", flush=True)

    worker.run()