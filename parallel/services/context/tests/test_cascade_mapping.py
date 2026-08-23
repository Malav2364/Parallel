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
