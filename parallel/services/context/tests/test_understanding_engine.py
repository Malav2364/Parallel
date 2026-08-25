"""UnderstandingEngine: the single Gemini call that decides and, for a matched
project, reports that project's activity in the same structured response.

These are hermetic -- no genai client is constructed and no network is touched.
Each test builds the engine via ``__new__`` (skipping the real client) and swaps
in a fake whose ``models.generate_content`` returns canned JSON while recording
the prompt and config it was handed. That lets us assert three things: a matched
project makes the prompt ask for activity and the result parses it; a miss omits
the activity section; and an unparseable/partial response falls back to a no-op
decision instead of raising (never silently wrong).
"""

from types import SimpleNamespace

from app.schemas.decision import ContextDecision
from app.schemas.project_activity import ProjectActivity
from app.schemas.project_resolution import ProjectResolution
from app.schemas.understanding import UnderstandingResult
from app.services.context_extractor import ContextExtraction
from app.services.understanding_engine import UnderstandingEngine


class _FakeModels:
    """Stand-in for ``client.models``; records the call and returns canned text."""

    def __init__(self, response_text, recorder: dict) -> None:
        self._response_text = response_text
        self._recorder = recorder

    def generate_content(self, model, contents, config):
        self._recorder["model"] = model
        self._recorder["contents"] = contents
        self._recorder["config"] = config
        return SimpleNamespace(text=self._response_text)


def _engine_with_response(response_text):
    """Build an engine wired to a fake client, bypassing genai construction."""

    recorder: dict = {}
    engine = UnderstandingEngine.__new__(UnderstandingEngine)
    engine.client = SimpleNamespace(models=_FakeModels(response_text, recorder))
    return engine, recorder


def _extraction() -> ContextExtraction:
    return ContextExtraction(updates={}, confidence=1.0, reasoning="")


def test_matched_project_requests_and_parses_activity() -> None:
    payload = UnderstandingResult(
        decision=ContextDecision(action="none", reason="noted"),
        activity=ProjectActivity(
            current_focus="chapter 4",
            latest_activity="wrote three chapters",
            confidence=0.9,
        ),
    ).model_dump_json()
    engine, recorder = _engine_with_response(payload)

    project = {"id": "proj-novel", "name": "Fantasy Novel"}
    result = engine.decide(
        user_input="wrote three chapters of my novel today",
        current_context={"goals": []},
        extraction=_extraction(),
        project_resolution=ProjectResolution(
            matched=True,
            project_id="proj-novel",
            confidence=0.9,
            reason="local match",
        ),
        project=project,
    )

    # The activity sub-object round-trips out of the merged response.
    assert result.activity is not None
    assert result.activity.latest_activity == "wrote three chapters"
    assert result.activity.current_focus == "chapter 4"

    # The prompt actually asked for activity and named the resolved project,
    # and the structured-output schema was the merged one.
    assert "PROJECT ACTIVITY EXTRACTION" in recorder["contents"]
    assert "proj-novel" in recorder["contents"]
    assert (
        recorder["config"]["response_json_schema"]
        == UnderstandingResult.model_json_schema()
    )


def test_miss_omits_activity_section() -> None:
    payload = UnderstandingResult(
        decision=ContextDecision(action="none", reason="noted"),
        activity=None,
    ).model_dump_json()
    engine, recorder = _engine_with_response(payload)

    result = engine.decide(
        user_input="I got promoted at work today",
        current_context={"goals": []},
        extraction=_extraction(),
        project_resolution=ProjectResolution(
            matched=False,
            confidence=0.9,
            reason="no match",
        ),
        project=None,
    )

    assert result.activity is None
    # With no resolved project the prompt must not ask for project activity.
    assert "PROJECT ACTIVITY EXTRACTION" not in recorder["contents"]
    assert "No existing project was resolved" in recorder["contents"]


def test_unparseable_response_falls_back_safely() -> None:
    engine, _ = _engine_with_response("this is not json")

    result = engine.decide(
        user_input="hello there",
        current_context={},
        extraction=_extraction(),
        project_resolution=None,
        project=None,
    )

    # Never silently wrong: a garbage response degrades to a no-op decision.
    assert result.decision.action == "none"
    assert result.activity is None


def test_missing_decision_falls_back_safely() -> None:
    # Valid JSON but missing the required ``decision`` sub-object.
    engine, _ = _engine_with_response('{"activity": null}')

    result = engine.decide(
        user_input="hello there",
        current_context={},
        extraction=_extraction(),
        project_resolution=None,
        project=None,
    )

    assert result.decision.action == "none"
    assert result.activity is None


def test_empty_response_text_falls_back_safely() -> None:
    # ``response.text`` can be None; the engine must not crash on it.
    engine, _ = _engine_with_response(None)

    result = engine.decide(
        user_input="hello there",
        current_context={},
        extraction=_extraction(),
        project_resolution=None,
        project=None,
    )

    assert result.decision.action == "none"
    assert result.activity is None
