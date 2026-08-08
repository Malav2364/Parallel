from enum import Enum


class LifeStage(str, Enum):
    UNKNOWN = "unknown"
    STUDENT = "student"
    PROFESSIONAL = "professional"
    ENTREPRENEUR = "entrepreneur"
    RETIRED = "retired"
