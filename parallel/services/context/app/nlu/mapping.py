from app.nlu.schemas import ProposedAction
from app.schemas.decision import ContextDecision


def to_decision(proposal: ProposedAction) -> ContextDecision:
    """Translate a Tier-1 reminder proposal into a ContextDecision.

    The rules tier only emits ``create_reminder``, carrying a pre-resolved
    absolute ``scheduled_for`` in its slots; the executor consumes that
    directly, so no LLM decision step is needed.
    """
    slots = proposal.slots

    return ContextDecision(
        action=proposal.action,
        reason=proposal.reason or "tier-1 rule",
        reminder_title=slots.get("title"),
        reminder_scheduled_for=slots.get("scheduled_for"),
        reminder_recurrence=slots.get("recurrence"),
    )
