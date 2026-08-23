"""ActionExecutor reminder path: dedup, read-back, and error handling.

A fake reminders client stands in for the HTTP layer so these exercise the
executor's guarantees without a network: retries/double-taps do not create
duplicates, a write is read back before success is reported, and downstream
failures surface as structured results instead of raising.
"""

import httpx
import pytest

from app.schemas.decision import ContextDecision
from app.services.action_executor import ActionExecutor


class FakeRemindersClient:
    def __init__(
        self,
        existing=None,
        created=None,
        readback="echo",
        raise_on_create=False,
    ) -> None:
        self.existing = existing
        self.created = created if created is not None else {"id": "rem-1"}
        self.readback = readback  # "echo" -> return created; else value as-is
        self.raise_on_create = raise_on_create
        self.create_calls: list[dict] = []
        self.readback_calls: list[str] = []

    async def get_by_details(self, user_id, title, scheduled_for):
        return self.existing

    async def create_reminder(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.raise_on_create:
            raise httpx.HTTPError("boom")
        return self.created

    async def get_reminder(self, user_id, reminder_id):
        self.readback_calls.append(reminder_id)
        if self.readback == "echo":
            return self.created
        return self.readback


class FakeGoalsClient:
    def __init__(
        self,
        existing=None,
        created=None,
        readback="found",
        raise_on_create=False,
    ) -> None:
        self.existing = existing
        self.created = created if created is not None else {"id": "goal-1"}
        self.readback = readback  # "found" -> return created; else value as-is
        self.raise_on_create = raise_on_create
        self.create_calls: list[dict] = []
        self.get_by_name_calls = 0

    async def get_by_name(self, user_id, name):
        # First call is the pre-create dedup check; later calls are read-backs.
        self.get_by_name_calls += 1
        if self.get_by_name_calls == 1:
            return self.existing
        if self.readback == "found":
            return self.created
        return self.readback

    async def create_goal(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.raise_on_create:
            raise httpx.HTTPError("boom")
        return self.created


class FakeHabitsClient:
    def __init__(
        self,
        existing=None,
        created=None,
        readback="found",
        raise_on_create=False,
    ) -> None:
        self.existing = existing
        self.created = created if created is not None else {"id": "habit-1"}
        self.readback = readback  # "found" -> return created; else value as-is
        self.raise_on_create = raise_on_create
        self.create_calls: list[dict] = []
        self.get_by_name_calls = 0

    async def get_by_name(self, user_id, name):
        # First call is the pre-create dedup check; later calls are read-backs.
        self.get_by_name_calls += 1
        if self.get_by_name_calls == 1:
            return self.existing
        if self.readback == "found":
            return self.created
        return self.readback

    async def create_habit(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.raise_on_create:
            raise httpx.HTTPError("boom")
        return self.created


class FakeProjectsClient:
    def __init__(
        self,
        existing=None,
        created=None,
        readback="found",
        raise_on_create=False,
    ) -> None:
        self.existing = existing
        self.created = created if created is not None else {"id": "proj-1"}
        self.readback = readback  # "found" -> return created; else value as-is
        self.raise_on_create = raise_on_create
        self.create_calls: list[dict] = []
        self.get_by_name_calls = 0

    async def get_by_name(self, user_id, name):
        # First call is the pre-create dedup check; later calls are read-backs.
        self.get_by_name_calls += 1
        if self.get_by_name_calls == 1:
            return self.existing
        if self.readback == "found":
            return self.created
        return self.readback

    async def create_project(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.raise_on_create:
            raise httpx.HTTPError("boom")
        return self.created


def _executor(
    reminders_client=None,
    *,
    goals_client=None,
    habits_client=None,
    projects_client=None,
) -> ActionExecutor:
    return ActionExecutor(
        projects_client=projects_client,
        workspace_client=None,
        goals_client=goals_client,
        habits_client=habits_client,
        reminders_client=reminders_client,
    )


def _decision(**overrides) -> ContextDecision:
    base = dict(
        action="create_reminder",
        reason="test",
        reminder_title="Call mom",
        reminder_date="tomorrow",
        reminder_time="09:00",
    )
    base.update(overrides)
    return ContextDecision(**base)


def _goal_decision(**overrides) -> ContextDecision:
    base = dict(action="create_goal", reason="test", goal_name="Learn piano")
    base.update(overrides)
    return ContextDecision(**base)


def _habit_decision(**overrides) -> ContextDecision:
    base = dict(
        action="create_habit",
        reason="test",
        habit_name="Meditate",
        habit_schedule="daily",
    )
    base.update(overrides)
    return ContextDecision(**base)


def _project_decision(**overrides) -> ContextDecision:
    base = dict(action="create_project", reason="test", project_name="Website")
    base.update(overrides)
    return ContextDecision(**base)


async def test_happy_path_creates_and_verifies() -> None:
    client = FakeRemindersClient(created={"id": "rem-1", "title": "Call mom"})
    result = await _executor(client).execute("user-1", _decision())

    assert result["executed"] is True
    assert result["reminder_created"] is True
    assert result["verified"] is True
    assert result["idempotency_key"]
    assert client.readback_calls == ["rem-1"]
    # The read-back copy is preferred as the returned reminder.
    assert result["reminder"] == {"id": "rem-1", "title": "Call mom"}


async def test_duplicate_is_not_recreated() -> None:
    client = FakeRemindersClient(existing={"id": "rem-0"})
    result = await _executor(client).execute("user-1", _decision())

    assert result["executed"] is False
    assert result["reminder_created"] is False
    assert result["reason"] == "Reminder already exists."
    assert client.create_calls == []  # never hit the write


async def test_idempotency_key_is_stable_across_retries() -> None:
    client = FakeRemindersClient()
    executor = _executor(client)

    first = await executor.execute("user-1", _decision())
    second = await executor.execute("user-1", _decision())

    assert first["idempotency_key"] == second["idempotency_key"]
    # The same key is what gets sent downstream on every attempt.
    assert client.create_calls[0]["idempotency_key"] == first["idempotency_key"]


async def test_create_forwards_idempotency_key() -> None:
    client = FakeRemindersClient()
    result = await _executor(client).execute("user-1", _decision())

    assert client.create_calls[0]["idempotency_key"] == result["idempotency_key"]


async def test_unverifiable_write_is_flagged() -> None:
    # Create claims success but the read-back cannot find it.
    client = FakeRemindersClient(readback=None)
    result = await _executor(client).execute("user-1", _decision())

    assert result["executed"] is True
    assert result["verified"] is False


async def test_missing_id_is_not_reported_as_success() -> None:
    client = FakeRemindersClient(created={"title": "Call mom"})  # no id
    result = await _executor(client).execute("user-1", _decision())

    assert result["executed"] is False
    assert "not verified" in result["reason"]


async def test_downstream_error_is_structured_not_raised() -> None:
    client = FakeRemindersClient(raise_on_create=True)
    result = await _executor(client).execute("user-1", _decision())

    assert result["executed"] is False
    assert "failed" in result["reason"]
    assert result["idempotency_key"]


@pytest.mark.parametrize(
    "overrides, reason_fragment",
    [
        ({"reminder_title": None}, "title"),
        ({"reminder_date": None}, "date"),
        ({"reminder_time": None}, "time"),
    ],
)
async def test_missing_fields_are_rejected(overrides, reason_fragment) -> None:
    client = FakeRemindersClient()
    result = await _executor(client).execute("user-1", _decision(**overrides))

    assert result["executed"] is False
    assert reason_fragment in result["reason"].lower()
    assert client.create_calls == []


async def test_goal_happy_path_creates_and_verifies() -> None:
    client = FakeGoalsClient(created={"id": "goal-1", "name": "Learn piano"})
    result = await _executor(goals_client=client).execute("user-1", _goal_decision())

    assert result["executed"] is True
    assert result["goal_created"] is True
    assert result["verified"] is True
    assert result["idempotency_key"]
    assert len(client.create_calls) == 1
    # The read-back copy is preferred as the returned goal.
    assert result["goal"] == {"id": "goal-1", "name": "Learn piano"}


async def test_goal_duplicate_is_not_recreated() -> None:
    client = FakeGoalsClient(existing={"id": "goal-0"})
    result = await _executor(goals_client=client).execute("user-1", _goal_decision())

    assert result["executed"] is False
    assert result["goal_created"] is False
    assert result["reason"] == "Goal already exists."
    assert client.create_calls == []  # never hit the write


async def test_goal_create_forwards_idempotency_key() -> None:
    client = FakeGoalsClient()
    result = await _executor(goals_client=client).execute("user-1", _goal_decision())

    assert client.create_calls[0]["idempotency_key"] == result["idempotency_key"]


async def test_goal_unverifiable_write_is_flagged() -> None:
    # Create claims success but the read-back cannot find it by name.
    client = FakeGoalsClient(readback=None)
    result = await _executor(goals_client=client).execute("user-1", _goal_decision())

    assert result["executed"] is True
    assert result["verified"] is False


async def test_goal_downstream_error_is_structured_not_raised() -> None:
    client = FakeGoalsClient(raise_on_create=True)
    result = await _executor(goals_client=client).execute("user-1", _goal_decision())

    assert result["executed"] is False
    assert "failed" in result["reason"]
    assert result["idempotency_key"]


async def test_goal_missing_name_is_rejected() -> None:
    client = FakeGoalsClient()
    result = await _executor(goals_client=client).execute(
        "user-1", _goal_decision(goal_name=None)
    )

    assert result["executed"] is False
    assert "name" in result["reason"].lower()
    assert client.create_calls == []


async def test_habit_happy_path_creates_and_verifies() -> None:
    client = FakeHabitsClient(created={"id": "habit-1", "name": "Meditate"})
    result = await _executor(habits_client=client).execute("user-1", _habit_decision())

    assert result["executed"] is True
    assert result["habit_created"] is True
    assert result["verified"] is True
    assert result["idempotency_key"]
    assert len(client.create_calls) == 1
    # The read-back copy is preferred as the returned habit.
    assert result["habit"] == {"id": "habit-1", "name": "Meditate"}


async def test_habit_duplicate_is_not_recreated() -> None:
    client = FakeHabitsClient(existing={"id": "habit-0"})
    result = await _executor(habits_client=client).execute("user-1", _habit_decision())

    assert result["executed"] is False
    assert result["habit_created"] is False
    assert result["reason"] == "Habit already exists."
    assert client.create_calls == []  # never hit the write


async def test_habit_create_forwards_idempotency_key() -> None:
    client = FakeHabitsClient()
    result = await _executor(habits_client=client).execute("user-1", _habit_decision())

    assert client.create_calls[0]["idempotency_key"] == result["idempotency_key"]


async def test_habit_unverifiable_write_is_flagged() -> None:
    # Create claims success but the read-back cannot find it by name.
    client = FakeHabitsClient(readback=None)
    result = await _executor(habits_client=client).execute("user-1", _habit_decision())

    assert result["executed"] is True
    assert result["verified"] is False


async def test_habit_downstream_error_is_structured_not_raised() -> None:
    client = FakeHabitsClient(raise_on_create=True)
    result = await _executor(habits_client=client).execute("user-1", _habit_decision())

    assert result["executed"] is False
    assert "failed" in result["reason"]
    assert result["idempotency_key"]


@pytest.mark.parametrize(
    "overrides, reason_fragment",
    [
        ({"habit_name": None}, "activity"),
        ({"habit_schedule": None}, "schedule"),
    ],
)
async def test_habit_missing_fields_are_rejected(overrides, reason_fragment) -> None:
    client = FakeHabitsClient()
    result = await _executor(habits_client=client).execute(
        "user-1", _habit_decision(**overrides)
    )

    assert result["executed"] is False
    assert reason_fragment in result["reason"].lower()
    assert client.create_calls == []


async def test_project_happy_path_creates_and_verifies() -> None:
    client = FakeProjectsClient(created={"id": "proj-1", "name": "Website"})
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision()
    )

    assert result["executed"] is True
    assert result["project_created"] is True
    assert result["verified"] is True
    assert result["idempotency_key"]
    assert len(client.create_calls) == 1
    # The read-back copy is preferred as the returned project.
    assert result["project"] == {"id": "proj-1", "name": "Website"}


async def test_project_duplicate_is_not_recreated() -> None:
    # Projects do not early-return on a duplicate (a space/association may
    # still be pending), but the project itself must not be recreated.
    client = FakeProjectsClient(existing={"id": "proj-0"})
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision()
    )

    assert result["executed"] is False
    assert result["project_created"] is False
    assert client.create_calls == []  # never hit the write


async def test_project_create_forwards_idempotency_key() -> None:
    client = FakeProjectsClient()
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision()
    )

    assert client.create_calls[0]["idempotency_key"] == result["idempotency_key"]


async def test_project_unverifiable_write_is_flagged() -> None:
    # Create claims success but the read-back cannot find it by name.
    client = FakeProjectsClient(readback=None)
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision()
    )

    assert result["executed"] is True
    assert result["verified"] is False


