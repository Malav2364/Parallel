"""Turn a ``/process`` outcome into a short, human-readable reply -- LLM-free.

Every ``/process`` response is a structured dict. The confirm/clarify branches
already carry a human ``prompt``, but the executed outcomes (``new_intent``,
``context_only``, ``existing_project``, ``multi_intent``) do not.
:func:`with_message` composes one warm, first-person sentence for each and
attaches it under a single ``message`` key, so the caller always has one field
to show the user.

Deterministic and pure: dates are formatted by hand (no humanize/babel dep, and
no ``%-I``/``%-d`` flags -- those are glibc-only and this host is Windows), and
``now`` is injectable so the relative phrasing ("tomorrow") stays testable.

The composer runs in-process, before serialization: ``decision`` and
``activity`` are Pydantic instances (attribute access) and ``execution`` is a
plain dict. Each may be absent, so every read is guarded.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

_RECURRENCE_PHRASE = {
    "daily": "every day",
    "weekly": "every week",
    "monthly": "every month",
}

_FAILURE_VERB = {
    "create_reminder": "set that reminder",
    "create_goal": "save that goal",
    "create_habit": "add that habit",
    "create_project": "create that project",
}


def with_message(response: dict, now: datetime | None = None) -> dict:
    """Attach a warm-assistant ``message`` to a ``/process`` response dict."""

    if now is None:
        now = datetime.now(IST)

    response["message"] = _compose(response, now)
    return response


def _compose(response: dict, now: datetime) -> str:
    # Confirm/clarify turns already phrased the question -- echo it verbatim.
    prompt = response.get("prompt")
    if prompt:
        return prompt

    rtype = response.get("type")
    decision = response.get("decision")
    execution = response.get("execution") or {}
    activity = response.get("activity")

    if rtype == "new_intent":
        return _success_sentence(decision, execution, now)

    if rtype == "multi_intent":
        base = _success_sentence(decision, execution, now)
        return f"{base} I've also updated your project."

    if rtype == "existing_project":
        if activity is not None and getattr(activity, "current_focus", None):
            return "Got it — I've updated what you're working on."
        return "Got it — I've updated that project."

    if rtype == "context_only":
        return _context_only_sentence(decision, execution)

    return "Got it."


def _success_sentence(decision, execution: dict, now: datetime) -> str:
    action = getattr(decision, "action", None)

    if action == "create_reminder":
        title = _reminder_title(decision, execution)
        iso = execution.get("scheduled_for") or getattr(
            decision, "reminder_scheduled_for", None
        )
        when = _format_when(iso, getattr(decision, "reminder_recurrence", None), now)
        if title and when:
            return f"Done — I'll remind you to {title} {when}."
        if title:
            return f"Done — I'll remind you to {title}."
        return "Done — I've set that reminder."

    if action == "create_goal":
        name = _goal_name(decision, execution)
        target = _format_date(getattr(decision, "goal_target_date", None), now)
        if name and target:
            return f"Done — I've set your goal to {name} by {target}."
        if name:
            return f"Done — I've set your goal to {name}."
        return "Done — I've set that goal."

    if action == "create_habit":
        name = _habit_name(decision, execution)
        schedule = _recurrence_phrase(getattr(decision, "habit_schedule", None))
        window = _time_window_phrase(getattr(decision, "habit_time_window", None))
        if name:
            body = " ".join(part for part in (name, schedule, window) if part)
            return f"Great — I'll help you {body}."
        return "Great — I'll help you build that habit."

    if action == "create_project":
        name = _project_name(decision, execution)
        if name:
            return f"Done — I've created the project {name}."
        return "Done — I've created that project."

    return "Done — that's taken care of."


def _context_only_sentence(decision, execution: dict) -> str:
    reason = execution.get("reason") or ""
    action = execution.get("action") or getattr(decision, "action", None) or "none"

    # No entity was attempted (a pure context update), so nothing failed.
    if action == "none" or not reason:
        return "Got it — I've noted that."

    if "already exists" in reason.lower():
        return _already_exists_sentence(action, decision, execution)

    # A real failure. Stay friendly and never surface the raw reason.
    verb = _FAILURE_VERB.get(action, "do that")
    return f"Sorry — I couldn't {verb} just now. Mind trying again?"


def _already_exists_sentence(action: str, decision, execution: dict) -> str:
    if action == "create_reminder":
        title = _reminder_title(decision, execution)
        if title:
            return f"You already have a reminder to {title}."
        return "You already have that reminder."
    if action == "create_goal":
        return "You're already tracking that goal."
    if action == "create_habit":
        return "You already have that habit going."
    if action == "create_project":
        return "You already have that project."
    return "You already have that."


# --------------------------------------------------------------------------
# Pure formatters
# --------------------------------------------------------------------------


def _parse_iso(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _clock(dt: datetime) -> str:
    """12-hour clock, built by hand (no ``%-I`` -- unsupported on Windows)."""

    hour = dt.hour % 12 or 12
    suffix = "AM" if dt.hour < 12 else "PM"
    if dt.minute:
        return f"{hour}:{dt.minute:02d} {suffix}"
    return f"{hour} {suffix}"


def _recurrence_phrase(recurrence) -> str:
    if not recurrence:
        return ""
    return _RECURRENCE_PHRASE.get(recurrence.lower(), "")


def _relative_day(dt: datetime, now: datetime) -> str:
    delta = (dt.date() - now.date()).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    if 2 <= delta <= 6:
        return f"on {dt.strftime('%A')}"
    month = dt.strftime("%b")
    if dt.year != now.year:
        return f"on {month} {dt.day}, {dt.year}"
    return f"on {month} {dt.day}"


def _format_when(iso, recurrence, now: datetime) -> str:
    """A reminder's timing phrase: recurring cadence or a relative one-off."""

    recurrence_phrase = _recurrence_phrase(recurrence)
    dt = _parse_iso(iso)
    if dt is None:
        return recurrence_phrase
    clock = _clock(dt)
    if recurrence_phrase:
        return f"{recurrence_phrase} at {clock}"
    return f"{_relative_day(dt, now)} at {clock}"


