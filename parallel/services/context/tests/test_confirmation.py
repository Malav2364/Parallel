"""confirmation_prompt builds a targeted question from a MEDIUM proposal.

The prompt is derived from the resolved slots, so each action asks only for
the piece it is actually missing -- no model call.
"""

import pytest

from app.nlu.confirmation import clarification_prompt, confirmation_prompt
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
