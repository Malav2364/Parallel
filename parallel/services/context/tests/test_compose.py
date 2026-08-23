"""with_message composes a warm, deterministic reply for each /process outcome.

Anchored to a fixed clock (Sunday 2026-08-23 10:00 IST) so relative phrasing
("tomorrow", weekday names) resolves to stable, assertable text. Fixtures mirror
the runtime types the endpoint passes: a real ``ContextDecision`` instance, a
plain ``execution`` dict, and a ``ProjectActivity`` for the matched-project path.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.nlu.compose import with_message
from app.schemas.decision import ContextDecision
from app.schemas.project_activity import ProjectActivity

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 8, 23, 10, 0, tzinfo=IST)


def _decision(action: str, **fields) -> ContextDecision:
    return ContextDecision(action=action, reason="test", **fields)


def _message(**response) -> str:
    response.setdefault("prompt", None)
    return with_message(response, now=NOW)["message"]


# --------------------------------------------------------------------------
# Reminder success -- relative one-off and recurring cadence
# --------------------------------------------------------------------------


def test_reminder_one_off_reads_relative_day_and_12h_time() -> None:
    message = _message(
        type="new_intent",
        decision=_decision("create_reminder", reminder_title="submit report"),
        execution={
            "executed": True,
            "action": "create_reminder",
            "scheduled_for": "2026-08-24T17:00:00+05:30",
        },
    )

    assert message == "Done — I'll remind you to submit report tomorrow at 5 PM."


def test_reminder_recurring_states_the_cadence() -> None:
    message = _message(
        type="new_intent",
        decision=_decision(
            "create_reminder",
            reminder_title="take medicine",
            reminder_recurrence="daily",
        ),
        execution={
            "executed": True,
            "action": "create_reminder",
            "scheduled_for": "2026-08-24T09:00:00+05:30",
        },
    )

    assert "every day at 9 AM" in message
    assert "take medicine" in message


def test_reminder_today_and_weekday_and_far_date() -> None:
    def _for(iso: str) -> str:
        return _message(
            type="new_intent",
            decision=_decision("create_reminder", reminder_title="stretch"),
            execution={"executed": True, "scheduled_for": iso},
        )

    assert "today at 8 PM" in _for("2026-08-23T20:00:00+05:30")
    # 2026-08-26 is a Wednesday (3 days out -> named, not "tomorrow").
    assert "on Wednesday at 3 PM" in _for("2026-08-26T15:00:00+05:30")
    # 13 days out, same year -> month + day.
    assert "on Sep 5 at 5 PM" in _for("2026-09-05T17:00:00+05:30")
    # Different year -> the year is spelled out.
    assert "on Jan 2, 2027 at 10 AM" in _for("2027-01-02T10:00:00+05:30")


def test_reminder_falls_back_to_decision_scheduled_for() -> None:
    # The LLM path leaves scheduled_for on the decision, not the execution dict.
    message = _message(
        type="new_intent",
        decision=_decision(
            "create_reminder",
            reminder_title="call the dentist",
            reminder_scheduled_for="2026-08-24T15:00:00+05:30",
        ),
        execution={"executed": True, "action": "create_reminder"},
    )

    assert message == "Done — I'll remind you to call the dentist tomorrow at 3 PM."


# --------------------------------------------------------------------------
# Goal / habit / project success
# --------------------------------------------------------------------------


def test_goal_with_and_without_deadline() -> None:
    with_deadline = _message(
        type="new_intent",
        decision=_decision(
            "create_goal", goal_name="lose weight", goal_target_date="2026-12-01"
        ),
        execution={"executed": True, "action": "create_goal"},
    )
    assert with_deadline == "Done — I've set your goal to lose weight by Dec 1."

    without = _message(
        type="new_intent",
        decision=_decision("create_goal", goal_name="lose weight"),
        execution={"executed": True, "action": "create_goal"},
    )
    assert without == "Done — I've set your goal to lose weight."


def test_habit_with_and_without_time_window() -> None:
    plain = _message(
        type="new_intent",
        decision=_decision(
            "create_habit", habit_name="meditate", habit_schedule="daily"
        ),
        execution={"executed": True, "action": "create_habit"},
    )
    assert plain == "Great — I'll help you meditate every day."

    windowed = _message(
        type="new_intent",
        decision=_decision(
            "create_habit",
            habit_name="meditate",
            habit_schedule="daily",
            habit_time_window="morning",
        ),
        execution={"executed": True, "action": "create_habit"},
    )
    assert windowed == "Great — I'll help you meditate every day in the morning."


def test_project_success_names_the_project() -> None:
    message = _message(
        type="new_intent",
        decision=_decision("create_project", project_name="website redesign"),
        execution={"executed": True, "action": "create_project"},
    )

    assert message == "Done — I've created the project website redesign."


# --------------------------------------------------------------------------
# context_only -- pure update, "already exists", and soft failure
# --------------------------------------------------------------------------


def test_pure_context_update_is_acknowledged() -> None:
    message = _message(
        type="context_only",
        decision=_decision("none"),
        execution={"executed": False, "action": "none"},
    )

    assert message == "Got it — I've noted that."


def test_already_exists_is_friendly_per_entity() -> None:
    reminder = _message(
        type="context_only",
        decision=_decision("create_reminder", reminder_title="submit report"),
        execution={
            "executed": False,
            "action": "create_reminder",
            "reason": "Reminder already exists.",
        },
    )
    assert reminder == "You already have a reminder to submit report."

    goal = _message(
        type="context_only",
        decision=_decision("create_goal", goal_name="lose weight"),
        execution={
            "executed": False,
            "action": "create_goal",
            "reason": "Goal already exists.",
        },
    )
    assert goal == "You're already tracking that goal."

    habit = _message(
        type="context_only",
        decision=_decision("create_habit", habit_name="meditate"),
        execution={
            "executed": False,
            "action": "create_habit",
            "reason": "Habit already exists.",
        },
    )
    assert habit == "You already have that habit going."


def test_failure_stays_soft_and_hides_the_raw_reason() -> None:
    message = _message(
        type="context_only",
        decision=_decision("create_reminder", reminder_title="stretch"),
        execution={
            "executed": False,
            "action": "create_reminder",
            "reason": "Resolved reminder time is in the past.",
        },
    )

    assert (
        message == "Sorry — I couldn't set that reminder just now. Mind trying again?"
    )
    # The internal reason must never leak to the user.
    assert "past" not in message.lower()


# --------------------------------------------------------------------------
# Confirm / clarify echo, matched-project, multi-intent, fallback
# --------------------------------------------------------------------------


def test_confirmation_and_clarification_echo_the_prompt() -> None:
    confirm = with_message(
        {"type": "needs_confirmation", "prompt": "When should I remind you to X?"},
        now=NOW,
    )
    assert confirm["message"] == "When should I remind you to X?"

    clarify = with_message(
        {"type": "needs_clarification", "prompt": "A habit, or a reminder?"},
        now=NOW,
    )
    assert clarify["message"] == "A habit, or a reminder?"


def test_existing_project_stays_generic_with_no_uuid_leak() -> None:
    focused = _message(
        type="existing_project",
        activity=ProjectActivity(current_focus="the redesign", confidence=1.0),
    )
    assert focused == "Got it — I've updated what you're working on."

    unfocused = _message(
        type="existing_project",
        activity=ProjectActivity(confidence=1.0),
    )
    assert unfocused == "Got it — I've updated that project."


def test_multi_intent_reports_the_action_and_the_project() -> None:
    message = _message(
        type="multi_intent",
        decision=_decision("create_reminder", reminder_title="call mom"),
        execution={
            "executed": True,
            "action": "create_reminder",
            "scheduled_for": "2026-08-24T09:00:00+05:30",
        },
        activity=ProjectActivity(current_focus="launch", confidence=1.0),
    )

    assert "remind you to call mom tomorrow at 9 AM" in message
    assert "also updated your project" in message


def test_unknown_type_gets_a_safe_default() -> None:
    assert _message(type="something_new") == "Got it."
