from datetime import datetime
from uuid import UUID

from pios_kernel.enums import SpaceSource, SpaceType, Visibility
from pydantic import BaseModel, ConfigDict, Field


class SpaceCreateRequest(BaseModel):
    """Request payload for creating a user-owned space."""

    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type: SpaceType = SpaceType.CUSTOM
    visibility: Visibility = Visibility.PRIVATE
    source: SpaceSource = SpaceSource.USER
    icon: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=20)


class SpaceResponse(BaseModel):
    """Public representation of a space."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: str
    name: str
    slug: str
    description: str | None = None
    type: str
    visibility: str
    source: str
    icon: str | None = None
    color: str | None = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
