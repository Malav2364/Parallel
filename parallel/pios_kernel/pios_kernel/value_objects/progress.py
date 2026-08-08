from pydantic import BaseModel, Field


class Progress(BaseModel):
    value: float = Field(
        ge=0,
        le=100,
    )
