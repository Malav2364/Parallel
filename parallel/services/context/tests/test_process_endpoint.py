"""/process fast-path wiring: a HIGH Tier-1 reminder skips the LLM stages.

These drive the real cascade (propose + mapping + the endpoint branch) through
FastAPI, faking only the I/O services. The project resolver, decision engine,
and activity extractor are replaced with stand-ins that raise if called, so a
green fast-path test proves those three Gemini stages were skipped. A
non-reminder message falls through and the decision engine does run.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_action_executor,
    get_context_decision_engine,
    get_context_extractor,
    get_context_service,
    get_project_activity_extractor,
    get_project_resolver,
    get_projects_client,
)
from app.main import app
from app.schemas.decision import ContextDecision
from app.schemas.project_resolution import ProjectResolution
from app.services.context_extractor import ContextExtraction

PROCESS_URL = "/api/v1/context/process"
HEADERS = {"X-User-Id": "user-1"}


class _FakeContext:
    def __init__(self, data: dict) -> None:
        self.context = data


class FakeContextService:
    def get_context(self, user_id):
        return _FakeContext({"goals": []})

    def apply_updates(self, user_id, updates):
        return _FakeContext({"goals": []})


class FakeExtractor:
    def __init__(self) -> None:
        self.calls = 0

    def extract(self, user_input, current_context):
        self.calls += 1
        return ContextExtraction(updates={}, confidence=1.0, reasoning="")


class RecordingExecutor:
    def __init__(self) -> None:
        self.decisions: list[ContextDecision] = []

    async def execute(self, user_id, decision):
        self.decisions.append(decision)
        return {"executed": True, "action": decision.action}


class RecordingDecisionEngine:
    def __init__(self) -> None:
        self.called = False

    def evaluate(self, **kwargs):
        self.called = True
        return ContextDecision(action="none", reason="fallback")


class NoMatchResolver:
    async def resolve(self, user_id, user_input):
        return ProjectResolution(
            matched=False,
            confidence=1.0,
            reason="no projects",
        )


class RaiseIfCalled:
    """Stand-in whose every attribute access yields a raising callable."""

    def __getattr__(self, name):
        def _boom(*args, **kwargs):
            raise AssertionError(f"{name} must not run on the fast path")

        return _boom


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_high_reminder_takes_fast_path_and_skips_llm_stages() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # The three LLM stages the fast path must skip: raise if touched.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "remind me to call mom tomorrow at 9am"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "rules"
    assert body["resolution"] is None

    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "create_reminder"
    assert decision.reminder_scheduled_for is not None


def test_high_habit_takes_fast_path_and_skips_llm_stages() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # The three LLM stages the fast path must skip: raise if touched.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "start a habit of meditating every day"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "rules"
    assert body["resolution"] is None

    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "create_habit"
    assert decision.habit_schedule == "daily"
    assert decision.reminder_scheduled_for is None


def test_high_goal_takes_fast_path_and_skips_llm_stages() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # The three LLM stages the fast path must skip: raise if touched.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "my goal is to lose weight"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "rules"
    assert body["resolution"] is None

    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "create_goal"
    assert decision.goal_name == "lose weight"
    assert decision.reminder_scheduled_for is None


def test_medium_reminder_requests_confirmation() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # A MEDIUM proposal must skip both execution and every LLM stage.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "remind me to submit report"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "needs_confirmation"
    assert body["tier"] == "rules"

    pending = body["pending_action"]
    assert pending["action"] == "create_reminder"
    assert pending["slots"]["title"] == "submit report"
    assert "when" in body["prompt"].lower()

    # Nothing was executed -- we asked first.
    assert executor.decisions == []


def test_ambiguous_recurring_requests_clarification() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # A LOW proposal must skip both execution and every LLM stage.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "i want to meditate every day"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "needs_clarification"
    assert body["tier"] == "rules"

    pending = body["pending_action"]
    assert pending["action"] == "none"
    assert pending["slots"]["activity"] == "meditate"
    assert pending["slots"]["schedule"] == "daily"
    assert "habit" in body["prompt"].lower()
    assert "reminder" in body["prompt"].lower()

    # Nothing was executed -- we asked which category first.
    assert executor.decisions == []


def test_non_reminder_falls_through_to_decision_engine() -> None:
    executor = RecordingExecutor()
    engine = RecordingDecisionEngine()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_project_resolver] = lambda: NoMatchResolver()
    app.dependency_overrides[get_context_decision_engine] = lambda: engine
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "I got promoted to senior engineer"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "llm"
    assert engine.called is True


def test_confirmation_answer_executes_deterministically() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    # The answer turn is model-free: the context service, extractor, and every
    # LLM stage must be untouched. RaiseIfCalled raises on any attribute access.
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={
                "message": "tomorrow at 5pm",
                "pending_action": {
                    "action": "create_reminder",
                    "source": "rules",
                    "confidence": 0.5,
                    "slots": {"title": "submit report"},
                },
            },
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "rules"
    assert body["type"] == "new_intent"

    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "create_reminder"
    assert decision.reminder_title == "submit report"
    assert decision.reminder_scheduled_for is not None


def test_ambiguous_confirmation_answer_re_confirms() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={
                "message": "at 8",  # no am/pm -> still unresolved
                "pending_action": {
                    "action": "create_reminder",
                    "source": "rules",
                    "confidence": 0.5,
                    "slots": {"title": "stretch"},
                },
            },
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "needs_confirmation"
    assert body["pending_action"]["slots"]["title"] == "stretch"
    assert executor.decisions == []


_CLARIFY_PENDING = {
    "action": "none",
    "source": "rules",
    "confidence": 0.3,
    "slots": {
        "activity": "meditate",
        "schedule": "daily",
        "candidates": ["create_habit", "create_reminder"],
    },
}


def test_clarification_answer_habit_executes_deterministically() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    # Model-free: the context service, extractor, and every LLM stage untouched.
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "make it a habit", "pending_action": _CLARIFY_PENDING},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "rules"
    assert body["type"] == "new_intent"

    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "create_habit"
    assert decision.habit_name == "meditate"
    assert decision.habit_schedule == "daily"


def test_clarification_answer_reminder_chains_to_confirmation() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_decision_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_activity_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "a reminder please", "pending_action": _CLARIFY_PENDING},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    # Picking "reminder" still needs a time -> hand off to the confirm loop.
    assert body["type"] == "needs_confirmation"
    assert body["tier"] == "rules"

    pending = body["pending_action"]
    assert pending["action"] == "create_reminder"
    assert pending["slots"]["title"] == "meditate"
    assert pending["slots"]["recurrence"] == "daily"
    assert "when" in body["prompt"].lower()

    assert executor.decisions == []
