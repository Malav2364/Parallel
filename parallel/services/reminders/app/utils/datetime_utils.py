from datetime import datetime, timezone
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Kolkata"


def normalize_to_utc(
    value: datetime,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> datetime:
    """
    Convert a datetime to UTC.

    Naive datetime:
        Interpret it using the supplied timezone.

    Aware datetime:
        Respect its existing timezone/offset.
    """

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=ZoneInfo(timezone_name)
        )

    return value.astimezone(timezone.utc)