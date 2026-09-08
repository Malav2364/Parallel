"""Deterministic date, time, and recurrence parsing.

Turns natural-language scheduling phrases ("tomorrow at 6pm", "in 2 hours",
"every monday at 9") into a concrete IST-aware datetime plus an optional
recurrence, without calling an LLM. This is the Tier-1 fast path: instant,
offline, and fully testable, which removes the model from the most common
and most error-prone slot-filling job.
"""

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import dateparser
from dateparser.search import search_dates

IST = ZoneInfo("Asia/Kolkata")

# Recurrence phrases -> the vocabulary the reminders service already accepts
# (services/reminders RecurrenceType: daily | weekly | monthly).
_RECURRENCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bevery\s*month\b|\bmonthly\b|\beach\s*month\b"), "monthly"),
    (re.compile(r"\bevery\s*week\b|\bweekly\b|\beach\s*week\b"), "weekly"),
    (re.compile(r"\bevery\s+(mon|tue|wed|thu|fri|sat|sun)\w*"), "weekly"),
    (re.compile(r"\bevery\s*day\b|\bdaily\b|\beach\s*day\b"), "daily"),
]

# Frequency words to remove before date parsing (weekday names are kept so
# the parser can still anchor the first occurrence, e.g. "every monday").
_STRIP_FOR_PARSE = re.compile(
    r"\b(every\s*day|each\s*day|daily|every\s*week|each\s*week|weekly|"
    r"every\s*month|each\s*month|monthly|every|each)\b"
)

# An unambiguous clock time: "9am", "9 pm", "9:30", "18:00", "noon", "midnight".
_EXPLICIT_TIME = re.compile(
    r"\b\d{1,2}\s*(?::\d{2})?\s*(?:am|pm)\b|\b\d{1,2}:\d{2}\b|\b(?:noon|midnight)\b"
)

# The user gestured at a time ("at 8") but may not have made it unambiguous.
_TIME_INTENT = re.compile(r"\bat\s+\d")

# A word that plausibly anchors a date/time. search_dates() happily invents
# dates from arbitrary prose, so we only consult it when one of these is
# present ("call mom next friday 5pm" -> yes; "do the thing" -> no).
_TEMPORAL_HINT = re.compile(
    r"\b(?:mon|tue|wed|thu|fri|sat|sun)\w*\b"
    r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b"
    r"|\b(?:today|tonight|tomorrow|tmrw|noon|midnight)\b"
    r"|\b(?:next|this|coming)\b"
    r"|\bin\s+\d+\s*(?:min|hour|day|week|month|year)"
    r"|\b\d{1,2}\s*(?::\d{2})?\s*(?:am|pm)\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)\b"
    r"|\bat\s+\d"
)

# The start of a trailing temporal clause. We split the utterance here so the
# subject ("take medicine") and the time phrase ("every day at 9am") can be
# parsed independently -- dateparser.parse is reliable on a clean time phrase
# but not on a full sentence.
_TEMPORAL_START = re.compile(
    r"\b(?:every|each|daily|weekly|monthly"
    r"|day\s+after\s+tomorrow|today|tonight|tomorrow|tmrw"
    r"|next|this|coming"
    r"|mon(?:day)?|tue(?:s|sday)?|wed(?:nesday)?|thu(?:r|rs|rsday)?"
    r"|fri(?:day)?|sat(?:urday)?|sun(?:day)?"
    r"|jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*"
    r"|sep\w*|oct\w*|nov\w*|dec\w*"
    r"|noon|midnight|in\s+\d+|at\s+\d"
    r"|\d{1,2}(?::\d{2})?\s*(?:am|pm)|\d{1,2}(?:st|nd|rd|th))\b",
    re.IGNORECASE,
)


def split_time(text: str) -> tuple[str, str | None]:
    """Split an utterance into (subject, trailing time phrase).

    Returns ``(text, None)`` when no temporal clause is found.
    """

    match = _TEMPORAL_START.search(text)
    if match is None:
        return text.strip(), None

    subject = text[: match.start()].strip()
    time_phrase = text[match.start() :].strip()
    return subject, time_phrase


_SETTINGS = {
    "TIMEZONE": "Asia/Kolkata",
    "RETURN_AS_TIMEZONE_AWARE": True,
    "PREFER_DATES_FROM": "future",
}


@dataclass(frozen=True)
class ParsedSchedule:
    scheduled_for: datetime  # IST-aware
    recurrence: str | None
    confidence: float


