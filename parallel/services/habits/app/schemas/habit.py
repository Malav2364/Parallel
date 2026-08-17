from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    schedule: str = Field(min_length=1, max_length=255)
    time_window: str | None = Field(
        default=None,
        max_length=100,
    )
    status: str = Field(
        default="active",
        max_length=50,
    )


class HabitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    normalized_name: str
    description: str | None
    owner_id: str
    schedule: str
    time_window: str | None
    status: str
    created_at: datetime
    updated_at: datetime