def _format_date(iso_date, now: datetime) -> str:
    """A goal deadline: "Dec 1" (add the year only when it differs from now)."""

    if not iso_date:
        return ""
    try:
        target = date.fromisoformat(iso_date)
    except (ValueError, TypeError):
        parsed = _parse_iso(iso_date)
        if parsed is None:
            return ""
        target = parsed.date()
    month = target.strftime("%b")
    if target.year != now.year:
        return f"{month} {target.day}, {target.year}"
    return f"{month} {target.day}"


def _time_window_phrase(time_window) -> str:
    if not time_window:
        return ""
    window = time_window.strip()
    lowered = window.lower()
    if lowered in {"morning", "afternoon", "evening", "night"}:
        return f"in the {lowered}"
    if lowered in {"noon", "midnight"}:
        return f"at {lowered}"
    return f"at {window}"


# --------------------------------------------------------------------------
# Entity naming: prefer the decision (always set on the fast path), fall back
# to the created entity dict the executor nests under its action key.
# --------------------------------------------------------------------------


def _entity_field(execution: dict, key: str, field: str) -> str:
    entity = (execution or {}).get(key)
    if isinstance(entity, dict):
        return (entity.get(field) or "").strip()
    return ""


def _reminder_title(decision, execution: dict) -> str:
    title = (getattr(decision, "reminder_title", None) or "").strip()
    return title or _entity_field(execution, "reminder", "title")


def _goal_name(decision, execution: dict) -> str:
    name = (getattr(decision, "goal_name", None) or "").strip()
    return name or _entity_field(execution, "goal", "name")


def _habit_name(decision, execution: dict) -> str:
    name = (getattr(decision, "habit_name", None) or "").strip()
    return name or _entity_field(execution, "habit", "name")


def _project_name(decision, execution: dict) -> str:
    name = (getattr(decision, "project_name", None) or "").strip()
    return name or _entity_field(execution, "project", "name")
