from pydantic import BaseModel

from app.schemas.decision import ContextDecision
from app.schemas.project_activity import ProjectActivity


class UnderstandingResult(BaseModel):
    """One Gemini call's merged output: the decision plus optional activity.

    ``decision`` and ``activity`` reuse the existing schemas verbatim, so the
    ``/process`` response builder and ``compose.py`` read the same attributes
    they did when these were two separate calls. ``activity`` is ``None``
    whenever no existing project was resolved for the message.
    """

    decision: ContextDecision
    activity: ProjectActivity | None = None
