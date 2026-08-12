from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from pios_kernel.enums import LifeStage


class UserProfile(BaseModel):
    id: UUID

    workspace_id: UUID

    occupation: str | None = None

    life_stage: LifeStage = LifeStage.UNKNOWN

    bio: str | None = None

    current_focus: list[str] = Field(default_factory=list)

    interests: list[str] = Field(default_factory=list)

    strengths: list[str] = Field(default_factory=list)

    weaknesses: list[str] = Field(default_factory=list)

    values: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
