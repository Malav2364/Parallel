from datetime import datetime
from typing import Literal

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


class CommentCreateRequest(BaseModel):
    repo: str = Field(min_length=1)
    number: int
    body: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: int
    url: str
    body: str


class ApprovalCreateRequest(BaseModel):
    repo: str = Field(min_length=1)
    number: int
    body: str | None = None


class ReviewResponse(BaseModel):
    id: int
    state: str


class MergeCreateRequest(BaseModel):
    repo: str = Field(min_length=1)
    number: int
    merge_method: Literal["merge", "squash", "rebase"] = "merge"


class MergeResponse(BaseModel):
    merged: bool
    sha: str | None = None
    message: str


class CloseCreateRequest(BaseModel):
    repo: str = Field(min_length=1)
    number: int


class PullStateResponse(BaseModel):
    number: int
    state: str

