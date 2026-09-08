from typing import Any

from pydantic import BaseModel, Field


class Goal(BaseModel):
    name: str = Field(min_length=1)
    status: str = "active"
    target_date: str | None = None


class ContextUpdate(BaseModel):
    updates: dict[str, Any] = Field(min_length=1)


class ContextExtractRequest(BaseModel):
    message: str = Field(min_length=1)


class ContextAnalyzeRequest(BaseModel):
    message: str = Field(min_length=1)


class ContextProcessRequest(ContextAnalyzeRequest):
    # Echoed-back pending action from a prior needs_confirmation response. Kept
    # as a plain dict (not ProposedAction) to avoid an app.schemas <-> app.nlu
    # import cycle; /process validates it into a ProposedAction.
    pending_action: dict[str, Any] | None = None


class ContextResponse(BaseModel):
    user_id: str
    context: dict[str, Any]
    version: int