async def test_project_downstream_error_is_structured_not_raised() -> None:
    client = FakeProjectsClient(raise_on_create=True)
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision()
    )

    assert result["executed"] is False
    assert "failed" in result["reason"]
    assert result["idempotency_key"]


async def test_project_missing_name_is_rejected() -> None:
    client = FakeProjectsClient()
    result = await _executor(projects_client=client).execute(
        "user-1", _project_decision(project_name=None)
    )

    assert result["executed"] is False
    assert "name" in result["reason"].lower()
    assert client.create_calls == []


def _scheduled_decision(**overrides) -> ContextDecision:
    # A reminder decision carrying a pre-resolved absolute datetime (as the
    # deterministic Tier-1 cascade emits) instead of date/time expressions.
    base = dict(
        action="create_reminder",
        reason="test",
        reminder_title="Call mom",
        reminder_scheduled_for="2999-01-01T09:00:00+05:30",
    )
    base.update(overrides)
    return ContextDecision(**base)


async def test_reminder_scheduled_for_creates_and_verifies() -> None:
    client = FakeRemindersClient(created={"id": "rem-1", "title": "Call mom"})
    result = await _executor(client).execute("user-1", _scheduled_decision())

    assert result["executed"] is True
    assert result["reminder_created"] is True
    assert result["verified"] is True
    assert result["idempotency_key"]
    # The absolute datetime was used directly, normalized to IST.
    assert client.create_calls[0]["scheduled_for"] == "2999-01-01T09:00:00+05:30"


