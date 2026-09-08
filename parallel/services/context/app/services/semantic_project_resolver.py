"""Tier-2 semantic project resolver: in-process cosine over cached embeddings.

Sits between the deterministic Tier-1 rules and the Gemini ``ProjectResolver``.
When a message reaches the fallback branch, this resolves *which* existing
project it is about by embedding the projects and the message and cosine-ranking
them locally. It returns the same :class:`ProjectResolution` the Gemini resolver
does, so the downstream endpoint is unchanged. A match is emitted only for a
confident, unambiguous winner; otherwise it returns ``matched=False`` so the
cascade defers to the LLM rather than guessing -- never silently wrong.
"""

import hashlib
import logging

from app.clients.embeddings_client import EmbeddingsClient
from app.nlu.similarity import decide, rank
from app.repositories import ProjectEmbeddingRepository
from app.schemas.project_resolution import ProjectResolution

logger = logging.getLogger(__name__)


def _project_text(project: dict) -> str:
    """Descriptive text for a project, from the fields the projects service
    returns (name/description/current_focus -- there is no status)."""

    parts = [
        project.get("name"),
        project.get("description"),
        project.get("current_focus"),
    ]
    return "\n".join(part for part in parts if part)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticProjectResolver:
    """Resolve a project by semantic similarity, with a per-user embedding cache."""

    def __init__(
        self,
        embeddings: EmbeddingsClient,
        repo: ProjectEmbeddingRepository,
        threshold: float,
        margin: float,
    ) -> None:
        self.embeddings = embeddings
        self.repo = repo
        self.threshold = threshold
        self.margin = margin

    async def resolve(
        self,
        user_id: str,
        user_input: str,
        projects: list[dict],
    ) -> ProjectResolution:
        if not projects:
            return ProjectResolution(
                matched=False,
                confidence=1.0,
                reason="The user has no existing projects.",
            )

        try:
            candidates = self._project_vectors(user_id, projects)
            query_vector = self.embeddings.embed(user_input)
        except Exception:
            # Any embedding/cache failure defers to the LLM resolver rather than
            # surfacing an error or guessing -- Tier-2 is an optimisation, not a
            # dependency. A failed DB statement leaves the shared request session
            # in an aborted transaction, so roll it back before returning;
            # otherwise every later query on that same session (the downstream
            # context reload, the decision engine) fails with
            # InFailedSqlTransaction and 500s the whole request. The context
            # updates applied earlier were already committed, so the rollback
            # discards nothing.
            logger.exception("Tier-2 embedding failed; deferring to LLM resolver")
            try:
                self.repo.rollback()
            except Exception:
                logger.exception("Tier-2 session rollback failed")
            return ProjectResolution(
                matched=False,
                confidence=0.0,
                reason="Semantic resolver unavailable.",
            )

        ranked = rank(query_vector, candidates)
        project_id, score = decide(
            ranked,
            threshold=self.threshold,
            margin=self.margin,
        )

        if project_id is None:
            return ProjectResolution(
                matched=False,
                confidence=score,
                reason="No project cleared the semantic match threshold.",
            )

        return ProjectResolution(
            matched=True,
            project_id=project_id,
            confidence=score,
            reason="Matched by semantic similarity (Tier-2).",
        )

    def _project_vectors(
        self,
        user_id: str,
        projects: list[dict],
    ) -> list[tuple[str, list[float]]]:
        """Return ``(project_id, embedding)`` for each project with usable text,
        (re)embedding only those whose text changed since it was last cached."""

        cached = self.repo.get_many(user_id)

        eligible: list[tuple[str, str]] = []  # (project_id, text_hash)
        to_embed_texts: list[str] = []
        to_embed_ids: list[str] = []
        to_embed_hashes: list[str] = []

        for project in projects:
            project_id = project["id"]
            text = _project_text(project)
            if not text:
                # Nothing to embed -- an empty project can't be matched.
                continue

            text_hash = _hash(text)
            eligible.append((project_id, text_hash))

            entry = cached.get(project_id)
            if entry is None or entry[0] != text_hash:
                to_embed_texts.append(text)
                to_embed_ids.append(project_id)
                to_embed_hashes.append(text_hash)

        if to_embed_texts:
            fresh = self.embeddings.embed_batch(to_embed_texts)
            for project_id, text_hash, vector in zip(
                to_embed_ids,
                to_embed_hashes,
                fresh,
                strict=True,
            ):
                self.repo.upsert(
                    user_id=user_id,
                    project_id=project_id,
                    text_hash=text_hash,
                    embedding=vector,
                )
                cached[project_id] = (text_hash, vector)
            self.repo.commit()

        return [(project_id, cached[project_id][1]) for project_id, _ in eligible]
