"""merge_answer fills a pending proposal's missing slot from a reply.

Anchored to the same fixed clock as test_rules (Sunday 2026-08-23 10:00 IST)
so relative phrases in the answer resolve to stable datetimes. A completed
proposal comes back HIGH; an answer that still doesn't resolve stays MEDIUM.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.nlu.rules import _is_affirmative, merge_answer
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


@pytest.mark.parametrize(
    "answer, verdict",
    [
        ("yes", True),
        ("post it", True),
        ("lgtm", True),
        ("no", False),
        ("cancel", False),
        ("don't post it", False),
        # A negative word anywhere overrides an affirmative one in the same reply.
        ("no, go ahead", False),
        # Neither yes nor no -> undecided, so the caller re-asks.
        ("maybe later", None),
        ("hmm", None),
    ],
)
def test_is_affirmative_reads_yes_no(answer: str, verdict: bool | None) -> None:
    assert _is_affirmative(answer) is verdict


def test_github_stage_a_fills_repo_and_stays_medium() -> None:
    # No repo yet: the answer names the target, but a public write still confirms.
    pending = _pending(
        "post_github_comment",
        {"number": 42, "body": "LGTM"},
        reason="rule:github_comment",
    )

    merged = merge_answer(pending, "acme/app#42", now=NOW)

    assert merged.action == "post_github_comment"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.slots["repo"] == "acme/app"
    assert merged.slots["number"] == 42
    assert merged.slots["body"] == "LGTM"
    assert merged.reason == "rule:github_comment"


def test_github_stage_b_yes_confirms_to_high() -> None:
    pending = _pending(
        "post_github_comment",
        {"repo": "acme/app", "number": 42, "body": "LGTM"},
    )

    merged = merge_answer(pending, "yes, post it", now=NOW)

    assert merged.action == "post_github_comment"
    assert merged.band == "high"
    assert merged.is_executable
    assert merged.reason == "post_github_comment confirmed"
    assert merged.slots == {"repo": "acme/app", "number": 42, "body": "LGTM"}


def test_github_stage_b_no_declines_terminally() -> None:
    pending = _pending(
        "post_github_comment",
        {"repo": "acme/app", "number": 42, "body": "LGTM"},
    )

    merged = merge_answer(pending, "no, cancel that", now=NOW)

    assert merged.action == "none"
    assert not merged.is_executable
    assert merged.reason == "post_github_comment declined"
    # Slots survive the decline so the target is still named if we need it.
    assert merged.slots["repo"] == "acme/app"
    assert merged.slots["body"] == "LGTM"


def test_github_stage_b_unreadable_answer_stays_medium() -> None:
    pending = _pending(
        "post_github_comment",
        {"repo": "acme/app", "number": 42, "body": "LGTM"},
        reason="rule:github_comment",
    )

    merged = merge_answer(pending, "maybe later", now=NOW)

    assert merged.action == "post_github_comment"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.reason == "rule:github_comment"


# --- approve & close: same yes/no shape as comment, minus the body gate --------


@pytest.mark.parametrize(
    "action, reason",
    [
        ("approve_github_pr", "rule:github_approve"),
        ("close_github_pr", "rule:github_close"),
    ],
)
def test_github_write_stage_a_fills_repo_and_stays_medium(
    action: str, reason: str
) -> None:
    pending = _pending(action, {"number": 42}, reason=reason)

    merged = merge_answer(pending, "acme/app#42", now=NOW)

    assert merged.action == action
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.slots["repo"] == "acme/app"
    assert merged.slots["number"] == 42
    assert merged.reason == reason


@pytest.mark.parametrize("action", ["approve_github_pr", "close_github_pr"])
def test_github_write_stage_b_yes_confirms_to_high(action: str) -> None:
    pending = _pending(action, {"repo": "acme/app", "number": 42})

    merged = merge_answer(pending, "yes, do it", now=NOW)

    assert merged.action == action
    assert merged.band == "high"
    assert merged.is_executable
    assert merged.reason == f"{action} confirmed"


@pytest.mark.parametrize("action", ["approve_github_pr", "close_github_pr"])
def test_github_write_stage_b_no_declines_terminally(action: str) -> None:
    pending = _pending(action, {"repo": "acme/app", "number": 42})

    merged = merge_answer(pending, "no, cancel that", now=NOW)

    assert merged.action == "none"
    assert not merged.is_executable
    assert merged.reason == f"{action} declined"
    # The target survives the decline for honest messaging.
    assert merged.slots["repo"] == "acme/app"
    assert merged.slots["number"] == 42


# --- merge: the extra-friction state machine (repo -> method -> firm gate) -----


def test_merge_stage_a_fills_repo_then_asks_method() -> None:
    pending = _pending("merge_github_pr", {"number": 42}, reason="rule:github_merge")

    merged = merge_answer(pending, "acme/app#42", now=NOW)

    assert merged.action == "merge_github_pr"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.slots["repo"] == "acme/app"
    # Repo is known but the method is not, so we cannot fire yet.
    assert "method" not in merged.slots


def test_merge_method_pick_sets_method_and_stays_medium() -> None:
    pending = _pending(
        "merge_github_pr",
        {"repo": "acme/app", "number": 42},
        reason="rule:github_merge",
    )

    merged = merge_answer(pending, "squash", now=NOW)

    assert merged.action == "merge_github_pr"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.slots["method"] == "squash"


@pytest.mark.parametrize("answer", ["42", "merge it"])
def test_merge_firm_gate_confirms_to_high(answer: str) -> None:
    # With a method chosen, naming the PR number (or the word "merge") fires.
    pending = _pending(
        "merge_github_pr",
        {"repo": "acme/app", "number": 42, "method": "squash"},
        reason="rule:github_merge",
    )

    merged = merge_answer(pending, answer, now=NOW)

    assert merged.action == "merge_github_pr"
    assert merged.band == "high"
    assert merged.is_executable
    assert merged.reason == "merge_github_pr confirmed"


def test_merge_bare_yes_does_not_pass_firm_gate() -> None:
    # A bare "yes" is deliberately not enough to land code on the base branch.
    pending = _pending(
        "merge_github_pr",
        {"repo": "acme/app", "number": 42, "method": "squash"},
        reason="rule:github_merge",
    )

    merged = merge_answer(pending, "yes", now=NOW)

    assert merged.action == "merge_github_pr"
    assert merged.band == "medium"
    assert not merged.is_executable
    assert merged.reason == "rule:github_merge"


def test_merge_negative_declines_despite_naming_number() -> None:
    # "no, don't merge 42" contains both "merge" and "42", but the negative wins
    # -- the decline check runs before the firm gate.
    pending = _pending(
        "merge_github_pr",
        {"repo": "acme/app", "number": 42, "method": "squash"},
        reason="rule:github_merge",
    )

    merged = merge_answer(pending, "no, don't merge 42", now=NOW)

    assert merged.action == "none"
    assert not merged.is_executable
    assert merged.reason == "merge_github_pr declined"
    assert merged.slots["repo"] == "acme/app"
