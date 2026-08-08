from enum import Enum


class SpaceType(str, Enum):
    PERSONAL = "personal"
    HEALTH = "health"
    HABITS = "habits"
    LEARNING = "learning"
    FINANCE = "finance"
    CAREER = "career"
    BUSINESS = "business"
    CUSTOM = "custom"
