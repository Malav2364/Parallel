from pydantic import BaseModel, Field


class Streak(BaseModel):
    current: int = Field(
        ge=0,
    )

    longest: int = Field(
        ge=0,
    )
