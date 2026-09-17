"""/process fast-path wiring: a HIGH Tier-1 reminder skips the LLM stages.

These drive the real cascade (propose + mapping + the endpoint branch) through
FastAPI, faking only the I/O services. The project resolver and the
understanding engine (the merged decide+activity Gemini call) are replaced with
stand-ins that raise if called, so a green fast-path test proves those Gemini
stages were skipped. A non-reminder message falls through and the engine runs.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_action_executor,
    get_context_extractor,
    get_context_service,
    get_github_client,
    get_project_resolver,
    get_projects_client,
    get_semantic_project_resolver,
    get_understanding_engine,
)
from app.main import app
from app.schemas.decision import ContextDecision
from app.schemas.project_resolution import ProjectResolution
from app.schemas.understanding import UnderstandingResult
from app.services.context_extractor import ContextExtraction
from app.services.semantic_project_resolver import SemanticProjectResolver

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


class RecordingUnderstandingEngine:
    """Merged extract+decide+activity engine stand-in.

    Records that it ran, the ``project`` it was handed (a resolved project dict
    on a Tier-2 hit, ``None`` on a miss/no-projects), and -- for the merged
    miss path -- the ``project_resolution`` and candidate ``projects`` it
    received, so a test can prove the endpoint fed the right thing into the
    single Gemini call. On the self-resolve path (``project_resolution`` is None
    with candidate ``projects``) it stands in for the model's own resolution by
    returning ``self._resolution``, mirroring the real engine's guarantee that
    ``result.resolution`` is never null there; otherwise it leaves it null.
    Returns a benign "none" decision with an empty extraction and no activity;
    the engine's own parsing is covered by test_understanding_engine.
    """

    def __init__(self, resolution: ProjectResolution | None = None) -> None:
        self.called = False
        self.projects: list[dict | None] = []
        self.project_lists: list[list[dict] | None] = []
        self.project_resolutions: list[ProjectResolution | None] = []
        self.contexts: list[dict] = []
        self._resolution = resolution or ProjectResolution(
            matched=False,
            confidence=0.9,
            reason="engine self-resolve: no match",
        )

    def decide(
        self,
        user_input,
        current_context,
        project_resolution=None,
        project=None,
        projects=None,
        **kwargs,
    ) -> UnderstandingResult:
        self.called = True
        self.projects.append(project)
        self.project_lists.append(projects)
        self.project_resolutions.append(project_resolution)
        self.contexts.append(current_context)
        self_resolve = project_resolution is None and projects is not None
        return UnderstandingResult(
            decision=ContextDecision(action="none", reason="fallback"),
            activity=None,
            extraction=ContextExtraction(updates={}, confidence=1.0, reasoning=""),
            resolution=self._resolution if self_resolve else None,
        )


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


class FakeProjectsClient:
    """In-memory projects client for the Tier-2 semantic branch."""

    def __init__(self, projects: list[dict]) -> None:
        self._projects = projects
        self.activity_updates: list[dict] = []

    async def list_projects(self, user_id):
        return self._projects

    async def update_activity(self, project_id, current_focus, latest_activity):
        self.activity_updates.append(
            {
                "project_id": project_id,
                "current_focus": current_focus,
                "latest_activity": latest_activity,
            }
        )
        return {"id": project_id}


class KeywordEmbeddings:
    """Deterministic stand-in for the Gemini embeddings client.

    Maps text to a basis vector by the first keyword it contains, so a test can
    make one project the unambiguous cosine winner (or make everything
    dissimilar) without any real embedding round-trip.
    """

    def __init__(
        self,
        mapping: dict[str, list[float]],
        default: list[float],
    ) -> None:
        self._mapping = mapping
        self._default = default

    def _vector(self, text: str) -> list[float]:
        lowered = text.lower()
        for keyword, vector in self._mapping.items():
            if keyword in lowered:
                return list(vector)
        return list(self._default)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed(self, text: str) -> list[float]:
        return self._vector(text)


class InMemoryEmbeddingRepo:
    """Cache repo backed by a dict; mirrors ProjectEmbeddingRepository's surface."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, list[float]]] = {}

    def get_many(self, user_id):
        return dict(self.rows)

    def upsert(self, user_id, project_id, text_hash, embedding):
        self.rows[project_id] = (text_hash, embedding)

    def commit(self):
        pass


