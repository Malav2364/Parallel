"""to_decision maps a Tier-1 reminder proposal onto a ContextDecision.

The rules tier resolves the absolute time itself, so the mapped decision
carries reminder_scheduled_for (not date/time expressions) and needs no LLM.
"""

from app.nlu.mapping import to_decision
from app.nlu.schemas import ProposedAction


def test_high_reminder_proposal_maps_to_decision() -> None:
    proposal = ProposedAction(
        action="create_reminder",
        source="rules",
        confidence=0.9,
        slots={
            "title": "Call mom",
            "scheduled_for": "2999-01-01T09:00:00+05:30",
            "recurrence": "daily",
        },
        reason="rule:reminder",
    )

    decision = to_decision(proposal)

    assert decision.action == "create_reminder"
    assert decision.reminder_title == "Call mom"
    assert decision.reminder_scheduled_for == "2999-01-01T09:00:00+05:30"
    assert decision.reminder_recurrence == "daily"
    assert decision.reason == "rule:reminder"
    # date/time expressions stay unset; the executor uses scheduled_for.
    assert decision.reminder_date is None
    assert decision.reminder_time is None


def test_missing_optional_slots_default_to_none() -> None:
    proposal = ProposedAction(
        action="create_reminder",
        source="rules",
        confidence=0.9,
        slots={"title": "Standup"},
    )

    decision = to_decision(proposal)

    assert decision.reminder_title == "Standup"
    assert decision.reminder_scheduled_for is None
    assert decision.reminder_recurrence is None
    # reason falls back when the proposal carries none.
    assert decision.reason == "tier-1 rule"


def test_habit_proposal_maps_to_decision() -> None:
    proposal = ProposedAction(
        action="create_habit",
        source="rules",
        confidence=0.9,
        slots={
            "title": "Meditate",
            "schedule": "daily",
            "time_window": "morning",
        },
        reason="rule:habit",
    )

    decision = to_decision(proposal)

    assert decision.action == "create_habit"
    assert decision.habit_name == "Meditate"
    assert decision.habit_schedule == "daily"
    assert decision.habit_time_window == "morning"
    assert decision.habit_status == "active"
    assert decision.reason == "rule:habit"
    # reminder fields stay unset for a habit proposal.
    assert decision.reminder_title is None


def test_goal_proposal_maps_to_decision() -> None:
    proposal = ProposedAction(
        action="create_goal",
        source="rules",
        confidence=0.88,
        slots={"title": "Lose weight", "target_date": "2026-12-01"},
        reason="rule:goal",
    )

    decision = to_decision(proposal)

    assert decision.action == "create_goal"
    assert decision.goal_name == "Lose weight"
    assert decision.goal_target_date == "2026-12-01"
    assert decision.goal_status == "active"
    assert decision.reason == "rule:goal"
    # reminder fields stay unset for a goal proposal.
    assert decision.reminder_title is None
