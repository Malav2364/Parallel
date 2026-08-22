from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="active", min_length=1, max_length=50)
    target_date: str | None = Field(default=None, max_length=100)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    owner_id: str
    status: str
    target_date: str | None
    created_at: datetime
    updated_at: datetime
