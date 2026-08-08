from enum import Enum


class GoalType(str, Enum):
    OUTCOME = "outcome"

    HABIT = "habit"

    LEARNING = "learning"

    PROJECT = "project"

    FINANCIAL = "financial"

    HEALTH = "health"

    CUSTOM = "custom"
