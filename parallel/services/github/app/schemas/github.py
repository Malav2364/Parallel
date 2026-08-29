from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TokenConnectRequest(BaseModel):
    pat: str = Field(min_length=1)


class TokenStatusResponse(BaseModel):
    connected: bool
    hint: str | None = None
    login: str | None = None


class SyncResponse(BaseModel):
    review_requests: int
    my_prs: int


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    external_id: str
    payload: dict
    created_at: datetime
    synced_at: datetime
    read_at: datetime | None
