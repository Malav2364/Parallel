"""Tier-1 date grammar: fast, offline, deterministic scheduling parse.

A fixed clock (Sunday 2026-08-23 10:00 IST) anchors every relative phrase so
the expected datetimes are stable regardless of when the suite runs.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.nlu.datetime_grammar import detect_recurrence, parse_schedule

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 8, 23, 10, 0, tzinfo=IST)


def _ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("every day at 9am", "daily"),
        ("daily at 9am", "daily"),
        ("every monday at 8am", "weekly"),
        ("weekly on friday", "weekly"),
        ("monthly on the 15th", "monthly"),
        ("every month on the 1st", "monthly"),
        ("tomorrow at 6pm", None),
        ("call mom next friday", None),
    ],
)
def test_detect_recurrence(text: str, expected: str | None) -> None:
    assert detect_recurrence(text) == expected


@pytest.mark.parametrize(
    "text, expected_dt, expected_recurrence",
    [
        ("every day at 9am", _ist(2026, 8, 24, 9, 0), "daily"),
        ("every monday at 8am", _ist(2026, 8, 24, 8, 0), "weekly"),
        ("tomorrow at 6pm", _ist(2026, 8, 24, 18, 0), None),
        ("in 2 hours", _ist(2026, 8, 23, 12, 0), None),
        ("call mom next friday 5pm", _ist(2026, 8, 28, 17, 0), None),
        # dateparser anchors "the 15th" to the past month; the future-roll
        # must push a monthly first-occurrence forward to 2026-09-15.
        ("monthly on the 15th at 9am", _ist(2026, 9, 15, 9, 0), "monthly"),
    ],
)
def test_parse_schedule_resolves(
    text: str, expected_dt: datetime, expected_recurrence: str | None
) -> None:
    result = parse_schedule(text, now=NOW)

    assert result is not None
    assert result.scheduled_for == expected_dt
    assert result.recurrence == expected_recurrence
    assert result.scheduled_for > NOW


@pytest.mark.parametrize("text", ["at 8", "every monday at 8", "remind me at 12"])
def test_ambiguous_bare_hour_is_deferred(text: str) -> None:
    """A bare hour has no am/pm; Tier 1 declines rather than guessing."""

    assert parse_schedule(text, now=NOW) is None


def test_unparseable_text_returns_none() -> None:
    assert parse_schedule("do the thing", now=NOW) is None
