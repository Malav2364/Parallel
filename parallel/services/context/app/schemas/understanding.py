from pydantic import BaseModel, Field

from app.schemas.decision import ContextDecision
from app.schemas.extraction import ContextExtraction
from app.schemas.project_activity import ProjectActivity


class UnderstandingResult(BaseModel):
    """One Gemini call's merged output: the decision, the durable-context
    extraction, and (for a matched project) the activity.

    ``decision``, ``extraction``, and ``activity`` reuse the existing schemas
    verbatim, so the ``/process`` response builder and ``compose.py`` read the
    same attributes they did when these were separate calls. ``activity`` is
    ``None`` whenever no existing project was resolved for the message.
    ``extraction`` defaults to empty updates, so a response that omits it
    degrades to "no durable context" rather than failing the whole turn.
    """

    decision: ContextDecision
    activity: ProjectActivity | None = None
    extraction: ContextExtraction = Field(
        default_factory=lambda: ContextExtraction(
            updates={}, confidence=0.0, reasoning=""
        )
    )
