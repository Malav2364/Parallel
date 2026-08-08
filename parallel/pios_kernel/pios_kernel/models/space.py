from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from pios_kernel.enums import SpaceSource, SpaceType, Visibility
from pios_kernel.value_objects import Color


class Space(BaseModel):
    id: UUID

    workspace_id: UUID

    name: str

    description: str | None = None

    type: SpaceType

    visibility: Visibility = Visibility.PRIVATE

    icon: str | None = None

    color: Color | None = None

    source: SpaceSource = SpaceSource.USER

    is_archived: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
