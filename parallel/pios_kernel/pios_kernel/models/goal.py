from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from pios_kernel.enums import GoalStatus, GoalType
from pios_kernel.value_objects import Priority, Progress


class Goal(BaseModel):
    id: UUID

    space_id: UUID

    title: str

    description: str | None = None

    why: str | None = None

    status: GoalStatus = GoalStatus.NOT_STARTED

    priority: Priority = Field(
        default_factory=lambda: Priority(value=3),
    )

    progress: Progress = Field(
        default_factory=lambda: Progress(value=0),
    )

    target_date: date | None = None

    started_at: date | None = None

    type: GoalType = GoalType.CUSTOM

    completed_at: date | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
