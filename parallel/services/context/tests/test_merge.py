"""merge_answer fills a pending proposal's missing slot from a reply.

Anchored to the same fixed clock as test_rules (Sunday 2026-08-23 10:00 IST)
so relative phrases in the answer resolve to stable datetimes. A completed
proposal comes back HIGH; an answer that still doesn't resolve stays MEDIUM.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.nlu.rules import merge_answer
from app.nlu.schemas import ProposedAction

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 8, 23, 10, 0, tzinfo=IST)


def _pending(action: str, slots: dict, reason: str = "test") -> ProposedAction:
    return ProposedAction(
        action=action,
        source="rules",
        confidence=0.5,
        slots=slots,
        reason=reason,
    )


def _clarify(activity: str, schedule: str) -> ProposedAction:
    return ProposedAction(
        action="none",
        source="rules",
        confidence=0.3,
        slots={
            "activity": activity,
            "schedule": schedule,
            "candidates": ["create_habit", "create_reminder"],
        },
        reason="ambiguous: recurring activity, category unclear",
    )


def test_reminder_answer_resolves_time_to_high() -> None:
    pending = _pending("create_reminder", {"title": "submit report"})

    merged = merge_answer(pending, "tomorrow at 5pm", now=NOW)

    assert merged.band == "high"
    assert merged.is_executable
    assert merged.slots["title"] == "submit report"
    assert merged.slots["scheduled_for"].startswith("2026-08-24T17:00")


def test_reminder_answer_carries_recurrence() -> None:
    pending = _pending("create_reminder", {"title": "drink water"})

    merged = merge_answer(pending, "every day at 9am", now=NOW)

    assert merged.is_executable
    assert merged.slots["recurrence"] == "daily"


def test_habit_answer_resolves_schedule_to_high() -> None:
    pending = _pending("create_habit", {"title": "reading"})

    merged = merge_answer(pending, "daily", now=NOW)

    assert merged.band == "high"
    assert merged.is_executable
    assert merged.slots["title"] == "reading"
    assert merged.slots["schedule"] == "daily"


def test_goal_answer_supplies_objective() -> None:
    pending = _pending("create_goal", {"title": ""})

    merged = merge_answer(pending, "lose weight", now=NOW)

    assert merged.band == "high"
    assert merged.is_executable
    assert merged.slots["title"] == "lose weight"


def test_ambiguous_reminder_answer_stays_medium() -> None:
    # "at 8" has no am/pm; the time cannot be resolved, so we must ask again
    # rather than invent one.
    pending = _pending("create_reminder", {"title": "stretch"})

    merged = merge_answer(pending, "at 8", now=NOW)

    assert merged.band == "medium"
    assert not merged.is_executable
    assert "scheduled_for" not in merged.slots


def test_reminder_recurrence_survives_time_only_answer() -> None:
    # A recurrence resolved on an earlier turn must not be clobbered when the
    # answer only supplies the time.
    pending = _pending(
        "create_reminder", {"title": "drink water", "recurrence": "daily"}
    )

    merged = merge_answer(pending, "tomorrow at 9am", now=NOW)

    assert merged.is_executable
    assert merged.slots["scheduled_for"].startswith("2026-08-24T09:00")
    assert merged.slots["recurrence"] == "daily"


def test_clarification_habit_choice_completes_high() -> None:
    merged = merge_answer(_clarify("meditate", "daily"), "make it a habit", now=NOW)

    assert merged.action == "create_habit"
    assert merged.band == "high"
    assert merged.is_executable
    assert merged.slots["title"] == "meditate"
    assert merged.slots["schedule"] == "daily"


def test_clarification_reminder_choice_needs_time() -> None:
    merged = merge_answer(_clarify("meditate", "daily"), "a reminder please", now=NOW)

    assert merged.action == "create_reminder"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.slots["title"] == "meditate"
    assert merged.slots["recurrence"] == "daily"
    assert "scheduled_for" not in merged.slots


def test_clarification_unreadable_answer_stays_low() -> None:
    merged = merge_answer(_clarify("meditate", "daily"), "not sure", now=NOW)

    assert merged.action == "none"
    assert merged.band == "low"
    assert "candidates" in merged.slots
