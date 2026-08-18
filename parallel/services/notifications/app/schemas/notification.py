from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    type: str = Field(min_length=1, max_length=50)
    priority: str = Field(
        default="normal",
        max_length=50,
    )


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    title: str
    message: str
    type: str
    status: str
    priority: str
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime