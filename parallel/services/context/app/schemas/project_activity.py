from pydantic import BaseModel, Field


class ProjectActivity(BaseModel):
    current_focus: str | None = None
    latest_activity: str | None = None
    confidence: float = Field(
        ge=0,
        le=1,
    )