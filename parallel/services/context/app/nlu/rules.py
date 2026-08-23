"""Tier-1 deterministic intent rules.

Maps a raw utterance straight to a :class:`ProposedAction` using keyword
triggers and the offline date grammar -- no model call. This is the fast
path that handles the common, unambiguous cases ("remind me to call mom
tomorrow at 6pm") in microseconds. Anything it cannot resolve confidently
it declines (returns ``None``) so the cascade can escalate to a later tier.
"""

import re

from app.nlu.datetime_grammar import detect_recurrence, parse_schedule, split_time
from app.nlu.schemas import MEDIUM_CONFIDENCE, ProposedAction

# Phrases that clearly signal "set me a reminder".
_REMINDER_TRIGGER = re.compile(
    r"\b(remind|reminder|remember to|don'?t forget|ping me|alert me|wake me)\b",
    re.IGNORECASE,
)

# Leading trigger/filler removed to recover the reminder subject.
_TRIGGER_PREFIX = re.compile(
    r"^\s*(please\s+)?"
    r"(remind\s+me\s+(to|that|about)?|reminder\s*(to|:)?|remember\s+to|"
    r"don'?t\s+forget\s+(to)?|ping\s+me\s+(to|about)?|alert\s+me\s+(to|about)?|"
    r"wake\s+me\s*(up)?)\s*",
    re.IGNORECASE,
)

# Connective/filler words trimmed from the ends of a recovered title.
_EDGE_STOPWORDS = {
    "to",
    "that",
    "about",
    "on",
    "at",
    "by",
    "for",
    "the",
    "a",
    "an",
    "of",
    "me",
    "my",
    "please",
}


def _clean_title(subject: str) -> str:
    """Tidy the recovered subject into a reminder title.

    Interior words are kept verbatim ("call the dentist"); only dangling
    connectives at either edge are dropped ("on the" -> "").
    """

    tokens = re.sub(r"\s+", " ", subject).strip(" ,.-:;").split(" ")
    tokens = [t for t in tokens if t]

    while tokens and tokens[0].lower() in _EDGE_STOPWORDS:
        tokens.pop(0)
    while tokens and tokens[-1].lower() in _EDGE_STOPWORDS:
        tokens.pop()

    return " ".join(tokens).strip(" ,.-:;")


def propose_reminder(text, now=None) -> ProposedAction | None:
    """Propose a ``create_reminder`` action, or ``None`` if not a reminder."""

    if not _REMINDER_TRIGGER.search(text):
        return None

    body = _TRIGGER_PREFIX.sub("", text, count=1)
    subject, time_phrase = split_time(body)
    title = _clean_title(subject)

    schedule = parse_schedule(time_phrase, now=now) if time_phrase else None

    # High confidence requires both halves: a subject and a resolved time.
    if schedule is not None and title:
        return ProposedAction(
            action="create_reminder",
            source="rules",
            confidence=min(0.9, schedule.confidence),
            slots={
                "title": title,
                "scheduled_for": schedule.scheduled_for.isoformat(),
                "recurrence": schedule.recurrence,
            },
            reason="rule:reminder",
        )

    # Reminder intent is clear but something is missing (the time, the
    # subject, or both): propose at medium confidence so the cascade can
    # confirm rather than invent the missing piece. Whatever we did resolve
    # is carried through to prefill the confirmation.
    slots: dict = {"title": title}
    if schedule is not None:
        slots["scheduled_for"] = schedule.scheduled_for.isoformat()
        slots["recurrence"] = schedule.recurrence
        missing = "subject"
    else:
        recurrence = detect_recurrence(time_phrase) if time_phrase else None
        if recurrence:
            slots["recurrence"] = recurrence
        missing = "time" if title else "subject and time"

    return ProposedAction(
        action="create_reminder",
        source="rules",
        confidence=MEDIUM_CONFIDENCE,
        slots=slots,
        reason=f"reminder intent, missing {missing}",
    )