def _semantic_projects() -> list[dict]:
    return [
        {
            "id": "proj-novel",
            "name": "Fantasy Novel",
            "description": "drafting my fantasy novel",
            "current_focus": None,
        },
        {
            "id": "proj-taxes",
            "name": "Quarterly Taxes",
            "description": "file the quarterly taxes",
            "current_focus": None,
        },
    ]


def _keyword_semantic_resolver() -> SemanticProjectResolver:
    embeddings = KeywordEmbeddings(
        mapping={"novel": [1.0, 0.0, 0.0], "tax": [0.0, 1.0, 0.0]},
        default=[0.0, 0.0, 1.0],
    )
    return SemanticProjectResolver(
        embeddings=embeddings,
        repo=InMemoryEmbeddingRepo(),
        threshold=0.78,
        margin=0.06,
    )


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
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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

    message = body["message"]
    assert isinstance(message, str) and message
    assert "remind" in message.lower()
    assert "call mom" in message.lower()


def test_high_habit_takes_fast_path_and_skips_llm_stages() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # The three LLM stages the fast path must skip: raise if touched.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    # A slot-fill confirmation ("when?") is free-text, not yes/no -- no chips.
    assert "candidates" not in pending["slots"]
    assert "when" in body["prompt"].lower()
    # The composed reply is the same question we asked.
    assert body["message"] == body["prompt"]

    # Nothing was executed -- we asked first.
    assert executor.decisions == []


def test_ambiguous_recurring_requests_clarification() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    # A LOW proposal must skip both execution and every LLM stage.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    # The clarification renders two tap chips -- the display words the choice
    # parser reads, not the internal create_habit/create_reminder action names.
    assert pending["slots"]["candidates"] == ["Habit", "Reminder"]
    assert "habit" in body["prompt"].lower()
    assert "reminder" in body["prompt"].lower()
    # The composed reply is the same question we asked.
    assert body["message"] == body["prompt"]

    # Nothing was executed -- we asked which category first.
    assert executor.decisions == []


def test_non_reminder_falls_through_to_understanding_engine() -> None:
    executor = RecordingExecutor()
    understanding = RecordingUnderstandingEngine()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_understanding_engine] = lambda: understanding
    # No existing projects: the fallback branch short-circuits before either
    # resolver, so both stay untouched while the understanding engine still runs.
    app.dependency_overrides[get_projects_client] = lambda: FakeProjectsClient([])
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_semantic_project_resolver] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "I got promoted to senior engineer"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "llm"
    assert body["resolution_source"] == "nlu"
    assert understanding.called is True
    # No projects -> a miss -> the engine is handed no project to report on.
    assert understanding.projects[-1] is None


def test_semantic_match_resolves_project_without_gemini() -> None:
    executor = RecordingExecutor()
    understanding = RecordingUnderstandingEngine()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_understanding_engine] = lambda: understanding
    app.dependency_overrides[get_projects_client] = lambda: FakeProjectsClient(
        _semantic_projects(),
    )
    app.dependency_overrides[get_semantic_project_resolver] = _keyword_semantic_resolver
    # Tier-2 resolves the project locally; the Gemini resolver must NOT run.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "wrote three chapters of my novel today"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resolution_source"] == "nlu"
    assert body["resolution"]["matched"] is True
    assert body["resolution"]["project_id"] == "proj-novel"
    assert body["tier"] == "llm"
    assert understanding.called is True
    # A local match hands the resolved project dict to the single Gemini call.
    assert understanding.projects[-1] is not None
    assert understanding.projects[-1]["id"] == "proj-novel"


def test_semantic_miss_merges_resolution_into_understanding_call() -> None:
    """A Tier-2 miss no longer fires a separate Tier-3 Gemini resolve.

    Instead the one understanding call self-resolves: the endpoint feeds it the
    candidate ``projects`` with ``project_resolution=None`` and reads the
    ``resolution`` back off the merged result -- one model round trip, not two.
    """

    executor = RecordingExecutor()
    understanding = RecordingUnderstandingEngine()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_understanding_engine] = lambda: understanding
    app.dependency_overrides[get_projects_client] = lambda: FakeProjectsClient(
        _semantic_projects(),
    )
    app.dependency_overrides[get_semantic_project_resolver] = _keyword_semantic_resolver
    # The Tier-3 Gemini resolver is gone from /process; if it were still wired
    # in, this override would blow up the moment it ran.
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "I got promoted at work today"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resolution_source"] == "llm"
    # The resolution rode back on the single merged understanding call.
    assert body["resolution"]["matched"] is False
    assert body["tier"] == "llm"
    assert understanding.called is True
    # The miss self-resolves: no concrete resolution in, candidate projects in.
    assert understanding.project_resolutions[-1] is None
    assert understanding.project_lists[-1] == _semantic_projects()
    # No project handed in pre-call, and the miss resolves to none.
    assert understanding.projects[-1] is None


