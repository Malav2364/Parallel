from pydantic import BaseModel, Field


class Priority(BaseModel):
    value: int = Field(
        ge=1,
        le=5,
    )
