from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from pios_kernel.enums import HabitFrequency, HabitType
from pios_kernel.value_objects import Progress, Streak


class Habit(BaseModel):
    id: UUID

    space_id: UUID

    name: str

    description: str | None = None

    type: HabitType

    frequency: HabitFrequency

    streak: Streak = Field(
        default_factory=lambda: Streak(current=0, longest=0),
    )

    why: str | None = None

    completion_rate: Progress = Field(
        default_factory=lambda: Progress(value=0),
    )

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
