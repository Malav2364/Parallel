from pydantic import BaseModel, Field


class ProjectResolution(BaseModel):
    matched: bool

    project_id: str | None = None

    confidence: float = Field(
        ge=0,
        le=1,
    )

    reason: str