# Habit intent must be explicit: the literal word "habit"/"routine".
_HABIT_TRIGGER = re.compile(r"\b(?:habit|routine)\b", re.IGNORECASE)

# The activity is what follows "habit/routine of|to ..." ("habit of reading").
_HABIT_OF = re.compile(r"\b(?:habit|routine)\s+(?:of|to)\s+(.+)$", re.IGNORECASE)

# An optional, best-effort daypart/clock window. Never gates high confidence.
_TIME_WINDOW = re.compile(
    r"\b(morning|afternoon|evening|night|noon|midnight"
    r"|\d{1,2}(?::\d{2})?\s*(?:am|pm)|\d{1,2}:\d{2})\b",
    re.IGNORECASE,
)


def propose_habit(text, now=None) -> ProposedAction | None:
    """Propose a ``create_habit`` action, or ``None`` if not a habit.

    Deliberately conservative: high confidence requires the explicit word
    "habit"/"routine" AND a recognised recurrence AND a recovered activity.
    Intention+recurrence without the word (e.g. "meditate every day", which
    could equally be a recurring reminder) is left for a later tier.
    """

    if not _HABIT_TRIGGER.search(text):
        return None

    recurrence = detect_recurrence(text)
    match = _HABIT_OF.search(text)
    if match:
        subject, _ = split_time(match.group(1))
        name = _clean_title(subject)
    else:
        name = ""

    window = _TIME_WINDOW.search(text)
    time_window = window.group(1) if window else None

    # High confidence needs the explicit word (checked above), a name, and a
    # schedule -- everything the executor requires to create the habit.
    if name and recurrence:
        slots: dict = {"title": name, "schedule": recurrence}
        if time_window:
            slots["time_window"] = time_window
        return ProposedAction(
            action="create_habit",
            source="rules",
            confidence=0.9,
            slots=slots,
            reason="rule:habit",
        )

    # Habit intent is clear but the schedule or the activity is missing:
    # defer at medium so a later tier can confirm rather than invent it.
    # Whatever we did resolve is carried through to prefill the confirmation.
    slots = {"title": name}
    if recurrence:
        slots["schedule"] = recurrence
    if time_window:
        slots["time_window"] = time_window
    if name:
        missing = "schedule"
    else:
        missing = "activity" if recurrence else "activity and schedule"

    return ProposedAction(
        action="create_habit",
        source="rules",
        confidence=MEDIUM_CONFIDENCE,
        slots=slots,
        reason=f"habit intent, missing {missing}",
    )


# Goal intent must be explicit; plain "I want to X" is deliberately NOT a
# trigger (too broad -- it captures reminders, habits, and idle musings alike).
_GOAL_TRIGGER = re.compile(
    r"\b(?:my\s+goal|(?:set|make|create)\s+(?:a|the|my)?\s*goal"
    r"|i\s+want\s+to\s+(?:achieve|accomplish|reach)"
    r"|i\s+aim\s+to|i'?m\s+aiming\s+to|my\s+aim\s+is"
    r"|i\s+aspire\s+to|my\s+objective|my\s+target\s+is"
    r"|i'?m\s+working\s+towards?|goal\s+is|goal\s*:)",
    re.IGNORECASE,
)

# Leading goal framing removed to recover the objective itself.
_GOAL_PREFIX = re.compile(
    r"^\s*(?:please\s+)?"
    r"(?:my\s+goal\s+is(?:\s+to|\s*:)?|my\s+goal\s*:?"
    r"|(?:set|make|create)\s+(?:a|the|my)?\s*goal\s+(?:to|of|:)?"
    r"|i\s+want\s+to\s+(?:achieve|accomplish|reach)"
    r"|i\s+aim\s+to|i'?m\s+aiming\s+to|my\s+aim\s+is(?:\s+to|\s*:)?"
    r"|i\s+aspire\s+to|my\s+objective\s+is(?:\s+to|\s*:)?|my\s+objective\s*:?"
    r"|my\s+target\s+is(?:\s+to|\s*:)?|i'?m\s+working\s+towards?"
    r"|goal\s+is(?:\s+to|\s*:)?|goal\s*:)\s*",
    re.IGNORECASE,
)

