from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RecurrenceType = Literal[
    "daily",
    "weekly",
    "monthly",
]


class ReminderCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    scheduled_for: datetime

    timezone: str = Field(
        default="Asia/Kolkata",
        max_length=100,
    )

    recurrence: RecurrenceType | None = None

    status: str = Field(
        default="pending",
        max_length=50,
    )


class ReminderUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    scheduled_for: datetime | None = None

    timezone: str | None = Field(
        default=None,
        max_length=100,
    )

    recurrence: RecurrenceType | None = None

    status: str | None = Field(
        default=None,
        max_length=50,
    )


class ReminderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str
    owner_id: str
    title: str
    description: str | None
    scheduled_for: datetime
    timezone: str = "Asia/Kolkata"
    status: str
    recurrence: RecurrenceType | None = None
    created_at: datetime
    updated_at: datetime