class FakeGithubClient:
    """Records whether /status was consulted; mirrors the briefing test fake."""

    def __init__(self, signals=None, status=None, raise_error=False) -> None:
        self._signals = signals or []
        self._status = status or {}
        self._raise = raise_error
        self.status_calls = 0

    async def list_signals(self, user_id, unread=False):
        if self._raise:
            raise httpx.HTTPError("connector down")
        return self._signals

    async def get_status(self, user_id):
        self.status_calls += 1
        return self._status


def _all_stages_raise() -> None:
    """A GitHub query answers from signals alone -- no cascade, no LLM."""

    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_action_executor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_semantic_project_resolver] = lambda: RaiseIfCalled()


def test_github_query_answers_from_signals_without_cascade() -> None:
    fake = FakeGithubClient(
        signals=[
            {
                "kind": "review_request",
                "payload": {"repo": "me/api", "number": 12, "title": "Fix auth"},
            },
        ],
    )
    _all_stages_raise()
    app.dependency_overrides[get_github_client] = lambda: fake

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "what's waiting on my review?"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "github_query"
    assert body["tier"] == "rules"
    assert body["decision"] is None
    assert body["execution"] is None
    assert "me/api #12 — Fix auth" in body["message"]
    # A read-only lookup never writes durable context.
    assert body["context_update"] is None


def test_github_query_degrades_when_connector_down_never_500() -> None:
    fake = FakeGithubClient(raise_error=True)
    _all_stages_raise()
    app.dependency_overrides[get_github_client] = lambda: fake

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "any PRs waiting on my review?"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "github_query"
    assert "isn't connected" in body["message"]


def test_github_query_caught_up_when_connected_no_signals() -> None:
    fake = FakeGithubClient(signals=[], status={"connected": True})
    _all_stages_raise()
    app.dependency_overrides[get_github_client] = lambda: fake

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "any open pull requests?"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "github_query"
    assert "caught up" in body["message"]
    assert fake.status_calls == 1


def test_create_intent_naming_a_pr_is_not_hijacked_by_github_query() -> None:
    """A create phrasing that happens to contain a GitHub anchor ("remind me to
    open a pull request") must be claimed by the reminder proposer, not the
    read-only lookup. The recogniser alone can't split those (it fires on both);
    precedence lives here -- the endpoint only consults GitHub when propose()
    finds no create-intent. The GitHub client raises if touched to prove it.
    """

    executor = RecordingExecutor()

    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()
    # The GitHub client must NOT be consulted: a create-intent owns this turn.
    app.dependency_overrides[get_github_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={"message": "remind me to open a pull request"},
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] != "github_query"
    assert body["tier"] == "rules"
    # A subject-only reminder is MEDIUM: it asks for the time rather than
    # firing the GitHub lookup.
    assert body["pending_action"]["action"] == "create_reminder"


def test_confirmation_answer_executes_deterministically() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    # The answer turn is model-free: the context service, extractor, and every
    # LLM stage must be untouched. RaiseIfCalled raises on any attribute access.
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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

    assert "meditate" in body["message"]


def test_clarification_answer_reminder_chains_to_confirmation() -> None:
    executor = RecordingExecutor()

    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
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


# --------------------------------------------------------------------------
# GitHub merge -- the full firm-gate walk (fresh -> method -> firm -> execute)
# and a terminal decline, threading the real serialized pending_action across
# turns. This is the e2e the comment slice never had: a public write confirms
# on every turn and only the deliberate final reply lands code.
# --------------------------------------------------------------------------


