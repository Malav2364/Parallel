from enum import Enum


class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
