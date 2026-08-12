from pydantic import BaseModel, Field


class Confidence(BaseModel):
    value: float = Field(
        ge=0,
        le=100,
    )
