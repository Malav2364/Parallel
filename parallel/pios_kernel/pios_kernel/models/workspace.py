from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Workspace(BaseModel):
    id: UUID
    owner_id: UUID

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
