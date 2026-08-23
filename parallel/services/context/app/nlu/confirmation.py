"""Turn a MEDIUM Tier-1 proposal into a targeted confirmation question.

When the rules recognise an intent but a required slot is missing, the gate
asks for it rather than inventing it ("never silently wrong"). The question is
built from the resolved slots directly -- pure and LLM-free.
"""

from app.nlu.schemas import ProposedAction


def confirmation_prompt(proposal: ProposedAction) -> str:
    """Build a human-readable question for the slot the proposal is missing."""

    slots = proposal.slots
    title = (slots.get("title") or "").strip()

    if proposal.action == "create_reminder":
        if not slots.get("scheduled_for") and not title:
            return "What should I remind you about, and when?"
        if not slots.get("scheduled_for"):
            return f"When should I remind you to {title}?"
        return "What should I remind you about?"

    if proposal.action == "create_habit":
        if not slots.get("schedule") and not title:
            return "What habit do you want to build, and how often?"
        if not slots.get("schedule"):
            return f"How often do you want to {title}? (daily, weekly, or monthly)"
        return "What habit do you want to build?"

    if proposal.action == "create_goal":
        return "What goal would you like to set?"

    return "Could you give me a bit more detail?"


def clarification_prompt(proposal: ProposedAction) -> str:
    """Build a question that asks the user to disambiguate an ambiguous intent.

    A LOW proposal carries the recovered ``activity`` + ``schedule`` and the
    ``candidates`` it could be; we name them so the user picks rather than the
    system guessing ("never silently wrong").
    """

    slots = proposal.slots
    activity = (slots.get("activity") or "").strip()
    schedule = slots.get("schedule") or "regularly"

    if "candidates" in slots:
        if activity:
            return (
                f'Should I track "{activity}" as a {schedule} habit, '
                "or set a reminder for it?"
            )
        return "Is this a habit you want to build, or a reminder?"

    return "Could you tell me a bit more about what you'd like to do?"