async def test_reminder_scheduled_for_in_the_past_is_rejected() -> None:
    client = FakeRemindersClient()
    result = await _executor(client).execute(
        "user-1",
        _scheduled_decision(reminder_scheduled_for="2000-01-01T09:00:00+05:30"),
    )

    assert result["executed"] is False
    assert "past" in result["reason"].lower()
    assert client.create_calls == []


async def test_reminder_scheduled_for_malformed_is_structured_not_raised() -> None:
    client = FakeRemindersClient()
    result = await _executor(client).execute(
        "user-1",
        _scheduled_decision(reminder_scheduled_for="not-a-datetime"),
    )

    assert result["executed"] is False
    assert "scheduled_for" in result["reason"].lower()
    assert client.create_calls == []


async def test_reminder_naive_scheduled_for_is_treated_as_ist() -> None:
    # A tz-naive ISO string is assumed to already be IST and normalized.
    client = FakeRemindersClient()
    result = await _executor(client).execute(
        "user-1",
        _scheduled_decision(reminder_scheduled_for="2999-01-01T09:00:00"),
    )

    assert result["executed"] is True
    assert client.create_calls[0]["scheduled_for"] == "2999-01-01T09:00:00+05:30"


async def test_reminder_scheduled_for_takes_precedence_over_date_time() -> None:
    # When both are present the pre-resolved absolute datetime wins and the
    # narrow date/time resolver is not consulted.
    client = FakeRemindersClient()
    result = await _executor(client).execute(
        "user-1",
        _scheduled_decision(
            reminder_date="tomorrow",
            reminder_time="09:00",
        ),
    )

    assert result["executed"] is True
    assert client.create_calls[0]["scheduled_for"] == "2999-01-01T09:00:00+05:30"
