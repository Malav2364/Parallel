from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas import ContextDecision, ProjectResolution
from app.schemas.understanding import UnderstandingResult
from app.services.context_decision import build_decision_prompt
from app.services.context_extractor import (
    ContextExtraction,
    normalize_extraction_updates,
)


def _extraction_section() -> str:
    """Always appended: ask the same call to also extract durable context.

    Carries the ``ContextExtractor`` rules so the merged call produces the
    extraction the standalone extractor used to produce on its own turn.
    """

    return """

IMPORTANT DURABLE CONTEXT EXTRACTION:

In ADDITION to the decision above, identify meaningful, durable, user-specific
information from the user's message into the `extraction` object:

- `extraction.updates`: an object of durable context changes. Empty if none.
- `extraction.confidence`: a number between 0 and 1.
- `extraction.reasoning`: a short justification.

Rules for `extraction.updates`:
1. Extract only information supported by the message; never invent facts.
2. Do not treat temporary events as permanent user characteristics.
3. Capture changes to occupation, interests, goals, priorities, habits,
   preferences, or important life circumstances only when explicitly supported.
4. Extract only the user's CURRENT state. Never create previous_*, old_*,
   former_*, historical_*, or similar historical keys -- the Context Service
   derives history itself through change detection.
5. When the user describes a transition in occupation, career, lifestyle, or a
   major commitment, record the new state as a current-state field such as
   career_status or current_focus. Do not infer a new occupation unless the
   user explicitly establishes it.
6. Do not store project progress, project status, completed tasks, or activity
   updates here -- those belong to the Project Activity layer.
7. Never return a top-level `projects` key. Existing projects are owned by the
   Projects Service, not user context.
8. A goal introduced by THIS message goes in `extraction.updates.goals_to_add`,
   which must contain ONLY newly introduced goals. Never copy goals from the
   current context into it. If an existing goal is merely discussed or updated,
   represent that as an appropriate update instead of a duplicate.
9. If the message carries no meaningful durable information, return an empty
   `extraction.updates` object.
"""


def _activity_section(project: dict) -> str:
    """Appended only when a project resolved: ask for that project's activity."""

    return f"""

IMPORTANT PROJECT ACTIVITY EXTRACTION:

The user's message has been resolved to this existing project:
{project}

In ADDITION to the decision above, extract the user's activity WITHIN this
project into the `activity` object:

- `activity.latest_activity`: something the user actually did, changed,
  completed, started, or encountered within THIS project. Null if none.
- `activity.current_focus`: what the user is currently working on within THIS
  project. Null if their stated next focus is unrelated to this project.
- `activity.confidence`: a number between 0 and 1.

Only extract activity supported by the message and belonging specifically to
this project. Do not treat an unrelated goal, study plan, life area, or habit
as this project's activity. If the message contains no useful project
activity, set both latest_activity and current_focus to null.
"""


def _output_format_section(has_project: bool) -> str:
    """Map the decision examples above onto the nested output shape."""

    activity_line = (
        "- `activity`: the project activity object described above."
        if has_project
        else "- `activity`: null. No existing project was resolved for this message."
    )
    return f"""

OUTPUT FORMAT:

Return a single JSON object with exactly these top-level keys:
- `decision`: the decision object described above (its `signals`, `action`,
  `reason`, and any entity fields). Every decision rule and example above
  describes the CONTENTS of this `decision` object.
- `extraction`: the durable context extraction object described above.
{activity_line}
"""


class UnderstandingEngine:
    """One Gemini call that extracts, decides, and reports a matched project's activity.

    Collapses what used to be three calls -- ``ContextExtractor.extract``,
    ``ContextDecisionEngine.evaluate``, and
    ``ProjectActivityExtractor.extract`` -- into a single ``generate_content``
    whose structured output nests all three under ``extraction``, ``decision``,
    and ``activity``. They are independent enough to share one prompt: activity
    needs only the resolved project, and the decision reasons from the raw
    message plus the pre-update context rather than from applied updates.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def decide(
        self,
        user_input: str,
        current_context: dict,
        project_resolution: ProjectResolution | None = None,
        project: dict | None = None,
        now=datetime.now(ZoneInfo("Asia/Kolkata")),
    ) -> UnderstandingResult:
        prompt = build_decision_prompt(
            user_input=user_input,
            current_context=current_context,
            extraction=None,
            project_resolution=project_resolution,
            now=now,
        )

        prompt += _extraction_section()

        if project is not None:
            prompt += _activity_section(project)

        prompt += _output_format_section(project is not None)

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": UnderstandingResult.model_json_schema(),
            },
        )

        try:
            result = UnderstandingResult.model_validate_json(response.text or "{}")
        except ValidationError:
            # Never silently wrong: a malformed or partial merge falls back to a
            # no-op decision rather than raising and failing the whole turn.
            return UnderstandingResult(
                decision=ContextDecision(
                    action="none",
                    reason="The understanding engine returned an unparseable result.",
                ),
                activity=None,
            )

        # Normalize exactly as the standalone extractor would, so the merged
        # path and the Tier-1 path hand ``apply_updates`` the same shape.
        result.extraction = ContextExtraction(
            updates=normalize_extraction_updates(
                dict(result.extraction.updates), current_context
            ),
            confidence=result.extraction.confidence,
            reasoning=result.extraction.reasoning,
        )
        return result
