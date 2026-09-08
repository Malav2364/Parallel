"""SemanticProjectResolver: matching plus graceful degradation on a DB failure.

The resolver shares the request's DB session, so a failed cache query must not
poison it. On any embedding/cache error the resolver rolls the session back and
returns ``matched=False`` so the cascade falls through to the Gemini resolver
instead of 500ing the whole /process request (Tier-2 is an optimisation, not a
dependency).
"""

import asyncio

from app.services.semantic_project_resolver import SemanticProjectResolver


class FakeEmbeddings:
    """Maps text to a basis vector by the first keyword it contains."""

    def __init__(self, mapping: dict[str, list[float]], default: list[float]) -> None:
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


class InMemoryRepo:
    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, list[float]]] = {}
        self.rolled_back = False

    def get_many(self, user_id):
        return dict(self.rows)

    def upsert(self, user_id, project_id, text_hash, embedding):
        self.rows[project_id] = (text_hash, embedding)

    def commit(self):
        pass

    def rollback(self):
        self.rolled_back = True


class FailingRepo(InMemoryRepo):
    """Reproduces the missing-table / poisoned-session failure at the cache read."""

    def get_many(self, user_id):
        raise RuntimeError('relation "project_embeddings" does not exist')


PROJECTS = [
    {
        "id": "p-novel",
        "name": "Fantasy Novel",
        "description": "drafting my fantasy novel",
        "current_focus": None,
    },
    {
        "id": "p-tax",
        "name": "Quarterly Taxes",
        "description": "file the quarterly taxes",
        "current_focus": None,
    },
]


def _resolver(repo) -> SemanticProjectResolver:
    embeddings = FakeEmbeddings(
        mapping={"novel": [1.0, 0.0, 0.0], "tax": [0.0, 1.0, 0.0]},
        default=[0.0, 0.0, 1.0],
    )
    return SemanticProjectResolver(
        embeddings=embeddings,
        repo=repo,
        threshold=0.78,
        margin=0.06,
    )


def test_clear_winner_matches() -> None:
    resolver = _resolver(InMemoryRepo())
    result = asyncio.run(
        resolver.resolve(
            user_id="u1",
            user_input="wrote a chapter of my novel today",
            projects=PROJECTS,
        )
    )
    assert result.matched is True
    assert result.project_id == "p-novel"


def test_no_projects_returns_unmatched() -> None:
    resolver = _resolver(InMemoryRepo())
    result = asyncio.run(
        resolver.resolve(user_id="u1", user_input="anything", projects=[]),
    )
    assert result.matched is False


def test_db_failure_rolls_back_and_defers() -> None:
    repo = FailingRepo()
    resolver = _resolver(repo)
    result = asyncio.run(
        resolver.resolve(
            user_id="u1",
            user_input="wrote a chapter of my novel today",
            projects=PROJECTS,
        )
    )
    # Degrades to a miss (the cascade will fall through to Gemini)...
    assert result.matched is False
    # ...and crucially rolls back the shared session it just poisoned.
    assert repo.rolled_back is True
