from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas import ContextDecision, ProjectResolution
from app.schemas.understanding import UnderstandingResult
from app.services.context_decision import build_decision_prompt
from app.services.context_extractor import ContextExtraction


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
{activity_line}
"""


class UnderstandingEngine:
    """One Gemini call that both decides and, for a matched project, reports activity.

    Collapses what used to be two calls -- ``ContextDecisionEngine.evaluate``
    and ``ProjectActivityExtractor.extract`` -- into a single
    ``generate_content`` whose structured output nests both under ``decision``
    and ``activity``. The two are independent (activity needs only the resolved
    project; the decision needs extraction + resolution), so one prompt carries
    both without either constraining the other.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def decide(
        self,
        user_input: str,
        current_context: dict,
        extraction: ContextExtraction,
        project_resolution: ProjectResolution | None = None,
        project: dict | None = None,
        now=datetime.now(ZoneInfo("Asia/Kolkata")),
    ) -> UnderstandingResult:
        prompt = build_decision_prompt(
            user_input=user_input,
            current_context=current_context,
            extraction=extraction,
            project_resolution=project_resolution,
            now=now,
        )

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
            return UnderstandingResult.model_validate_json(response.text or "{}")
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
