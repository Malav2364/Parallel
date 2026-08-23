"""Tier-1 intent rules: deterministic reminder proposals, no model call.

Anchored to a fixed clock (Sunday 2026-08-23 10:00 IST) so relative phrases
resolve to stable, assertable datetimes.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.nlu.rules import propose

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 8, 23, 10, 0, tzinfo=IST)


def _ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


@pytest.mark.parametrize(
    "text, title, when, recurrence",
    [
        (
            "remind me to take medicine every day at 9am",
            "take medicine",
            _ist(2026, 8, 24, 9, 0),
            "daily",
        ),
        (
            "don't forget to pay rent monthly on the 1st",
            "pay rent",
            _ist(2026, 9, 1, 0, 0),
            "monthly",
        ),
        (
            "reminder: team standup tomorrow at 9am",
            "team standup",
            _ist(2026, 8, 24, 9, 0),
            None,
        ),
        (
            "remind me to call the dentist tomorrow at 3pm",
            "call the dentist",
            _ist(2026, 8, 24, 15, 0),
            None,
        ),
    ],
)
def test_high_confidence_reminder(
    text: str, title: str, when: datetime, recurrence: str | None
) -> None:
    proposal = propose(text, now=NOW)

    assert proposal is not None
    assert proposal.action == "create_reminder"
    assert proposal.band == "high"
    assert proposal.is_executable
    assert proposal.slots["title"] == title
    assert proposal.slots["scheduled_for"] == when.isoformat()
    assert proposal.slots["recurrence"] == recurrence


def test_interior_stopwords_are_kept_in_title() -> None:
    proposal = propose("remind me to call the dentist tomorrow at 3pm", now=NOW)

    assert proposal is not None
    assert proposal.slots["title"] == "call the dentist"


def test_missing_time_defers_at_medium() -> None:
    proposal = propose("remind me to submit report", now=NOW)

    assert proposal is not None
    assert proposal.band == "medium"
    assert not proposal.is_executable
    assert proposal.slots["title"] == "submit report"
    assert "scheduled_for" not in proposal.slots


def test_recurrence_preserved_when_time_missing() -> None:
    proposal = propose("remind me to drink water every day", now=NOW)

    assert proposal is not None
    assert proposal.band == "medium"
    assert proposal.slots["title"] == "drink water"
    assert proposal.slots["recurrence"] == "daily"
    assert "scheduled_for" not in proposal.slots


def test_ambiguous_bare_hour_defers() -> None:
    # "at 8" has no am/pm; the time cannot be resolved, so it must not execute.
    proposal = propose("ping me to stretch at 8", now=NOW)

    assert proposal is not None
    assert proposal.band == "medium"
    assert proposal.slots["title"] == "stretch"


def test_subjectless_reminder_defers() -> None:
    proposal = propose("remind me on the 5th at 8pm", now=NOW)

    assert proposal is not None
    assert proposal.band == "medium"
    assert proposal.slots["title"] == ""
    assert proposal.slots["scheduled_for"] == _ist(2026, 9, 5, 20, 0).isoformat()


@pytest.mark.parametrize(
    "text, name, schedule",
    [
        ("start a habit of meditating every day", "meditating", "daily"),
        ("build a daily habit of journaling", "journaling", "daily"),
        (
            "make it a weekly routine to review my goals",
            "review my goals",
            "weekly",
        ),
    ],
)
def test_high_confidence_habit(text: str, name: str, schedule: str) -> None:
    proposal = propose(text, now=NOW)

    assert proposal is not None
    assert proposal.action == "create_habit"
    assert proposal.band == "high"
    assert proposal.is_executable
    assert proposal.slots["title"] == name
    assert proposal.slots["schedule"] == schedule


def test_habit_missing_schedule_defers() -> None:
    # The explicit word "habit" is present but no recurrence resolves, so the
    # schedule the executor needs is missing: defer rather than invent it.
    proposal = propose("i want to build a habit of reading", now=NOW)

    assert proposal is not None
    assert proposal.action == "create_habit"
    assert proposal.band == "medium"
    assert not proposal.is_executable
    assert proposal.slots["title"] == "reading"
    assert "schedule" not in proposal.slots


@pytest.mark.parametrize(
    "text, name",
    [
        ("my goal is to lose weight", "lose weight"),
        ("i want to achieve financial independence", "financial independence"),
        ("set a goal to read 20 books", "read 20 books"),
    ],
)
def test_high_confidence_goal(text: str, name: str) -> None:
    proposal = propose(text, now=NOW)

    assert proposal is not None
    assert proposal.action == "create_goal"
    assert proposal.band == "high"
    assert proposal.is_executable
    assert proposal.slots["title"] == name


def test_goal_deadline_populates_target_date() -> None:
    proposal = propose("my goal is to launch the app by december", now=NOW)

    assert proposal is not None
    assert proposal.action == "create_goal"
    assert proposal.is_executable
    assert proposal.slots["title"] == "launch the app"
    # "december" resolves against the fixed 2026-08-23 clock, future-preferred.
    assert proposal.slots["target_date"].startswith("2026-12")


@pytest.mark.parametrize(
    "text",
    [
        "create a project for the website redesign",
        "i want to lose weight",
        "how is my week looking",
    ],
)
def test_non_reminder_is_declined(text: str) -> None:
    assert propose(text, now=NOW) is None