# A trailing deadline clause ("by december") -> an optional target_date.
_DEADLINE = re.compile(
    r"\b(?:by|before|until|due(?:\s+by)?)\s+(.+)$",
    re.IGNORECASE,
)


def propose_goal(text, now=None) -> ProposedAction | None:
    """Propose a ``create_goal`` action, or ``None`` if not a goal.

    Conservative by design: only the explicit goal markers above qualify, so
    a bare "I want to X" is left for a later tier rather than auto-created.
    """

    if not _GOAL_TRIGGER.search(text):
        return None

    body = _GOAL_PREFIX.sub("", text, count=1).strip()

    # Peel a "by <date>" clause only when it actually parses to a date;
    # otherwise keep the words in the objective (never silently drop them).
    target_date = None
    deadline = _DEADLINE.search(body)
    if deadline:
        parsed = parse_schedule(deadline.group(1), now=now)
        if parsed is not None:
            target_date = parsed.scheduled_for.date().isoformat()
            body = body[: deadline.start()].strip()

    name = _clean_title(body)

    if name:
        slots: dict = {"title": name}
        if target_date:
            slots["target_date"] = target_date
        return ProposedAction(
            action="create_goal",
            source="rules",
            confidence=0.88,
            slots=slots,
            reason="rule:goal",
        )

    # Goal intent is clear but no objective could be recovered: defer.
    return ProposedAction(
        action="create_goal",
        source="rules",
        confidence=MEDIUM_CONFIDENCE,
        slots={"title": name},
        reason="goal intent, missing objective",
    )


# An explicit intent to *do* something ("i want to ...", "start ...", "let me
# ...") without naming a category. Required so a passive mood statement ("i feel
# tired every day") never triggers a clarification -- only an actionable one does.
_INTENT_PREFIX = re.compile(
    r"^\s*(?:please\s+)?"
    r"(?:i\s+want\s+to|i'?d\s+like\s+to|i\s+wanna|i\s+need\s+to|"
    r"i\s+should|i\s+have\s+to|i\s+gotta|i\s+plan\s+to|i\s+intend\s+to|"
    r"i'?m\s+going\s+to|i\s+will|i'?m\s+trying\s+to|trying\s+to|"
    r"let\s+me|start|begin)\s+",
    re.IGNORECASE,
)


def propose_clarification(text, now=None) -> ProposedAction | None:
    """Propose a LOW clarification when the intent is actionable but its
    category is ambiguous: a recurring activity stated with an explicit intent
    but no reminder/habit/goal marker ("i want to meditate every day" -- a habit
    or a recurring reminder?). Runs last, so the specific proposers claim their
    own cases first. Declines (``None``) unless a recurrence resolves AND an
    intent prefix is present AND an activity is recovered, so the LLM still
    handles genuinely open-ended input rather than being nagged for a category.
    """

    recurrence = detect_recurrence(text)
    if not recurrence:
        return None

    match = _INTENT_PREFIX.match(text)
    if match is None:
        return None

    subject, _ = split_time(text[match.end() :])
    activity = _clean_title(subject)
    if not activity:
        return None

    return ProposedAction(
        action="none",
        source="rules",
        confidence=0.3,
        slots={
            "activity": activity,
            "schedule": recurrence,
            "candidates": ["create_habit", "create_reminder"],
        },
        reason="ambiguous: recurring activity, category unclear",
    )


def propose(text, now=None) -> ProposedAction | None:
    """Run the deterministic rules, returning the first confident match."""

    for proposer in (
        propose_reminder,
        propose_habit,
        propose_goal,
        propose_clarification,
    ):
        proposal = proposer(text, now=now)
        if proposal is not None:
            return proposal

    return None