def test_merge_walks_repo_then_method_then_firm_gate_then_executes() -> None:
    executor = RecordingExecutor()

    # Turn 1 is a fresh utterance, so the context service, extractor, and the
    # signals-based repo fill all run; every LLM stage must stay untouched on
    # all four turns (the answer turns 2-4 skip the fakes entirely).
    app.dependency_overrides[get_context_service] = lambda: FakeContextService()
    app.dependency_overrides[get_context_extractor] = lambda: FakeExtractor()
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_github_client] = lambda: FakeGithubClient(signals=[])
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_semantic_project_resolver] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        # Turn 1: bare "merge PR 42" names no repo (no signal matches) -> ask
        # which repo, still MEDIUM. Nothing fires.
        r1 = client.post(
            PROCESS_URL,
            json={"message": "merge PR 42"},
            headers=HEADERS,
        )
        assert r1.status_code == 200
        first = r1.json()
        assert first["type"] == "needs_confirmation"
        assert first["tier"] == "rules"
        assert first["pending_action"]["action"] == "merge_github_pr"
        assert first["pending_action"]["slots"]["number"] == 42
        # Repo still unknown -> Stage A needs a free-text repo, so no chips yet.
        assert "candidates" not in first["pending_action"]["slots"]
        assert "which repo is pr #42" in first["prompt"].lower()
        assert executor.decisions == []

        # Turn 2: name the repo -> the method question, still MEDIUM.
        r2 = client.post(
            PROCESS_URL,
            json={
                "message": "acme/app#42",
                "pending_action": first["pending_action"],
            },
            headers=HEADERS,
        )
        assert r2.status_code == 200
        second = r2.json()
        assert second["type"] == "needs_confirmation"
        assert second["pending_action"]["slots"]["repo"] == "acme/app"
        assert "method" not in second["pending_action"]["slots"]
        # Repo known, method open -> the three merge methods as tap chips.
        assert second["pending_action"]["slots"]["candidates"] == [
            "merge",
            "squash",
            "rebase",
        ]
        assert "how should i merge acme/app #42" in second["prompt"].lower()
        assert executor.decisions == []

        # Turn 3: pick squash -> the firm gate names the op and asks for the
        # number. A bare "yes" here would not pass (covered in test_merge).
        r3 = client.post(
            PROCESS_URL,
            json={
                "message": "squash",
                "pending_action": second["pending_action"],
            },
            headers=HEADERS,
        )
        assert r3.status_code == 200
        third = r3.json()
        assert third["type"] == "needs_confirmation"
        assert third["pending_action"]["slots"]["method"] == "squash"
        # Firm gate -> tap the PR number to confirm (or Cancel).
        assert third["pending_action"]["slots"]["candidates"] == ["42", "Cancel"]
        assert "Squash-merge acme/app #42?" in third["prompt"]
        assert "reply with the PR number (42)" in third["prompt"]
        assert executor.decisions == []

        # Turn 4: type the number -> the firm gate passes and the merge fires.
        r4 = client.post(
            PROCESS_URL,
            json={
                "message": "42",
                "pending_action": third["pending_action"],
            },
            headers=HEADERS,
        )
        assert r4.status_code == 200
        fourth = r4.json()

    assert fourth["type"] == "new_intent"
    assert fourth["tier"] == "rules"
    assert len(executor.decisions) == 1
    decision = executor.decisions[0]
    assert decision.action == "merge_github_pr"
    assert decision.github_repo == "acme/app"
    assert decision.github_number == 42
    assert decision.github_merge_method == "squash"


def test_merge_decline_is_terminal_and_writes_nothing() -> None:
    executor = RecordingExecutor()

    # A "no" to a public write is model-free AND connector-free: only the
    # executor is a real fake (to prove it never fires); everything else,
    # including the GitHub client, must be untouched.
    app.dependency_overrides[get_action_executor] = lambda: executor
    app.dependency_overrides[get_context_service] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_context_extractor] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_github_client] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_project_resolver] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_understanding_engine] = lambda: RaiseIfCalled()
    app.dependency_overrides[get_projects_client] = lambda: RaiseIfCalled()

    with TestClient(app) as client:
        response = client.post(
            PROCESS_URL,
            json={
                "message": "no",
                "pending_action": {
                    "action": "merge_github_pr",
                    "source": "rules",
                    "confidence": 0.5,
                    "slots": {"repo": "acme/app", "number": 42, "method": "squash"},
                    "reason": "rule:github_merge",
                },
            },
            headers=HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "context_only"
    assert body["tier"] == "rules"
    assert body["pending_action"] is None
    assert body["message"] == "No problem — I won't merge that PR."
    assert executor.decisions == []
