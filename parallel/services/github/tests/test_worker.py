from unittest.mock import MagicMock

from app.worker import GithubWatcher


def _signal(signal_id):
    signal = MagicMock()
    signal.id = signal_id
    return signal


def test_process_user_nudges_and_marks_notified():
    watcher = GithubWatcher(poll_interval=1)
    watcher.notifications_client = MagicMock()

    signal_service = MagicMock()
    signal_repository = MagicMock()
    signal_repository.list_unnotified.return_value = [
        _signal("s1"),
        _signal("s2"),
    ]

    watcher.process_user(
        user_id="user-1",
        signal_service=signal_service,
        signal_repository=signal_repository,
    )

    signal_service.sync.assert_called_once_with("user-1")

    watcher.notifications_client.create_notification.assert_called_once()
    kwargs = watcher.notifications_client.create_notification.call_args.kwargs
    assert kwargs["user_id"] == "user-1"
    assert kwargs["message"] == "2 PRs waiting on your review"
    assert kwargs["notification_type"] == "github"

    marked_ids = signal_repository.mark_notified.call_args.args[0]
    assert marked_ids == ["s1", "s2"]


def test_process_user_uses_singular_for_one_pr():
    watcher = GithubWatcher(poll_interval=1)
    watcher.notifications_client = MagicMock()

    signal_repository = MagicMock()
    signal_repository.list_unnotified.return_value = [_signal("s1")]

    watcher.process_user(
        user_id="user-1",
        signal_service=MagicMock(),
        signal_repository=signal_repository,
    )

    kwargs = watcher.notifications_client.create_notification.call_args.kwargs
    assert kwargs["message"] == "1 PR waiting on your review"


def test_process_user_skips_when_nothing_pending():
    watcher = GithubWatcher(poll_interval=1)
    watcher.notifications_client = MagicMock()

    signal_repository = MagicMock()
    signal_repository.list_unnotified.return_value = []

    watcher.process_user(
        user_id="user-1",
        signal_service=MagicMock(),
        signal_repository=signal_repository,
    )

    watcher.notifications_client.create_notification.assert_not_called()
    signal_repository.mark_notified.assert_not_called()


def test_process_user_nudges_even_when_sync_fails():
    watcher = GithubWatcher(poll_interval=1)
    watcher.notifications_client = MagicMock()

    signal_service = MagicMock()
    signal_service.sync.side_effect = RuntimeError("github down")

    signal_repository = MagicMock()
    signal_repository.list_unnotified.return_value = [_signal("s1")]

    watcher.process_user(
        user_id="user-1",
        signal_service=signal_service,
        signal_repository=signal_repository,
    )

    watcher.notifications_client.create_notification.assert_called_once()
