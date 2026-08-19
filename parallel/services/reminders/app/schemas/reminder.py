from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    scheduled_for: datetime

    recurrence: str | None = Field(
        default=None,
        max_length=100,
    )

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

    recurrence: str | None = Field(
        default=None,
        max_length=100,
    )

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
    status: str
    recurrence: str | None
    created_at: datetime
    updated_at: datetime