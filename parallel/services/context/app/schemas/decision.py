from typing import Literal

from pydantic import BaseModel, Field

SignalType = Literal[
    "life_change",
    "project",
    "goal",
    "habit",
    "interest",
    "context_update",
]

ActionType = Literal[
    "none",
    "create_goal",
    "create_habit",
    "create_project",
    "suggest_space",
    "create_reminder",
]


class ContextDecision(BaseModel):
    signals: list["ContextSignal"] = Field(default_factory=list)
    action: ActionType
    reason: str

    # Project
    project_name: str | None = None
    project_description: str | None = None
    space_candidate: str | None = None

    # Goal
    goal_name: str | None = None
    goal_description: str | None = None
    goal_status: str | None = "active"
    goal_target_date: str | None = None

    # Habit
    habit_name: str | None = None
    habit_description: str | None = None
    habit_schedule: str | None = None
    habit_time_window: str | None = None
    habit_status: str | None = "active"

    # Reminder_Services
    reminder_title: str | None = None
    reminder_description: str | None = None
    reminder_scheduled_for: str | None = None
    reminder_recurrence: str | None = None
    reminder_status: str | None = "pending"


class ContextSignal(BaseModel):
    type: SignalType
    description: str
    significance: float = Field(ge=0, le=1)
    name: str | None = None