def detect_recurrence(text: str) -> str | None:
    lowered = text.casefold()

    for pattern, recurrence in _RECURRENCE_PATTERNS:
        if pattern.search(lowered):
            return recurrence

    return None


def _add_month(dt: datetime) -> datetime:
    """Advance one calendar month, clamping the day to the month's length."""

    month = dt.month % 12 + 1
    year = dt.year + (dt.month // 12)
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


# "the 15th", "on the 1st", "22nd" -> an explicit day of the month.
_ORDINAL_DAY = re.compile(r"\b(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)\b", re.IGNORECASE)


def _next_day_of_month(day: int, now: datetime) -> datetime | None:
    """The soonest date (today or later) that falls on ``day`` of a month."""

    year, month = now.year, now.month
    for _ in range(13):
        if day <= calendar.monthrange(year, month)[1]:
            candidate = now.replace(
                year=year,
                month=month,
                day=day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            if candidate.date() >= now.date():
                return candidate
        month = month % 12 + 1
        if month == 1:
            year += 1
    return None


def _resolve_ordinal_day(phrase: str, now: datetime) -> str:
    """Rewrite a day-of-month ordinal to an ISO date dateparser reads reliably.

    dateparser misreads "the 1st" as January; anchoring it to a concrete date
    first ("2026-09-01") leaves only the time for dateparser to interpret.
    """

    match = _ORDINAL_DAY.search(phrase)
    if match is None:
        return phrase

    day = int(match.group(1))
    if not 1 <= day <= 31:
        return phrase

    candidate = _next_day_of_month(day, now)
    if candidate is None:
        return phrase

    return _ORDINAL_DAY.sub(candidate.strftime("%Y-%m-%d"), phrase, count=1)


def _ensure_future(dt: datetime, recurrence: str | None, now: datetime) -> datetime:
    """Roll a recurring first-occurrence forward until it is in the future.

    dateparser sometimes anchors a recurring phrase ("monthly on the 15th")
    to a date that has already passed this period; the reminders service
    needs the first fire in the future, so we step by the recurrence unit.
    """

    if dt > now or recurrence is None:
        return dt

    if recurrence == "weekly":
        while dt <= now:
            dt += timedelta(weeks=1)
    elif recurrence == "monthly":
        while dt <= now:
            dt = _add_month(dt)
    else:  # daily
        while dt <= now:
            dt += timedelta(days=1)

    return dt


def parse_schedule(
    text: str,
    now: datetime | None = None,
) -> ParsedSchedule | None:
    """Parse a scheduling phrase, or return ``None`` if no date is found."""

    if now is None:
        now = datetime.now(IST)

    recurrence = detect_recurrence(text)

    # Frequency words ("every", "daily") only confuse the date parser, so we
    # strip them for parsing while keeping any weekday/time anchor intact.
    cleaned = _STRIP_FOR_PARSE.sub(" ", text.casefold()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Anchor any day-of-month ordinal before parsing (dateparser misreads it).
    cleaned = _resolve_ordinal_day(cleaned, now)

    # A bare hour ("at 8") is ambiguous am/pm; dateparser silently misreads it
    # as a year. Rather than guess, we defer so a higher tier can confirm.
    if _TIME_INTENT.search(cleaned) and not _EXPLICIT_TIME.search(cleaned):
        return None

    settings = {**_SETTINGS, "RELATIVE_BASE": now.replace(tzinfo=None)}

    # Primary: dateparser.parse handles compact phrases reliably
    # ("at 9am", "monday at 8am", "in 2 hours", "tomorrow at 6pm").
    scheduled_for = dateparser.parse(cleaned or text, settings=settings)
    confidence = 0.9

    # Fallback: search_dates picks a date out of a fuller sentence
    # ("call mom next friday 5pm") where parse() returns nothing. It is
    # gated on a temporal hint so it cannot fabricate a date from prose.
    if scheduled_for is None:
        if not _TEMPORAL_HINT.search(cleaned):
            return None
        found = search_dates(text, settings=settings)
        if not found:
            return None
        scheduled_for = found[-1][1]
        confidence = 0.75

    if scheduled_for.tzinfo is None:
        scheduled_for = scheduled_for.replace(tzinfo=IST)
    else:
        scheduled_for = scheduled_for.astimezone(IST)

    scheduled_for = _ensure_future(scheduled_for, recurrence, now)

    return ParsedSchedule(
        scheduled_for=scheduled_for,
        recurrence=recurrence,
        confidence=confidence,
    )
