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


def propose(text, now=None) -> ProposedAction | None:
    """Run the deterministic rules, returning the first confident match."""

    return propose_reminder(text, now=now)
