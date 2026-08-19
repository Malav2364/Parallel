from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


class ReminderDateTimeResolver:
    @staticmethod
    def resolve(
        date_expression: str,
        time_expression: str,
        now: datetime | None = None,
    ) -> datetime:
        if now is None:
            now = datetime.now(IST)

        if now.tzinfo is None:
            now = now.replace(tzinfo=IST)
        else:
            now = now.astimezone(IST)

        date_expression = date_expression.strip().casefold()
        hour, minute = map(
            int,
            time_expression.strip().split(":"),
        )

        if date_expression == "today":
            target_date = now.date()

        elif date_expression == "tomorrow":
            target_date = now.date() + timedelta(days=1)

        elif date_expression == "day after tomorrow":
            target_date = now.date() + timedelta(days=2)

        else:
            target_date = ReminderDateTimeResolver._resolve_weekday(
                date_expression=date_expression,
                now=now,
            )

        scheduled_for = datetime(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=hour,
            minute=minute,
            tzinfo=IST,
        )

        return scheduled_for

    @staticmethod
    def _resolve_weekday(
        date_expression: str,
        now: datetime,
    ):
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        expression = date_expression.replace("next ", "").strip()

        if expression not in weekdays:
            raise ValueError(
                f"Unsupported reminder date expression: "
                f"{date_expression}"
            )

        target_weekday = weekdays[expression]
        current_weekday = now.weekday()

        days_ahead = (
            target_weekday - current_weekday
        ) % 7

        if days_ahead == 0:
            days_ahead = 7

        return (
            now.date()
            + timedelta(days=days_ahead)
        )