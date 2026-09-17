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


def _resolution_section(projects: list[dict]) -> str:
    """Appended on the self-resolve path: ask this same call to resolve the
    project itself, carrying the ``ProjectResolver`` rules verbatim so the merged
    call resolves exactly as the standalone resolver used to on its own turn.
    """

    return f"""

IMPORTANT PROJECT RESOLUTION:

Determine whether the user's message refers to one of the user's existing
projects, and record the outcome in the `resolution` object.

Existing projects:
{projects}

Rules:

1. Match the user's message to an existing project when
   the message is meaningfully related to that project's
   objective, description, current focus, latest activity,
   or known terminology.

2. Do not require the user to explicitly mention the
   project name.

3. Infer reasonable semantic relationships.

4. For example, a project named "AI Startup" with a
   current focus of "Payment integration" should match
   messages about:
   - payment integration
   - Stripe
   - checkout
   - payment gateway
   - billing
   - subscriptions
   - fixing payment bugs

5. Do not match merely because a generic word overlaps.

6. If two or more projects are plausible matches and the
   message does not provide enough evidence to distinguish
   them, return matched=false.

7. If a message contains multiple intents, separate project
   activity from broader context updates. Match the project that
   the concrete work or progress belongs to.

8. Do not treat a separate future focus, study plan, goal, or
   life-area mention as a competing project match unless the
   message describes concrete activity within that project too.

9. For example, "I completed the checkout page of my AI product
   and now I will study for MBA" should match the AI product
   project for the checkout activity. The MBA portion is a
   separate context or goal update.

10. If there is no meaningful relationship, return matched=false.

11. Never invent a project ID.

12. Confidence must be between 0 and 1.

13. Prefer an existing project when the semantic relationship
    is strong, even if the project name is not explicitly
    mentioned.

Produce the `resolution` object with exactly these fields:
- `resolution.matched`: true if the message refers to one of the existing
  projects above, false otherwise.
- `resolution.project_id`: the matched project's `id` when matched is true;
  null when matched is false. Never invent an ID -- use only an `id` listed
  above.
- `resolution.confidence`: a number between 0 and 1.
- `resolution.reason`: a short justification.
"""


def _conditional_activity_section() -> str:
    """Appended on the self-resolve path: extract activity only if the model's
    own ``resolution`` matched one of the candidate projects."""

    return """

IMPORTANT PROJECT ACTIVITY EXTRACTION:

IF your `resolution` above matched one of the candidate projects, ALSO extract
the user's activity WITHIN that resolved project into the `activity` object:

- `activity.latest_activity`: something the user actually did, changed,
  completed, started, or encountered within the resolved project. Null if none.
- `activity.current_focus`: what the user is currently working on within the
  resolved project. Null if their stated next focus is unrelated to it.
- `activity.confidence`: a number between 0 and 1.

Only extract activity supported by the message and belonging specifically to
the resolved project. Do not treat an unrelated goal, study plan, life area, or
habit as project activity. If `resolution.matched` is false, or the message
contains no useful project activity, set `activity` to null.
"""


def _output_format_section(has_project: bool, self_resolve: bool = False) -> str:
    """Map the decision examples above onto the nested output shape."""

    if self_resolve:
        resolution_line = (
            "- `resolution`: the project resolution object described above."
        )
        activity_line = (
            "- `activity`: the resolved project's activity object if your "
            "`resolution` matched an existing project, otherwise null."
        )
    else:
        resolution_line = (
            "- `resolution`: null. The project was already resolved before this "
            "call."
        )
        activity_line = (
            "- `activity`: the project activity object described above."
            if has_project
            else (
                "- `activity`: null. No existing project was resolved for "
                "this message."
            )
        )
    return f"""

OUTPUT FORMAT:

Return a single JSON object with exactly these top-level keys:
- `decision`: the decision object described above (its `signals`, `action`,
  `reason`, and any entity fields). Every decision rule and example above
  describes the CONTENTS of this `decision` object.
- `extraction`: the durable context extraction object described above.
{resolution_line}
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

    def __init__(self, client=None):
        # Reuse the process-wide genai client when the app lifespan supplies one;
        # fall back to building our own so directly-constructed engines (tests,
        # scripts) keep working unchanged.
        self.client = client or genai.Client(api_key=settings.GEMINI_API_KEY)

    def decide(
        self,
        user_input: str,
        current_context: dict,
        project_resolution: ProjectResolution | None = None,
        project: dict | None = None,
        projects: list[dict] | None = None,
        now: datetime | None = None,
    ) -> UnderstandingResult:
        # Default args evaluate once at import, which would freeze "now" for the
        # process lifetime; resolve it per call instead.
        now = now or datetime.now(ZoneInfo("Asia/Kolkata"))

        # Self-resolve: the caller handed us the candidate projects but no
        # concrete resolution, so this same call resolves the project itself (a
        # Tier-2 miss). On the HIT and no-projects paths a concrete
        # ``project_resolution`` is supplied and ``result.resolution`` is left
        # null and ignored.
        self_resolve = project_resolution is None and projects is not None

        prompt = build_decision_prompt(
            user_input=user_input,
            current_context=current_context,
            extraction=None,
            project_resolution=project_resolution,
            now=now,
            self_resolve=self_resolve,
        )

        prompt += _extraction_section()

        if self_resolve:
            prompt += _resolution_section(projects)
            prompt += _conditional_activity_section()
        elif project is not None:
            prompt += _activity_section(project)

        prompt += _output_format_section(project is not None, self_resolve=self_resolve)

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
            # no-op decision rather than raising and failing the whole turn. On
            # the self-resolve path the caller reads ``resolution.matched``, so
            # guarantee a concrete not-matched resolution there.
            return UnderstandingResult(
                decision=ContextDecision(
                    action="none",
                    reason="The understanding engine returned an unparseable result.",
                ),
                activity=None,
                resolution=(
                    ProjectResolution(
                        matched=False,
                        confidence=0.0,
                        reason=(
                            "The understanding engine returned an "
                            "unparseable result."
                        ),
                    )
                    if self_resolve
                    else None
                ),
            )

        # On the self-resolve path the caller trusts ``result.resolution`` to be
        # concrete and valid. Guarantee that here (never silently wrong): fill a
        # missing resolution, and reject a manufactured project ID exactly as the
        # standalone resolver's safety check did.
        if self_resolve:
            if result.resolution is None:
                result.resolution = ProjectResolution(
                    matched=False,
                    confidence=0.0,
                    reason="The understanding engine produced no resolution.",
                )
            elif result.resolution.matched:
                valid_ids = {p["id"] for p in projects}
                if result.resolution.project_id not in valid_ids:
                    result.resolution = ProjectResolution(
                        matched=False,
                        confidence=0.0,
                        reason="Resolver returned an invalid project ID.",
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
