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

    if proposal.action == "post_github_comment":
        number = slots.get("number")
        repo = slots.get("repo")
        if not repo:
            return f"Which repo is PR #{number} in? Tell me like acme/app#{number}."
        body = slots.get("body") or ""
        return f'Post this comment on {repo} #{number}?\n\n"{body}"'

    if proposal.action == "approve_github_pr":
        number = slots.get("number")
        repo = slots.get("repo")
        if not repo:
            return f"Which repo is PR #{number} in? Tell me like acme/app#{number}."
        body = (slots.get("body") or "").strip()
        if body:
            return f'Approve {repo} #{number} with this comment?\n\n"{body}"'
        return f"Approve {repo} #{number}?"

    if proposal.action == "merge_github_pr":
        number = slots.get("number")
        repo = slots.get("repo")
        if not repo:
            return f"Which repo is PR #{number} in? Tell me like acme/app#{number}."
        method = slots.get("method")
        if not method:
            return f"How should I merge {repo} #{number} — merge, squash, or rebase?"
        verb = "Merge" if method == "merge" else f"{method.capitalize()}-merge"
        return (
            f"{verb} {repo} #{number}? This lands code on the base branch — "
            f"reply with the PR number ({number}) to confirm."
        )

    if proposal.action == "close_github_pr":
        number = slots.get("number")
        repo = slots.get("repo")
        if not repo:
            return f"Which repo is PR #{number} in? Tell me like acme/app#{number}."
        return f"Close {repo} #{number}?"

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


# GitHub writes that read a plain yes/no once the repo is known.
_GITHUB_YES_NO_ACTIONS = (
    "post_github_comment",
    "approve_github_pr",
    "close_github_pr",
)


def answer_candidates(proposal: ProposedAction) -> list[str]:
    """One-tap chip labels for the confirm/clarify question, or ``[]``.

    The chat renders a tap chip per label and sends the label verbatim as the
    next answer, so every label here must parse back through the same offline
    grammar the confirmation loop uses (``rules.py``). Confirmations that are
    really slot-fills (a reminder time, a habit schedule, a goal) return ``[]``
    so the user types instead of tapping a nonsensical fixed choice; a github
    write with no repo yet does the same (Stage A needs a free-text repo).
    """

    slots = proposal.slots

    # Clarification: habit vs reminder. The stored candidates are the internal
    # action names ("create_habit"); relabel to the display words the choice
    # parser actually reads (``\bhabit\b`` fails inside "create_habit").
    if proposal.action == "none" and "candidates" in slots:
        return ["Habit", "Reminder"]

    if proposal.action == "merge_github_pr":
        if not slots.get("repo"):
            return []
        if not slots.get("method"):
            return ["merge", "squash", "rebase"]
        number = slots.get("number")
        if number is None:
            return []
        # Merge's firm gate: naming the PR number confirms, "Cancel" declines.
        return [str(number), "Cancel"]

    if proposal.action in _GITHUB_YES_NO_ACTIONS:
        if not slots.get("repo"):
            return []
        return ["Yes", "No"]

    # reminder / habit / goal confirmations are slot-fills, not yes/no; the
    # answer is free text, so no chip.
    return []
