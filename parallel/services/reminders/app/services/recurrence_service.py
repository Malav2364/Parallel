from datetime import datetime
from calendar import monthrange


class RecurrenceService:
    @staticmethod
    def get_next_occurrence(
        scheduled_for: datetime,
        recurrence: str | None,
    ) -> datetime | None:
        if not recurrence:
            return None

        recurrence = recurrence.strip().lower()

        if recurrence == "daily":
            from datetime import timedelta

            return scheduled_for + timedelta(days=1)

        if recurrence == "weekly":
            from datetime import timedelta

            return scheduled_for + timedelta(days=7)

        if recurrence == "monthly":
            year = scheduled_for.year
            month = scheduled_for.month

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            day = min(
                scheduled_for.day,
                monthrange(year, month)[1],
            )

            return scheduled_for.replace(
                year=year,
                month=month,
                day=day,
            )

        raise ValueError(
            f"Unsupported recurrence: {recurrence}"
        )