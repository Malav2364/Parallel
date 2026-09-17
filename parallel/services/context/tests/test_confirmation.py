"""confirmation_prompt builds a targeted question from a MEDIUM proposal.

The prompt is derived from the resolved slots, so each action asks only for
the piece it is actually missing -- no model call.
"""

import pytest

from app.nlu.confirmation import (
    answer_candidates,
    clarification_prompt,
    confirmation_prompt,
)
from app.nlu.schemas import ProposedAction


def _medium(action: str, slots: dict) -> ProposedAction:
    return ProposedAction(
        action=action,
        source="rules",
        confidence=0.5,
        slots=slots,
        reason="test",
    )


def _low(slots: dict) -> ProposedAction:
    return ProposedAction(
        action="none",
        source="rules",
        confidence=0.3,
        slots=slots,
        reason="ambiguous",
    )


@pytest.mark.parametrize(
    "action, slots, needle",
    [
        ("create_reminder", {"title": "submit report"}, "when should i remind"),
        (
            "create_reminder",
            {"title": "", "scheduled_for": "2999-01-01T09:00:00+05:30"},
            "what should i remind",
        ),
        ("create_reminder", {"title": ""}, "and when"),
        ("create_habit", {"title": "read"}, "how often"),
        ("create_habit", {"title": ""}, "how often"),
        ("create_goal", {"title": ""}, "what goal"),
    ],
)
def test_prompt_targets_the_missing_slot(action: str, slots: dict, needle: str) -> None:
    prompt = confirmation_prompt(_medium(action, slots))

    assert needle in prompt.lower()


def test_reminder_prompt_names_the_recovered_title() -> None:
    prompt = confirmation_prompt(_medium("create_reminder", {"title": "submit report"}))

    assert "submit report" in prompt


def test_clarification_offers_both_categories_and_names_the_activity() -> None:
    prompt = clarification_prompt(
        _low(
            {
                "activity": "meditate",
                "schedule": "daily",
                "candidates": ["create_habit", "create_reminder"],
            }
        )
    )

    lowered = prompt.lower()
    assert "meditate" in prompt
    assert "habit" in lowered
    assert "reminder" in lowered
    assert "daily" in lowered


@pytest.mark.parametrize(
    "action, slots, needle",
    [
        # Repo unknown -> the shared "which repo?" line, for every write action.
        ("approve_github_pr", {"number": 42}, "which repo is pr #42"),
        ("merge_github_pr", {"number": 42}, "which repo is pr #42"),
        ("close_github_pr", {"number": 42}, "which repo is pr #42"),
        # Repo known: each action asks its own confirm.
        (
            "approve_github_pr",
            {"repo": "acme/app", "number": 42},
            "approve acme/app #42?",
        ),
        ("close_github_pr", {"repo": "acme/app", "number": 42}, "close acme/app #42?"),
        # Merge with no method yet offers the three methods.
        (
            "merge_github_pr",
            {"repo": "acme/app", "number": 42},
            "how should i merge acme/app #42",
        ),
    ],
)
def test_github_write_prompts_target_the_missing_piece(
    action: str, slots: dict, needle: str
) -> None:
    assert needle in confirmation_prompt(_medium(action, slots)).lower()


def test_approve_prompt_includes_the_review_body() -> None:
    prompt = confirmation_prompt(
        _medium(
            "approve_github_pr",
            {"repo": "acme/app", "number": 42, "body": "nice work"},
        )
    )

    assert "nice work" in prompt


def test_merge_firm_prompt_names_operation_and_asks_for_number() -> None:
    prompt = confirmation_prompt(
        _medium(
            "merge_github_pr",
            {"repo": "acme/app", "number": 42, "method": "squash"},
        )
    )

    # Firm gate: names the fully-specified op and asks the user to type the number.
    assert "Squash-merge acme/app #42?" in prompt
    assert "reply with the PR number (42)" in prompt


def test_merge_plain_method_says_merge_not_merge_merge() -> None:
    prompt = confirmation_prompt(
        _medium(
            "merge_github_pr",
            {"repo": "acme/app", "number": 42, "method": "merge"},
        )
    )

    assert "Merge acme/app #42?" in prompt
    assert "Merge-merge" not in prompt


@pytest.mark.parametrize(
    "action, slots, expected",
    [
        # Slot-fill confirmations are free-text, not yes/no -- no chips.
        ("create_reminder", {"title": "submit report"}, []),
        ("create_habit", {"title": "read"}, []),
        ("create_goal", {"title": ""}, []),
        # GitHub yes/no writes, repo known -> a tappable Yes / No.
        (
            "post_github_comment",
            {"repo": "acme/app", "number": 42, "body": "hi"},
            ["Yes", "No"],
        ),
        ("approve_github_pr", {"repo": "acme/app", "number": 42}, ["Yes", "No"]),
        ("close_github_pr", {"repo": "acme/app", "number": 42}, ["Yes", "No"]),
        # Repo still unknown -> Stage A needs a free-text "acme/app" answer.
        ("post_github_comment", {"number": 42}, []),
        ("approve_github_pr", {"number": 42}, []),
        ("close_github_pr", {"number": 42}, []),
        # Merge: pick a method, then confirm by typing the PR number.
        (
            "merge_github_pr",
            {"repo": "acme/app", "number": 42},
            ["merge", "squash", "rebase"],
        ),
        (
            "merge_github_pr",
            {"repo": "acme/app", "number": 42, "method": "squash"},
            ["42", "Cancel"],
        ),
        # No repo, or a method but no number yet -> free text, no chips.
        ("merge_github_pr", {"number": 42}, []),
        ("merge_github_pr", {"repo": "acme/app", "method": "squash"}, []),
    ],
)
def test_answer_candidates_returns_tappable_labels(
    action: str, slots: dict, expected: list[str]
) -> None:
    assert answer_candidates(_medium(action, slots)) == expected


def test_clarification_candidates_are_display_labels() -> None:
    # Stored candidates are internal action names; the chips must be the display
    # words the choice parser reads ("Habit"/"Reminder"), not "create_habit".
    labels = answer_candidates(
        _low(
            {
                "activity": "meditate",
                "schedule": "daily",
                "candidates": ["create_habit", "create_reminder"],
            }
        )
    )

    assert labels == ["Habit", "Reminder"]
