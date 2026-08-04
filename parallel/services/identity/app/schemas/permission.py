from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=255,
    )


class PermissionUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=255,
    )


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )
