from enum import Enum


class SpaceSource(str, Enum):
    SYSTEM = "system"
    USER = "user"
    AI = "ai"
    IMPORTED = "imported"
