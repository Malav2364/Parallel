import logging
import time
from datetime import datetime, timezone

from app.clients.github_client import GitHubClient
from app.clients.notifications_client import NotificationsClient
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories import SignalRepository, TokenRepository
from app.services import SignalService, TokenService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class GithubWatcher:
    def __init__(self, poll_interval: int | None = None) -> None:
        self.poll_interval = poll_interval or settings.WATCHER_POLL_INTERVAL
        self.notifications_client = NotificationsClient()

    def run(self) -> None:
        logger.info("GitHub watcher started.")

        while True:
            try:
                self.process_all_users()
            except Exception:
                logger.exception("Unexpected error while polling signals")

            time.sleep(self.poll_interval)

    def process_all_users(self) -> None:
        db = SessionLocal()

        try:
            token_repository = TokenRepository(db)
            signal_repository = SignalRepository(db)
            token_service = TokenService(token_repository, GitHubClient())
            signal_service = SignalService(
                signal_repository,
                token_service,
                GitHubClient(),
            )

            for user_id in token_repository.list_user_ids():
                self.process_user(
                    user_id=user_id,
                    signal_service=signal_service,
                    signal_repository=signal_repository,
                )
        finally:
            db.close()

    def process_user(
        self,
        user_id: str,
        signal_service: SignalService,
        signal_repository: SignalRepository,
    ) -> None:
        # Refresh from GitHub first; a sync failure must not block a nudge
        # for signals already stored.
        try:
            signal_service.sync(user_id)
        except Exception:
            logger.exception("Signal sync failed for user %s", user_id)

        pending = signal_repository.list_unnotified(user_id, "review_request")

        if not pending:
            return

        count = len(pending)
        suffix = "" if count == 1 else "s"

        self.notifications_client.create_notification(
            user_id=user_id,
            title="GitHub",
            message=f"{count} PR{suffix} waiting on your review",
            notification_type="github",
        )

        signal_repository.mark_notified(
            [signal.id for signal in pending],
            datetime.now(timezone.utc),
        )

        logger.info("Nudged user %s about %s review request(s)", user_id, count)


if __name__ == "__main__":
    GithubWatcher().run()
