from app.nlu.schemas import ProposedAction
from app.schemas.decision import ContextDecision


def to_decision(proposal: ProposedAction) -> ContextDecision:
    """Translate a Tier-1 proposal into a ContextDecision.

    Each action fills its own slice of the decision from the proposal's
    slots; the executor consumes those directly, so no LLM step is needed.
    Reminders carry a pre-resolved absolute ``scheduled_for``.
    """
    slots = proposal.slots
    reason = proposal.reason or "tier-1 rule"

    if proposal.action == "create_goal":
        return ContextDecision(
            action=proposal.action,
            reason=reason,
            goal_name=slots.get("title"),
            goal_target_date=slots.get("target_date"),
        )

    if proposal.action == "create_habit":
        return ContextDecision(
            action=proposal.action,
            reason=reason,
            habit_name=slots.get("title"),
            habit_schedule=slots.get("schedule"),
            habit_time_window=slots.get("time_window"),
        )

    return ContextDecision(
        action=proposal.action,
        reason=reason,
        reminder_title=slots.get("title"),
        reminder_scheduled_for=slots.get("scheduled_for"),
        reminder_recurrence=slots.get("recurrence"),
    )