_HABIT_CHOICE = re.compile(r"\b(?:habit|routine|track|build)\b", re.IGNORECASE)
_REMINDER_CHOICE = re.compile(
    r"\b(?:remind(?:er)?|remember|ping|alert|notif\w*)\b",
    re.IGNORECASE,
)


def _classify_choice(answer: str) -> str | None:
    """Read a habit-vs-reminder pick from a clarification answer, or ``None``."""

    is_habit = bool(_HABIT_CHOICE.search(answer))
    is_reminder = bool(_REMINDER_CHOICE.search(answer))
    if is_habit and not is_reminder:
        return "create_habit"
    if is_reminder and not is_habit:
        return "create_reminder"
    return None


def _resolve_clarification(pending: ProposedAction, answer: str) -> ProposedAction:
    """Turn a habit-vs-reminder pick into a concrete proposal, re-graded.

    Choosing "habit" completes it (HIGH -> execute). Choosing "reminder" still
    needs a first-fire time, so it comes back MEDIUM to run the normal
    confirmation loop. An answer that names neither stays the LOW proposal so
    the caller asks again rather than guessing.
    """

    activity = (pending.slots.get("activity") or "").strip()
    schedule = pending.slots.get("schedule")
    choice = _classify_choice(answer)

    if choice == "create_habit":
        return ProposedAction(
            action="create_habit",
            source="rules",
            confidence=0.9,
            slots={"title": activity, "schedule": schedule},
            reason="clarified: habit",
        )

    if choice == "create_reminder":
        return ProposedAction(
            action="create_reminder",
            source="rules",
            confidence=MEDIUM_CONFIDENCE,
            slots={"title": activity, "recurrence": schedule},
            reason="reminder intent, missing time",
        )

    return pending


def merge_answer(pending: ProposedAction, answer: str, now=None) -> ProposedAction:
    """Fill a pending proposal's missing slot from a free-text answer.

    Given a MEDIUM proposal awaiting confirmation and the user's reply, resolve
    the one piece that was missing (a time, a schedule, or the subject) using
    the same offline grammar the proposers use, then re-grade confidence. If the
    proposal is now complete it comes back HIGH (ready to execute); otherwise it
    stays MEDIUM so the caller can ask again. Deterministic -- no model call.
    """

    slots = dict(pending.slots)
    title = (slots.get("title") or "").strip()

    if pending.action == "none" and "candidates" in slots:
        # A clarification answer picks a category; hand off to build the
        # concrete proposal (which then re-runs this gate on later turns).
        return _resolve_clarification(pending, answer)

    if pending.action == "create_reminder":
        if not slots.get("scheduled_for"):
            parsed = parse_schedule(answer, now=now)
            if parsed is not None:
                slots["scheduled_for"] = parsed.scheduled_for.isoformat()
                # Keep a recurrence resolved on an earlier turn; only a fresh
                # recurrence named in the answer should replace it.
                if parsed.recurrence is not None or "recurrence" not in slots:
                    slots["recurrence"] = parsed.recurrence
        elif not title:
            slots["title"] = _clean_title(answer)
        ready = bool(slots.get("title") and slots.get("scheduled_for"))
        confidence = 0.9 if ready else MEDIUM_CONFIDENCE

    elif pending.action == "create_habit":
        if not slots.get("schedule"):
            recurrence = detect_recurrence(answer)
            if recurrence:
                slots["schedule"] = recurrence
        elif not title:
            slots["title"] = _clean_title(answer)
        ready = bool(slots.get("title") and slots.get("schedule"))
        confidence = 0.9 if ready else MEDIUM_CONFIDENCE

    else:  # create_goal
        if not title:
            slots["title"] = _clean_title(answer)
        ready = bool(slots.get("title"))
        confidence = 0.88 if ready else MEDIUM_CONFIDENCE

    if confidence == MEDIUM_CONFIDENCE:
        reason = pending.reason
    else:
        reason = f"{pending.action} confirmed"

    return ProposedAction(
        action=pending.action,
        source="rules",
        confidence=confidence,
        slots=slots,
        reason=reason,
    )
